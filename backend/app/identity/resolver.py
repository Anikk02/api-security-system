import hashlib
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.api_key import APIKey
import logging

logger = logging.getLogger(__name__)
class Identity:
    def __init__(self, user_id: int, api_key: str | None, is_anonymous: bool):
        self.user_id = user_id
        self.api_key = api_key
        self.is_anonymous = is_anonymous

        # Derived attributes (attached later)
        self.ip_address = None
        self.behavioral_fingerprint = None

    
async def resolve_identity(request: Request, db: AsyncSession) -> Identity:
    logger.info(f"[IDENTITY] Resolving for path={request.url.path}")
    
    TRUST_PROXY = True
    if TRUST_PROXY:
        # Extract IP (single source of truth)
        forwarded_ip = request.headers.get("X-Forwarded-For")

        if forwarded_ip:
            ip = forwarded_ip.split(",")[0].strip()
            logger.debug(f"[IDENTITY] X-Forwarded-For detected → ip={ip}")
        else:
            ip = request.client.host if request.client else 'unknown'
            logger.debug(f"[IDENTITY] Direct client IP → ip={ip}")

    api_key = request.headers.get('X-API-KEY')

    if api_key:
        logger.debug(f"[IDENTITY] API key received (masked) from ip={ip}")

        result = await db.execute(
            select(APIKey).where(APIKey.key == api_key)
        )

        api_key_obj = result.scalar_one_or_none()

        if api_key_obj:
            logger.info(f"[IDENTITY] Authenticated user_id={api_key_obj.user_id} ip={ip}")

            identity = Identity(
                user_id=api_key_obj.user_id,
                api_key=api_key,
                is_anonymous=False
            )

            identity.ip_address = ip

            identity.behavioral_fingerprint = _generate_behavioral_fingerprint(request, identity)

            return identity

        else:
            logger.warning(f"[IDENTITY] Invalid API key from ip={ip}, falling back to anonymous")

    # Anonymous fallback
    fingerprint = _generate_anonymous_fingerprint(ip)

    logger.debug(f"[IDENTITY] Anonymous fingerprint generated user_id={fingerprint} ip={ip}")

    identity = Identity(
        user_id=fingerprint,
        api_key=None,
        is_anonymous=True
    )

    identity.ip_address = ip

    logger.info(f"[IDENTITY] Anonymous identity assigned user_id={fingerprint} ip={ip}")

    identity.behavioral_fingerprint = _generate_behavioral_fingerprint(request, identity)

    return identity

def _generate_anonymous_fingerprint(ip: str) -> int:
    if not ip:
        ip = "unknown"

    hashed = hashlib.sha256(ip.encode()).hexdigest()

    return int(hashed[:16], 16) % (2**63 - 1)

def _generate_behavioral_fingerprint(request: Request, identity: Identity) -> str:
    """Generate a stable fingerprint based on headers + identity anchor
    Does not include IP"""
    ua = request.headers.get("user-agent", "")
    accept_lang = request.headers.get("accept-language", "")
    accept_enc = request.headers.get("accept-encoding", "")

    #Strong anchor if API key exists
    if identity.api_key:
        api_hash = hashlib.sha256(identity.api_key.encode()).hexdigest()
        raw = f"{api_hash}:{ua}:{accept_lang}:{accept_enc}"
    else:
        raw = f"{ua}:{accept_lang}:{accept_enc}"
    
    return hashlib.sha256(raw.encode()).hexdigest()
