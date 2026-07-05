"""
Shared aggregation helpers for the Developer Panel.

These wrap common GROUP BY / date_trunc patterns already used throughout the
codebase (see app/api/routes/dashboard.py, app/usage/service.py) so
metrics_service.py and system_service.py don't repeat the same query shapes.
"""
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog


async def count_grouped_by(
    db: AsyncSession,
    column,
    extra_filter=None,
    limit: int = 10,
):
    """
    Generic top-N GROUP BY count on a RequestLog column.

    Example:
        rows = await count_grouped_by(db, RequestLog.endpoint, limit=5)
        # -> [(endpoint, count), ...] ordered descending
    """
    query = select(column, func.count(RequestLog.id).label("cnt"))
    if extra_filter is not None:
        query = query.where(extra_filter)
    query = (
        query.group_by(column)
        .order_by(func.count(RequestLog.id).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.all()


async def requests_per_hour(db: AsyncSession, hours: int = 24):
    """Hourly request counts for the last N hours — used by Overview throughput chart."""
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(
            func.date_trunc("hour", RequestLog.created_at).label("bucket"),
            func.count(RequestLog.id).label("cnt"),
        )
        .where(RequestLog.created_at >= since)
        .group_by("bucket")
        .order_by("bucket")
    )
    return result.all()


async def requests_per_day(db: AsyncSession, days: int = 7):
    """Daily request counts for the last N days — used by Traffic Analytics trend chart."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date_trunc("day", RequestLog.created_at).label("bucket"),
            func.count(RequestLog.id).label("cnt"),
        )
        .where(RequestLog.created_at >= since)
        .group_by("bucket")
        .order_by("bucket")
    )
    return result.all()
