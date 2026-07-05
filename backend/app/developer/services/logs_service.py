"""
Business logic for the Global Logs module.
Paginated, filterable read across ALL clients' RequestLog rows —
the platform-wide counterpart to app/api/routes/dashboard.py's
per-client get_decision_logs().
"""
import logging
import math
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog
from app.developer.utils.filters import apply_request_log_filters

logger = logging.getLogger(__name__)


async def get_logs(
    db: AsyncSession,
    client_id: int | None = None,
    identity_id: str | None = None,
    ip_address: str | None = None,
    endpoint: str | None = None,
    action: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Return one page of RequestLog rows matching the given filters, newest first."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 200:
        page_size = 50

    query = select(RequestLog)
    query = apply_request_log_filters(
        query,
        client_id=client_id,
        identity_id=identity_id,
        ip_address=ip_address,
        endpoint=endpoint,
        action=action,
        start_time=start_time,
        end_time=end_time,
    )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        query.order_by(RequestLog.created_at.desc()).offset(offset).limit(page_size)
    )
    logs = rows_result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "logs": logs,
    }
