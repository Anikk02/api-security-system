"""
Business logic for System Health.
Reuses the shared async Redis client (app/state/redis_client.py) directly —
no new connection, no hardcoded host/port.
"""
import logging
from datetime import datetime

from sqlalchemy import select, func, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog
from app.state.redis_client import redis_client
from app.websocket.developer_manager import developer_websocket_manager

logger = logging.getLogger(__name__)


async def get_system_health(db: AsyncSession, broadcast: bool = False) -> dict:
    """DB ping, Redis ping, error rate, and today's action breakdown."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── DB health ──
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"[DEVELOPER PANEL] DB health check failed: {e}")
        db_status = "down"

    # ── Redis health ──
    redis_status = "healthy"
    try:
        pong = await redis_client.ping()
        if not pong:
            redis_status = "down"
    except Exception as e:
        logger.error(f"[DEVELOPER PANEL] Redis health check failed: {e}")
        redis_status = "down"

    # ── Today's action breakdown ──
    today_result = await db.execute(
        select(
            func.count(RequestLog.id).label("total"),
            func.sum(case((RequestLog.action == "block", 1), else_=0)).label("blocked"),
            func.sum(case((RequestLog.action == "throttle", 1), else_=0)).label("throttled"),
            func.sum(case((RequestLog.action == "allow", 1), else_=0)).label("allowed"),
        ).where(RequestLog.created_at >= today_start)
    )
    today_row = today_result.one()
    total_today = today_row.total or 0
    blocked_today = today_row.blocked or 0
    throttled_today = today_row.throttled or 0
    allowed_today = today_row.allowed or 0

    error_rate_pct = (
        round(((blocked_today + throttled_today) / total_today) * 100, 2)
        if total_today else 0.0
    )

    # NOTE: RequestLog has no duration/latency column today, so we cannot
    # compute a real avg_latency_ms. Surfacing None rather than fabricating
    # a number — add a duration_ms column to RequestLog if this is needed.
    avg_latency_ms = None

    result = {
        "db_status": db_status,
        "redis_status": redis_status,
        "avg_latency_ms": avg_latency_ms,
        "error_rate_pct": error_rate_pct,
        "total_requests_today": total_today,
        "blocked_today": blocked_today,
        "throttled_today": throttled_today,
        "allowed_today": allowed_today,
    }

    # Broadcast system health via WebSocket if requested
    if broadcast:
        await developer_websocket_manager.broadcast_system_health(result)

    return result