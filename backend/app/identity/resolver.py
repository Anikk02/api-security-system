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

    
async def resolve_identity(request: Request, db: AsyncSession) -> Identity:
    '''
    Resolver user identity from request using:
    - API Key (primary)
    - fallback: anonymous user
    '''
    logger.info(f"Resolving identity for {request.url.path}")
    api_key = request.headers.get('X-API-KEY')

    if api_key:
        logger.debug(f"API key received")
        result = await db.execute(
            select(APIKey).where(APIKey.key==api_key)
        )

        api_key_obj = result.scalar_one_or_none()

        if api_key_obj:
            logger.info(f"User identified: user_id={api_key_obj.user_id}")

            return Identity(
                user_id = api_key_obj.user_id,
                api_key = api_key,
                is_anonymous=False
            )
        else:
            logger.info("Invalid API key, falling back to anonymous")
    
    fingerprint = _generate_anonymous_fingerprint(request)

    logger.debug(f"Anonymous user assigned id={fingerprint}")

    return Identity(
        user_id = fingerprint,
        api_key=None,
        is_anonymous=True
    )

def _generate_anonymous_fingerprint(request: Request) -> int:
    ip = request.client.host if request.client else 'unknown'

    raw = ip  

    hashed = hashlib.sha256(raw.encode()).hexdigest()

    return int(hashed[:16], 16)
