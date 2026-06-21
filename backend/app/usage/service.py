from sqlalchemy import select, func, distinct
from datetime import datetime, timedelta

from db.models.request_log import RequestLog


async def get_usage_data(db, client_id: int):
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)

    # =========================================
    # 📊 BASE FILTER
    # =========================================
    base = select(RequestLog).where(RequestLog.client_id == client_id).subquery()

    last_hour_base = select(RequestLog).where(
        RequestLog.client_id == client_id,
        RequestLog.created_at >= last_hour
    ).subquery()

    # =========================================
    # 📊 METRICS (SUBQUERY)
    # =========================================
    metrics_query = select(
        func.count(base.c.id).label("total_requests"),
        func.count(last_hour_base.c.id).label("last_hour_requests"),
        func.count(distinct(base.c.ip_address)).label("unique_ips"),
        func.sum(
            func.case(
                (base.c.action == "allowed", 1),
                else_=0
            )
        ).label("success")
    )

    metrics_result = (await db.execute(metrics_query)).one()

    total_requests = metrics_result.total_requests or 0
    last_hour_requests = metrics_result.last_hour_requests or 0
    unique_ips = metrics_result.unique_ips or 0
    success = metrics_result.success or 0

    avg_rps = round(last_hour_requests / 3600, 2) if last_hour_requests else 0
    success_rate = round((success / total_requests) * 100, 2) if total_requests else 0

    # =========================================
    # 📈 TREND
    # =========================================
    trend_query = await db.execute(
        select(
            func.date_trunc("minute", RequestLog.created_at).label("time"),
            func.count().label("requests")
        )
        .where(
            RequestLog.client_id == client_id,
            RequestLog.created_at >= last_hour
        )
        .group_by("time")
        .order_by("time")
    )

    trend = [
        {
            "time": row.time.strftime("%H:%M"),
            "requests": row.requests
        }
        for row in trend_query.all()
    ]

    # =========================================
    # 🎯 ENDPOINTS
    # =========================================
    endpoint_query = await db.execute(
        select(
            RequestLog.endpoint,
            func.count().label("requests")
        )
        .where(RequestLog.client_id == client_id)
        .group_by(RequestLog.endpoint)
        .order_by(func.count().desc())
        .limit(5)
    )

    endpoints = [
        {
            "endpoint": row.endpoint,
            "requests": row.requests
        }
        for row in endpoint_query.all()
    ]

    # =========================================
    # 🚀 FINAL RESPONSE
    # =========================================
    return {
        "metrics": {
            "total_requests": total_requests,
            "avg_rps": avg_rps,
            "unique_ips": unique_ips,
            "success_rate": success_rate
        },
        "trend": trend,
        "endpoints": endpoints
    }