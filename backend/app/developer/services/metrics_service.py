"""
Business logic for Overview Dashboard, Traffic Analytics, and Abuse Monitoring.

Queries only RequestLog (+ Client for email/company joins) — never touches
per-client filtering, since this is platform-level data by design
(see developer.md: "operates at the platform level, not per-client level").
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog
from app.db.models.client import Client
from app.developer.utils.aggregations import requests_per_hour, requests_per_day
from app.websocket.developer_manager import developer_websocket_manager

logger = logging.getLogger(__name__)


# ── 1. Overview ───────────────────────────────────────────────────────────────

async def get_overview(db: AsyncSession, broadcast: bool = False) -> dict:
    """Total requests (all-time + today), active/total clients, top 5 consumers, 24h throughput."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    totals_result = await db.execute(
        select(
            func.count(RequestLog.id).label("all_time"),
            func.sum(case((RequestLog.created_at >= today_start, 1), else_=0)).label("today"),
        )
    )
    totals_row = totals_result.one()

    client_counts_result = await db.execute(
        select(
            func.count(Client.id).label("total"),
            func.sum(case((Client.status == "active", 1), else_=0)).label("active"),
        )
    )
    client_counts_row = client_counts_result.one()

    top_consumers_result = await db.execute(
        select(
            RequestLog.client_id,
            Client.email,
            Client.company_name,
            func.count(RequestLog.id).label("request_count"),
        )
        .join(Client, Client.id == RequestLog.client_id, isouter=True)
        .where(RequestLog.client_id.isnot(None))
        .group_by(RequestLog.client_id, Client.email, Client.company_name)
        .order_by(func.count(RequestLog.id).desc())
        .limit(5)
    )
    top_consumers = [
        {
            "client_id": row.client_id,
            "email": row.email,
            "company_name": row.company_name,
            "request_count": row.request_count,
        }
        for row in top_consumers_result.all()
    ]

    throughput_rows = await requests_per_hour(db, hours=24)
    throughput = [{"time": bucket, "requests": cnt} for bucket, cnt in throughput_rows]

    result = {
        "total_requests_all_time": totals_row.all_time or 0,
        "total_requests_today": totals_row.today or 0,
        "active_clients": client_counts_row.active or 0,
        "total_clients": client_counts_row.total or 0,
        "top_consumers": top_consumers,
        "throughput_last_24h": throughput,
    }

    # Broadcast metrics update via WebSocket
    if broadcast:
        await developer_websocket_manager.broadcast_metrics_update({
            "type": "overview",
            "payload": result
        })

    return result


# ── 2. Traffic Analytics ──────────────────────────────────────────────────────

async def get_traffic(db: AsyncSession, broadcast: bool = False) -> dict:
    """Requests by endpoint, by client, 7-day trend, and load distribution."""
    by_endpoint_result = await db.execute(
        select(RequestLog.endpoint, func.count(RequestLog.id).label("count"))
        .group_by(RequestLog.endpoint)
        .order_by(func.count(RequestLog.id).desc())
        .limit(20)
    )
    by_endpoint = [{"endpoint": row.endpoint, "count": row.count} for row in by_endpoint_result.all()]

    by_client_result = await db.execute(
        select(RequestLog.client_id, Client.email, func.count(RequestLog.id).label("count"))
        .join(Client, Client.id == RequestLog.client_id, isouter=True)
        .where(RequestLog.client_id.isnot(None))
        .group_by(RequestLog.client_id, Client.email)
        .order_by(func.count(RequestLog.id).desc())
        .limit(20)
    )
    by_client = [
        {"client_id": row.client_id, "email": row.email, "count": row.count}
        for row in by_client_result.all()
    ]

    trend_rows = await requests_per_day(db, days=7)
    trend = [{"day": bucket, "count": cnt} for bucket, cnt in trend_rows]

    result = {
        "requests_by_endpoint": by_endpoint,
        "requests_by_client": by_client,
        "traffic_trend_7d": trend,
        "load_distribution": by_endpoint,  # same data, alias used by frontend chart
    }

    if broadcast:
        await developer_websocket_manager.broadcast_metrics_update({
            "type": "traffic",
            "payload": result
        })

    return result


# ── 3. Abuse Monitoring ───────────────────────────────────────────────────────

async def get_abuse(db: AsyncSession, broadcast: bool = False) -> dict:
    """Top abusive clients, most-blocked IPs, high-frequency sources, endpoint abuse patterns."""
    block_filter = RequestLog.action == "block"

    abusive_clients_result = await db.execute(
        select(RequestLog.client_id, Client.email, func.count(RequestLog.id).label("blocked_count"))
        .join(Client, Client.id == RequestLog.client_id, isouter=True)
        .where(and_(block_filter, RequestLog.client_id.isnot(None)))
        .group_by(RequestLog.client_id, Client.email)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
    )
    abusive_clients = [
        {"client_id": row.client_id, "email": row.email, "blocked_count": row.blocked_count}
        for row in abusive_clients_result.all()
    ]

    blocked_ips_result = await db.execute(
        select(RequestLog.ip_address, func.count(RequestLog.id).label("blocked_count"))
        .where(and_(block_filter, RequestLog.ip_address.isnot(None)))
        .group_by(RequestLog.ip_address)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
    )
    blocked_ips = [
        {"ip_address": row.ip_address, "blocked_count": row.blocked_count}
        for row in blocked_ips_result.all()
    ]

    high_freq_result = await db.execute(
        select(
            RequestLog.identity_id,
            RequestLog.client_id,
            func.count(RequestLog.id).label("total_requests"),
        )
        .where(RequestLog.identity_id.isnot(None))
        .group_by(RequestLog.identity_id, RequestLog.client_id)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
    )
    high_freq = [
        {
            "identity_id": row.identity_id,
            "client_id": row.client_id,
            "total_requests": row.total_requests,
        }
        for row in high_freq_result.all()
    ]

    endpoint_abuse_result = await db.execute(
        select(RequestLog.endpoint, func.count(RequestLog.id).label("blocked_count"))
        .where(block_filter)
        .group_by(RequestLog.endpoint)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
    )
    endpoint_abuse = [
        {"endpoint": row.endpoint, "blocked_count": row.blocked_count}
        for row in endpoint_abuse_result.all()
    ]

    result = {
        "top_abusive_clients": abusive_clients,
        "most_blocked_ips": blocked_ips,
        "high_freq_sources": high_freq,
        "endpoint_abuse_patterns": endpoint_abuse,
    }

    # Broadcast abuse alert if significant abuse detected
    if broadcast and abusive_clients:
        await developer_websocket_manager.broadcast_abuse_alert({
            "type": "abuse_detected",
            "top_abusive_clients": abusive_clients[:3],
            "most_blocked_ips": blocked_ips[:3],
            "timestamp": datetime.utcnow().isoformat()
        })

    return result