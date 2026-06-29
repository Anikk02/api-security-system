import time
import logging
import uuid
import asyncio

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.identity.resolver import resolve_identity, set_user_cookie_if_needed
from app.identity.signals import extract_signals
from app.state.state_manager import StateManager
from app.utils.rate_limiter import SlidingWindowRateLimiter

# Background pipeline (heavy work)
from app.background.analysis_pipeline import run_analysis_pipeline

logger = logging.getLogger(__name__)

CONTROL_PLANE_PREFIXES = [
    "/api/auth",
    "/api/client",
    "/api-keys",
    "/api/settings",
    "/api/activity",
    "/api/client/keys",
    "/api/usage"
]

# Initialize rate limiter
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
        
        # Detailed timing tracking
        timings = {}

        logger.info(
            f"{request.method} {request.url.path} | "
            f"req_uuid={request.state.request_uuid}"
        )

        try:
            # SAFE ENDPOINT BYPASS (before identity - zero DB cost)
            if any(request.url.path.startswith(p) for p in CONTROL_PLANE_PREFIXES):
                t0 = time.time()
                response = await call_next(request)
                timings['call_next'] = time.time() - t0
                timings['total'] = time.time() - start_time
                
                response.headers["X-Request-UUID"] = request.state.request_uuid
                response.headers["X-Process-Time"] = f"{timings['total']:.4f}"
                
                # Log bypass with timing
                logger.info(
                    f"BYPASS: {request.url.path} | "
                    f"total={timings['total']:.3f}s | "
                    f"call_next={timings['call_next']:.3f}s | "
                    f"req_uuid={request.state.request_uuid}"
                )
                return response
            
            # ── 1. IDENTITY + SIGNALS ─────────────────────────────────────────
            t0 = time.time()
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                identity = await resolve_identity(request, db)
            timings['identity_resolution'] = time.time() - t0

            t0 = time.time()
            signals = await extract_signals(request)
            timings['signals_extract'] = time.time() - t0
            
            label = request.headers.get("X-Simulated-Label")

            # ── 2. FAST-PATH DECISION ─────────────────────────────────────────
            t0 = time.time()
            blocked, risk_score, throttled = await StateManager.get_decision_signals(
                identity,
                identity.behavioral_fingerprint
            )
            timings['redis_decision'] = time.time() - t0

            # ── 3. TRACK REQUEST ──────────────────────────────────────────────
            t0 = time.time()
            asyncio.ensure_future(
                StateManager.track_request_async(
                    identity=identity,
                    endpoint=signals.endpoint,
                    status_code=None,
                )
            )
            timings['track_request'] = time.time() - t0

            # ── 4. DECISION ────────────────────────────────────────────────────
            t0 = time.time()
            action, reason = await _fast_decision(blocked, throttled, risk_score)
            timings['fast_decision'] = time.time() - t0

            # _fast_decision can recommend "throttle" purely from risk_score
            # even when the Redis-cached `throttled` flag isn't set yet (e.g.
            # the first request that crosses the threshold, before the
            # background pipeline has persisted it). Fold that into
            # `throttled` so step 8 below actually acts on it instead of
            # silently falling through to normal flow.
            if action == "throttle":
                throttled = True

            # ── 5. BLOCK FAST PATH ────────────────────────────────────────────
            if action == "block":
                asyncio.ensure_future(
                    run_analysis_pipeline(
                        identity=identity,
                        signals=signals,
                        status_code=429,
                        request_uuid=request.state.request_uuid,
                        label=label,
                        fast_risk_score=risk_score,
                    )
                )

                response = JSONResponse(
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
                
                set_user_cookie_if_needed(request, response)
                
                timings['total'] = time.time() - start_time
                response.headers["X-Process-Time"] = f"{timings['total']:.4f}"
                
                # Log block with detailed timings
                logger.info(
                    f"BLOCK: user={identity.identity_id} | "
                    f"total={timings['total']:.3f}s | "
                    f"identity={timings['identity_resolution']:.3f}s | "
                    f"redis={timings['redis_decision']:.3f}s | "
                    f"timings={timings} | "
                    f"req_uuid={request.state.request_uuid}"
                )
                
                return response

            # ── 6. RATE LIMITING CHECK ────────────────────────────────────────
            t0 = time.time()
            limiter = strict_limiter if risk_score > 0.6 else minute_limiter
            rate_key = f"client:{identity.client_id}:identity:{identity.identity_id}"
            allowed, count, retry_after = await limiter.check_and_allow(rate_key)
            timings['rate_limit'] = time.time() - t0

            # ── 7. RATE LIMITED PATH ──────────────────────────────────────────
            if not allowed:
                asyncio.ensure_future(
                    run_analysis_pipeline(
                        identity=identity,
                        signals=signals,
                        status_code=429,
                        request_uuid=request.state.request_uuid,
                        label=label,
                        fast_risk_score=risk_score,
                    )
                )

                response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. {count}/{limiter.max_requests} requests per minute.",
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
                
                set_user_cookie_if_needed(request, response)
                
                timings['total'] = time.time() - start_time
                response.headers["X-Process-Time"] = f"{timings['total']:.4f}"
                
                # Log rate limit with detailed timings
                logger.info(
                    f"RATE_LIMIT: user={identity.identity_id} | "
                    f"total={timings['total']:.3f}s | "
                    f"identity={timings['identity_resolution']:.3f}s | "
                    f"redis={timings['redis_decision']:.3f}s | "
                    f"rate_limit={timings['rate_limit']:.3f}s | "
                    f"timings={timings} | "
                    f"req_uuid={request.state.request_uuid}"
                )
                
                return response
            
            # ── 8. THROTTLED USERS ────────────────────────────────────────────
            if throttled:
                t0 = time.time()
                response = await call_next(request)
                timings['call_next'] = time.time() - t0
                process_time = time.time() - start_time
    
                response.headers["X-RateLimit-Limit"] = "100"
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = "60"
                response.headers["X-Request-UUID"] = request.state.request_uuid
                response.headers["X-Process-Time"] = f"{process_time:.4f}"
                response.headers["X-Throttled"] = "true"
    
                asyncio.ensure_future(
                    run_analysis_pipeline(
                        identity=identity,
                        signals=signals,
                        status_code=response.status_code,
                        request_uuid=request.state.request_uuid,
                        label=label,
                        fast_risk_score=risk_score,
                    )
                )
                
                set_user_cookie_if_needed(request, response)
                
                timings['total'] = process_time
                
                # Log throttled with detailed timings
                logger.info(
                    f"THROTTLED: user={identity.identity_id} | "
                    f"total={timings['total']:.3f}s | "
                    f"identity={timings['identity_resolution']:.3f}s | "
                    f"redis={timings['redis_decision']:.3f}s | "
                    f"call_next={timings['call_next']:.3f}s | "
                    f"timings={timings} | "
                    f"req_uuid={request.state.request_uuid}"
                )
                
                return response

            # ── 9. NORMAL FLOW ────────────────────────────────────────────────
            t0 = time.time()
            response = await call_next(request)
            timings['call_next'] = time.time() - t0
            process_time = time.time() - start_time

            response.headers["X-Request-UUID"] = request.state.request_uuid
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            set_user_cookie_if_needed(request, response)

            asyncio.ensure_future(
                run_analysis_pipeline(
                    identity=identity,
                    signals=signals,
                    status_code=response.status_code,
                    request_uuid=request.state.request_uuid,
                    label=label,
                    fast_risk_score=risk_score,
                )
            )

            timings['total'] = process_time
            
            # Log normal flow with detailed timings
            logger.info(
                f"NORMAL: user={identity.identity_id} | action={action} | "
                f"status={response.status_code} | "
                f"total={timings['total']:.3f}s | "
                f"identity={timings['identity_resolution']:.3f}s | "
                f"redis={timings['redis_decision']:.3f}s | "
                f"rate_limit={timings['rate_limit']:.3f}s | "
                f"call_next={timings['call_next']:.3f}s | "
                f"timings={timings} | "
                f"req_uuid={request.state.request_uuid}"
            )

            return response

        except Exception as e:
            logger.exception(f"Middleware error: {e} | timings={timings}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal middleware error"},
            )
            set_user_cookie_if_needed(request, response)
            response.headers["X-Process-Time"] = f"{time.time() - start_time:.4f}"
            return response


# ── FAST DECISION LOGIC ──────────────────────────────────────────────────────
async def _fast_decision(blocked: bool, throttled: bool, risk_score: float) -> tuple[str, str]:
    """
    Returns (action, reason) using only pre-computed Redis signals.
    """
    if blocked:
        return "block", "User or IP is temporarily blocked"
    if throttled:
        return "throttle", "Rate limit active"
    if risk_score > 0.70:
        return "block", "Severe risk score detected"
    if risk_score > 0.50:
        return "throttle", "High risk detected"
    if risk_score > 0.45:
        return "throttle", "Suspicious activity detected"
    return "allow", "Normal traffic"