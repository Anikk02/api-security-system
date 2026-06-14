import time
import logging
import uuid
import asyncio

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTasks

from app.identity.resolver import resolve_identity
from app.identity.signals import extract_signals
from app.state.state_manager import StateManager
from app.utils.rate_limiter import SlidingWindowRateLimiter

# Background pipeline (heavy work)
from app.background.analysis_pipeline import run_analysis_pipeline

logger = logging.getLogger(__name__)

SAFE_ENDPOINTS = ["/api/dashboard", "/health"]

#Initialize rate limiter
minute_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)
strict_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)


class RequestMiddleware(BaseHTTPMiddleware):
    """
    Fast path: resolve identity → check signals → decide → respond.

    Target latency: <15ms (2 Redis GETs + 1 pipeline write).

    All heavy work (feature building, risk scoring, DB logging, reputation
    updates) runs in a background task AFTER the response is returned.
    The risk_score written by that background task feeds the NEXT request's
    fast-path lookup, so intelligence accumulates over time with zero
    added latency.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request.state.request_uuid = str(uuid.uuid4())

        logger.info(
            f"{request.method} {request.url.path} | "
            f"req_uuid={request.state.request_uuid}"
        )

        try:
            # SAFE ENDPOINT BYPASS (before identity - zero DB cost)
            if any(request.url.path.startswith(e) for e in SAFE_ENDPOINTS):
                response = await call_next(request)
                response.headers["X-Request-UUID"] = request.state.request_uuid
                return response
            
            # 1. IDENTITY + SIGNALS
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                identity = await resolve_identity(request, db)

            signals = await extract_signals(request)
            label = request.headers.get("X-Simulated-Label")

            # 3. FAST-PATH DECISION (1 Redis pipeline - 2 reads)
            #
            # Pass IP for IP block checking
            # checks BOTH user and IP blocks in a single pipeline
            #
            blocked, risk_score, throttled = await StateManager.get_decision_signals(
                identity.user_id, 
                identity.ip_address,  # Pass IP for block checking
                identity.behavioral_fingerprint
            )

            # Determine action based on fast-path signals
            action, reason = await _fast_decision(blocked, throttled, risk_score)

            # 4. TRACK THIS REQUEST (fire-and-forget pipeline)
            # One pipelined ZADD+SADD. Does NOT block the response.
            asyncio.ensure_future(
                StateManager.track_request_async(
                    user_id=identity.user_id,
                    endpoint=signals.endpoint,
                    ip=signals.ip_address,
                    status_code=None,   # unknown yet; updated in background
                )
            )

            # 5. BLOCK FAST PATH
            if action == "block":
                # Kick off background to still log + update reputation
                asyncio.ensure_future(
                    run_analysis_pipeline(
                        user_id=identity.user_id,
                        identity=identity,
                        signals=signals,
                        status_code=429,
                        request_uuid=request.state.request_uuid,
                        label=label,
                        fast_risk_score=risk_score,
                    )
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": reason,
                        "request_uuid": request.state.request_uuid,
                    },
                    headers={
                        "X-RateLimit-Reset": "blocked",
                        "Retry-After": "3600",
                    }
                )

            # 6. RATE LIMITING CHECK (Sliding Window)
            limiter = strict_limiter if risk_score > 0.6 else minute_limiter
            allowed, count, retry_after = await limiter.check_and_allow(
                f"user:{identity.user_id}"
            )

            # 7. RATE LIMITED PATH (429)
            if not allowed:
                # Still run background analysis
                asyncio.ensure_future(
                    run_analysis_pipeline(
                        user_id=identity.user_id,
                        identity=identity,
                        signals=signals,
                        status_code=429,
                        request_uuid=request.state.request_uuid,
                        label=label,
                        fast_risk_score=risk_score,
                    )
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail":f"Rated limit exceeded. {count}/{limiter.max_requests} requests per minute.",
                        "retry_after": retry_after,
                        "remaining": 0,
                        "reset": int(time.time() + retry_after),
                        "request_uuid": request.state.request_uuid
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limiter.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                        "Cache-Control": "no-cache, no-store, must-revalidate"
                    }
                )
            
            # Users flagged with throttled flag from penalty_manager
            if throttled:
                # The flag means they're already being rate-limited elsewhere
                # Just process the request normally
    
                response = await call_next(request)
                process_time = time.time() - start_time
    
                # Add throttle headers to inform them
                response.headers["X-RateLimit-Limit"] = "100"
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = "60"
                response.headers["X-Request-UUID"] = request.state.request_uuid
                response.headers["X-Process-Time"] = f"{process_time:.4f}"
                response.headers["X-Throttled"] = "true"
    
                logger.info(
                     f"user={identity.user_id} | action=throttle (flag active) | "
                     f"status={response.status_code} | time={process_time:.4f}s | "
                     f"req_uuid={request.state.request_uuid}"
                )
    
                # Background analysis
                asyncio.ensure_future(
                    run_analysis_pipeline(
                        user_id=identity.user_id,
                        identity=identity,
                        signals=signals,
                        status_code=response.status_code,
                        request_uuid=request.state.request_uuid,
                        label=label,
                        fast_risk_score=risk_score,
                    )
                )
                
                return response

            # 7. NORMAL FLOW
            response = await call_next(request)
            process_time = time.time() - start_time

            logger.info(
                f"user={identity.user_id} | action={action} | "
                f"status={response.status_code} | time={process_time:.4f}s | "
                f"req_uuid={request.state.request_uuid}"
            )

            response.headers["X-Request-UUID"] = request.state.request_uuid
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            # 8. BACKGROUND ANALYSIS
            # Runs AFTER response is sent. Updates risk_score, reputation,
            # feature log, DB — all invisible to this request's latency.
            asyncio.ensure_future(
                run_analysis_pipeline(
                    user_id=identity.user_id,
                    identity=identity,
                    signals=signals,
                    status_code=response.status_code,
                    request_uuid=request.state.request_uuid,
                    label=label,
                    fast_risk_score=risk_score,
                )
            )

            return response

        except Exception as e:
            logger.exception(f"Middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal middleware error"},
            )


# FAST DECISION LOGIC
# This is the ONLY decision logic in the hot path.
# Reads pre-computed Redis signals.
async def _fast_decision(blocked: bool, throttled: bool, risk_score: float) -> tuple[str, str]:
    """
    Returns (action, reason) using only pre-computed Redis signals.
    """
    
    # Highest priority: Blocked users
    if blocked:
        return "block", "User or IP is temporarily blocked"
    
    # Throttled users
    if throttled:
        return "throttle", "Rate limit active"
    
    # Risk-based decisions (thresholds mirror penalty_manager)
    if risk_score > 0.70:
        return "block", "Severe risk score detected"
    
    if risk_score > 0.50:
        return "throttle", "High risk detected"
    
    if risk_score > 0.45:
        return "throttle", "Suspicious activity detected"
    
    return "allow", "Normal traffic"