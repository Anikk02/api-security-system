import hashlib
import secrets
from datetime import datetime

from sqlalchemy import select

from app.db.models.api_key import APIKey
from app.db.models.clients import Client


def _mask_api_key(raw_key: str | None) -> str | None:
    if not raw_key:
        return None
    if len(raw_key) <= 12:
        return raw_key
    return f"{raw_key[:8]}...{raw_key[-4:]}"


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def _get_client(db, client_id: int) -> Client | None:
    result = await db.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


async def _get_active_api_key(db, client_id: int) -> APIKey | None:
    result = await db.execute(
        select(APIKey)
        .where(APIKey.client_id == client_id, APIKey.is_active == True)
        .order_by(APIKey.created_at.desc())
    )
    return result.scalar_one_or_none()


async def get_settings_overview(db, client_id: int):
    client = await _get_client(db, client_id)
    api_key = await _get_active_api_key(db, client_id)

    return {
        "profile": {
            "id": client.id if client else client_id,
            "email": client.email if client else "",
            "created_at": client.created_at if client else datetime.utcnow(),
        },
        "api_key": {
            "masked": _mask_api_key(getattr(api_key, "key_hash", None)),
            "is_active": bool(api_key and api_key.is_active),
            "created_at": api_key.created_at if api_key else None,
        },
    }


async def regenerate_api_key(db, client_id: int):
    existing = await _get_active_api_key(db, client_id)
    if existing:
        existing.is_active = False

    raw_key = "sk_live_" + secrets.token_hex(24)
    api_key = APIKey(
        key_hash=_hash_api_key(raw_key),
        client_id=client_id,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "api_key": raw_key,
        "message": "API key regenerated successfully",
    }


async def update_profile(db, client_id: int, email: str):
    client = await _get_client(db, client_id)
    if client:
        client.email = email
        await db.commit()

    return {"message": "Profile updated successfully"}
