import time
import logging
import uuid
import asyncio

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.session import AsyncSessionLocal
from app.db.models.request_log import RequestLog
from app.db.models.decision_log import DecisionLog
from app.db.models.feature_log import FeatureLog
from app.db.models.ml_prediction import MLPrediction

from app.identity.resolver import resolve_identity
from app.identity.signals import extract_signals
from app.policy.decision_engine import evaluate_request
from app.explainability.explainer import Explainer

from app.features.feature_builder import FeatureBuilder
from app.state.state_manager import StateManager

logger = logging.getLogger(__name__)

state_manager = StateManager()
feature_builder = FeatureBuilder(state_manager)


class RequestMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # ✅ Stable request UUID
        request.state.request_uuid = str(uuid.uuid4())

        logger.info(
            f"{request.method} {request.url.path} | req_uuid={request.state.request_uuid}"
        )

        async with AsyncSessionLocal() as db:
            try:
                # ---------------------------
                # Identity + Signals
                # ---------------------------
                identity = await resolve_identity(request, db)
                signals = await extract_signals(request)

                # ---------------------------
                # ✅ FEATURE TRACKING (ONLY HERE)
                # ---------------------------
                await state_manager.track_request(
                    identity.user_id,
                    request.url.path,
                    signals.ip_address
                )

                # ---------------------------
                # Features
                # ---------------------------
                try:
                    features = await feature_builder.build(identity, signals)
                except Exception as e:
                    logger.error(f"Feature builder failed: {e}")
                    features = {}

                # ---------------------------
                # Decision
                # ---------------------------
                try:
                    action, reason, risk_score, ml_data = await evaluate_request(
                        identity, signals, features
                    )
                except Exception as e:
                    logger.error(f"Decision engine failed: {e}")
                    action, reason, risk_score, ml_data = "allow", "fallback", 0.0, None

                # ---------------------------
                # Explanation
                # ---------------------------
                explanation = Explainer.generate(
                    action=action,
                    reason=reason,
                    risk_score=risk_score,
                    features=features,
                    ml_data=ml_data
                )

                # ---------------------------
                # 🚫 BLOCK FLOW
                # ---------------------------
                if action == "block":

                    # ✅ track error
                    await state_manager.increment_error(identity.user_id)

                    request_id = await self._log_all(
                        db, identity, signals, features,
                        action, reason, risk_score,
                        ml_data, explanation,
                        request.state.request_uuid,
                        status_code=429
                    )

                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": reason,
                            "request_id": request_id,
                            "request_uuid": request.state.request_uuid
                        }
                    )

                # ---------------------------
                # ⚠️ THROTTLE (progressive control)
                # ---------------------------
                if action == "throttle":
                    await asyncio.sleep(0.3)

                # ---------------------------
                # NORMAL FLOW
                # ---------------------------
                response = await call_next(request)

                # ✅ track error ONLY if needed
                if response.status_code >= 400:
                    await state_manager.increment_error(identity.user_id)

                process_time = time.time() - start_time

                request_id = await self._log_all(
                    db,
                    identity,
                    signals,
                    features,
                    action,
                    reason,
                    risk_score,
                    ml_data,
                    explanation,
                    request.state.request_uuid,
                    status_code=response.status_code
                )

                logger.info(
                    f"user={identity.user_id} | action={action} | "
                    f"status={response.status_code} | time={process_time:.4f}s | "
                    f"req_uuid={request.state.request_uuid}"
                )

                # ---------------------------
                # Headers
                # ---------------------------
                response.headers["X-Request-ID"] = str(request_id)
                response.headers["X-Request-UUID"] = request.state.request_uuid

                return response

            except Exception as e:
                logger.exception(f"Middleware error: {str(e)}")

                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal middleware error"}
                )

    # =========================
    # CENTRALIZED LOGGING
    # =========================
    async def _log_all(
        self,
        db,
        identity,
        signals,
        features,
        action,
        reason,
        risk_score,
        ml_data,
        explanation,
        request_uuid,
        status_code=200
    ):
        try:
            # REQUEST LOG
            request_log = RequestLog(
                user_id=identity.user_id,
                endpoint=signals.endpoint,
                ip_address=signals.ip_address,
                user_agent=signals.user_agent,
                status_code=status_code,
                request_uuid=request_uuid
            )

            db.add(request_log)
            await db.flush()

            request_id = request_log.id

            # DECISION LOG
            db.add(DecisionLog(
                user_id=identity.user_id,
                request_id=request_id,
                action=action,
                reason=reason,
                risk_score=risk_score,
                explanation=explanation.get("summary"),
                explanation_json=explanation
            ))

            # FEATURE LOG
            db.add(FeatureLog(
                user_id=identity.user_id,
                request_id=request_id,
                features=features,
                behavioral_features={
                    'req_per_min': features.get('req_per_min'),
                    'req_per_sec': features.get('req_per_sec'),
                    'burst_score': features.get('burst_score'),
                },
                pattern_features={
                    'endpoint_entropy': features.get('endpoint_entropy'),
                },
                identity_features={
                    'ip_changes': features.get('ip_changes'),
                    'is_bot': features.get('is_bot'),
                }
            ))

            # ML PREDICTION
            if ml_data:
                db.add(MLPrediction(
                    user_id=identity.user_id,
                    request_id=request_id,
                    risk_score=risk_score,
                    risk_label=ml_data.get("label"),
                    explanation=explanation.get("summary"),
                    feature_contributions=explanation.get("feature_contributions")
                ))

            await db.commit()

            return request_id

        except Exception as e:
            logger.error(f"DB logging failed: {e}")
            await db.rollback()
            return None