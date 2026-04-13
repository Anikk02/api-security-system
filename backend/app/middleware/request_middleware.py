import time
import logging
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

from app.features.feature_builder import FeatureBuilder
from app.state.state_manager import StateManager

logger = logging.getLogger(__name__)

state_manager = StateManager()
feature_builder = FeatureBuilder(state_manager)


class RequestMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(f"{request.method} {request.url.path}")

        async with AsyncSessionLocal() as db:
            try:
                #  Identity
                identity = await resolve_identity(request, db)

                #  Signals
                signals = await extract_signals(request)

                #  Features (safe)
                try:
                    features = await feature_builder.build(identity, signals)
                except Exception as e:
                    logger.error(f"Feature builder failed: {e}")
                    features = {}

                #  Decision (safe)
                try:
                    action, reason, risk_score, ml_data = await evaluate_request(
                        identity, signals, features
                    )
                except Exception as e:
                    logger.error(f"Decision engine failed: {e}")
                    action, reason, risk_score, ml_data = "allow", "fallback", 0.0, None

                #  BLOCK FLOW
                if action == "block":
                    await self._log_all(
                        db, identity, signals, features,
                        action, reason, risk_score, ml_data,
                        status_code=429
                    )
                    return JSONResponse(
                        status_code=429,
                        content={"detail": reason}
                    )

                # ALLOW / THROTTLE FLOW
                response = await call_next(request)

                process_time = time.time() - start_time

                #  Log everything
                await self._log_all(
                    db,
                    identity,
                    signals,
                    features,
                    action,
                    reason,
                    risk_score,
                    ml_data,
                    status_code=response.status_code
                )

                logger.info(
                    f"user={identity.user_id} | action={action} | status={response.status_code} | time={process_time:.4f}s"
                )

                return response

            except Exception as e:
                logger.error(f"Middleware error: {str(e)}")

                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal middleware error"}
                )

    #  CENTRALIZED LOGGING
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
        status_code=200
    ):
        try:
            # Request log
            db.add(RequestLog(
                user_id=identity.user_id,
                endpoint=signals.endpoint,
                ip_address=signals.ip_address,
                user_agent=signals.user_agent,
                status_code=status_code
            ))

            # Decision log
            db.add(DecisionLog(
                user_id=identity.user_id,
                action=action,
                reason=reason,
                risk_score=risk_score
            ))

            # Feature log
            db.add(FeatureLog(
                user_id=identity.user_id,
                features=features
            ))

            # ML prediction log
            if ml_data:
                db.add(MLPrediction(
                    user_id=identity.user_id,
                    risk_score=risk_score,
                    risk_label=ml_data.get("label"),
                    explanation=ml_data.get("explanation"),
                    feature_contributions=ml_data.get("contributions")
                ))

            await db.commit()

        except Exception as e:
            logger.error(f"DB logging failed: {e}")
            await db.rollback()