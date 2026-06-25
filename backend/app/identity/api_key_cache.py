import hashlib
import logging
from typing import Optional
from cachetools import TTLCache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.api_key import APIKey

logger = logging.getLogger(__name__)

# ============================
# 🗄️ API Key Cache Configuration
# ============================

# Main cache: Store up to 1000 API keys, expire after 5 minutes
# This is a safety net - if someone revokes a key, it will expire within 5 minutes
API_KEY_CACHE = TTLCache(maxsize=1000, ttl=300)

# Negative cache: Store invalid API keys for 1 minute to prevent brute force
# Shorter TTL because we don't want to lock out legitimate keys if there's a typo
INVALID_KEY_CACHE = TTLCache(maxsize=1000, ttl=60)

# ============================
# 🔍 Cache Operations
# ============================

async def get_api_key_cached(
    hashed_key: str, 
    db: AsyncSession
) -> Optional[APIKey]:
    """
    Get API key from cache or database.
    
    Priority:
    1. Check main cache → Return if found
    2. Check invalid cache → Return None if known invalid
    3. Query database → Store result in appropriate cache
    
    Args:
        hashed_key: SHA256 hash of the API key
        db: AsyncSession for database queries
    
    Returns:
        APIKey object or None if invalid
    """
    
    # 1. Check main cache
    if hashed_key in API_KEY_CACHE:
        logger.debug(f"[CACHE] API key cache HIT: {hashed_key[:8]}...")
        return API_KEY_CACHE[hashed_key]
    
    # 2. Check negative cache (known invalid keys)
    if hashed_key in INVALID_KEY_CACHE:
        logger.debug(f"[CACHE] API key negative cache HIT: {hashed_key[:8]}...")
        return None
    
    # 3. Cache miss → Query database
    logger.debug(f"[CACHE] API key cache MISS: {hashed_key[:8]}... Querying DB...")
    
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == hashed_key)
    )
    api_key_obj = result.scalar_one_or_none()
    
    # 4. Store result in cache
    if api_key_obj:
        # Valid API key → Store in main cache
        API_KEY_CACHE[hashed_key] = api_key_obj
        logger.debug(f"[CACHE] Valid API key cached: {hashed_key[:8]}...")
        
        # Also store by ID for quick lookups (optional)
        API_KEY_CACHE[f"id:{api_key_obj.id}"] = api_key_obj
    else:
        # Invalid API key → Store in negative cache (shorter TTL)
        INVALID_KEY_CACHE[hashed_key] = True
        logger.debug(f"[CACHE] Invalid API key cached (negative): {hashed_key[:8]}...")
    
    return api_key_obj


async def get_api_key_by_id_cached(
    api_key_id: int, 
    db: AsyncSession
) -> Optional[APIKey]:
    """
    Get API key by ID from cache or database.
    Useful for admin operations where you have the ID.
    """
    cache_key = f"id:{api_key_id}"
    
    # Check cache
    if cache_key in API_KEY_CACHE:
        logger.debug(f"[CACHE] API key by ID cache HIT: {api_key_id}")
        return API_KEY_CACHE[cache_key]
    
    # Query database
    result = await db.execute(
        select(APIKey).where(APIKey.id == api_key_id)
    )
    api_key_obj = result.scalar_one_or_none()
    
    # Cache by both ID and hash
    if api_key_obj:
        API_KEY_CACHE[cache_key] = api_key_obj
        API_KEY_CACHE[api_key_obj.key_hash] = api_key_obj
        logger.debug(f"[CACHE] API key by ID cached: {api_key_id}")
    
    return api_key_obj


def invalidate_api_key_cache(hashed_key: str, api_key_id: Optional[int] = None) -> None:
    """
    Invalidate API key from all caches.
    Call this when:
    - API key is revoked
    - API key is deleted
    - API key permissions change
    - API key is regenerated
    
    Args:
        hashed_key: SHA256 hash of the API key
        api_key_id: Optional ID to also invalidate by ID cache
    """
    # Remove from main cache
    if hashed_key in API_KEY_CACHE:
        del API_KEY_CACHE[hashed_key]
        logger.info(f"[CACHE] API key invalidated (by hash): {hashed_key[:8]}...")
    
    # Remove from negative cache
    if hashed_key in INVALID_KEY_CACHE:
        del INVALID_KEY_CACHE[hashed_key]
        logger.debug(f"[CACHE] API key removed from negative cache: {hashed_key[:8]}...")
    
    # Remove by ID if provided
    if api_key_id:
        cache_key = f"id:{api_key_id}"
        if cache_key in API_KEY_CACHE:
            del API_KEY_CACHE[cache_key]
            logger.info(f"[CACHE] API key invalidated (by ID): {api_key_id}")


def clear_all_api_key_cache() -> None:
    """Clear all API key caches (use with caution)"""
    API_KEY_CACHE.clear()
    INVALID_KEY_CACHE.clear()
    logger.warning("[CACHE] All API key caches cleared!")


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring"""
    return {
        "main_cache_size": len(API_KEY_CACHE),
        "main_cache_maxsize": API_KEY_CACHE.maxsize,
        "negative_cache_size": len(INVALID_KEY_CACHE),
        "negative_cache_maxsize": INVALID_KEY_CACHE.maxsize,
        "main_cache_usage_percent": (len(API_KEY_CACHE) / API_KEY_CACHE.maxsize) * 100
    }
