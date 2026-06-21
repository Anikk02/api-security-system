from sqlalchemy import select
from datetime import datetime, timedelta

from models.request_log import RequestLog
from activity.analyzer import analyze_activity


async def get_activity_data(db, client_id: int):
    time_threshold = datetime.utcnow() - timedelta(minutes=30)

    result = await db.execute(
        select(RequestLog).where(
            RequestLog.client_id == client_id,
            RequestLog.created_at >= time_threshold
        )
    )

    logs = result.scalars().all()

    return analyze_activity(logs)