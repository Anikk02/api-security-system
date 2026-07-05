"""
Business logic for Client Management.
Reuses the existing Client and APIKey models — no duplicate tables,
no new auth system. Mirrors the query/commit/refresh pattern already
used in app/api/routes/api_keys.py.
"""
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.client import Client
from app.db.models.api_key import APIKey
from app.db.models.request_log import RequestLog

logger = logging.getLogger(__name__)

VALID_STATUSES = {"active", "inactive", "suspended", "locked"}


async def get_all_clients(db: AsyncSession) -> dict:
    """List every registered client with request counts and API key info."""
    clients_result = await db.execute(select(Client).order_by(Client.created_at.desc()))
    clients = clients_result.scalars().all()

    if not clients:
        return {"total": 0, "clients": []}

    client_ids = [c.id for c in clients]

    counts_result = await db.execute(
        select(RequestLog.client_id, func.count(RequestLog.id).label("count"))
        .where(RequestLog.client_id.in_(client_ids))
        .group_by(RequestLog.client_id)
    )
    counts_by_client = {row.client_id: row.count for row in counts_result.all()}

    keys_result = await db.execute(
        select(APIKey).where(APIKey.client_id.in_(client_ids)).order_by(APIKey.created_at.desc())
    )
    keys_by_client: dict[int, list] = {}
    for key in keys_result.scalars().all():
        keys_by_client.setdefault(key.client_id, []).append(key)

    clients_out = [
        {
            "id": c.id,
            "email": c.email,
            "company_name": c.company_name,
            "role": c.role,
            "status": c.status,
            "email_verified": c.email_verified,
            "created_at": c.created_at,
            "last_login_at": c.last_login_at,
            "total_requests": counts_by_client.get(c.id, 0),
            "api_keys": keys_by_client.get(c.id, []),
        }
        for c in clients
    ]

    return {"total": len(clients_out), "clients": clients_out}


async def get_client_by_id(db: AsyncSession, client_id: int) -> dict | None:
    """Single client lookup, same response shape as get_all_clients rows."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        return None

    count_result = await db.execute(
        select(func.count(RequestLog.id)).where(RequestLog.client_id == client_id)
    )
    total_requests = count_result.scalar() or 0

    keys_result = await db.execute(
        select(APIKey).where(APIKey.client_id == client_id).order_by(APIKey.created_at.desc())
    )
    api_keys = keys_result.scalars().all()

    return {
        "id": client.id,
        "email": client.email,
        "company_name": client.company_name,
        "role": client.role,
        "status": client.status,
        "email_verified": client.email_verified,
        "created_at": client.created_at,
        "last_login_at": client.last_login_at,
        "total_requests": total_requests,
        "api_keys": api_keys,
    }


async def set_client_status(db: AsyncSession, client_id: int, new_status: str) -> dict | None:
    """Activate / deactivate / suspend / lock a client account."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {sorted(VALID_STATUSES)}")

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        return None

    client.status = new_status
    if new_status != "locked":
        client.locked_until = None
        client.failed_login_attempts = 0

    await db.commit()
    await db.refresh(client)

    logger.info(f"[DEVELOPER PANEL] Client {client_id} status set to '{new_status}'")
    return {"id": client.id, "status": client.status}


async def revoke_api_key(db: AsyncSession, api_key_id: int) -> dict | None:
    """
    Deactivate (not delete) a client's API key so request_logs/decision_logs
    that reference api_key_id keep their audit trail intact.
    """
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        return None

    key_obj.is_active = False
    await db.commit()
    await db.refresh(key_obj)

    logger.info(f"[DEVELOPER PANEL] API key {api_key_id} revoked (client {key_obj.client_id})")
    return {"id": key_obj.id, "client_id": key_obj.client_id, "is_active": key_obj.is_active}
