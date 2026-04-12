import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.session import AsyncSessionLocal
from app.db.models.request_log import RequestLog
from app.db.models.decision_log import DecisionLog

from app.identity.resolver import resolve_identity
from app.identity.signals import extract_signals
from app.policy.decision_engine import evaluate_request

logger = logging.getLogger(__name__)


class RequestMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(f"{request.method} {request.url.path}")

        async with AsyncSessionLocal() as db:
            try:
                # Extract Identity
                identity = await resolve_identity(request, db)

                # Extract Signals
                signals = await extract_signals(request)

                # Decision
                action, reason, risk_score = await evaluate_request(identity, signals)

                # BLOCK
                if action == "block":
                    logger.warning(f"Blocked {identity.user_id}: {reason}")

                    decision_log = DecisionLog(
                        user_id=identity.user_id,
                        action=action,
                        reason=reason,
                        risk_score=risk_score
                    )
                    db.add(decision_log)
                    await db.commit()

                    return JSONResponse(
                        status_code=429,
                        content={"detail": reason}
                    )

                # Forward request
                response = await call_next(request)

                process_time = time.time() - start_time

                # Request log
                request_log = RequestLog(
                    user_id=identity.user_id,
                    endpoint=signals.endpoint,
                    ip_address=signals.ip_address,
                    user_agent=signals.user_agent,
                    status_code=response.status_code,
                )
                db.add(request_log)

                # Decision log
                decision_log = DecisionLog(
                    user_id=identity.user_id,
                    action=action,
                    reason=reason,
                    risk_score=risk_score
                )
                db.add(decision_log)

                await db.commit()

                logger.info(
                    f"user={identity.user_id} | status={response.status_code} | time={process_time:.4f}s"
                )

                return response

            except Exception as e:
                logger.error(f"Middleware error: {str(e)}")
                return await call_next(request)