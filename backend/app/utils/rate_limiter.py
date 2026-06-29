import time
import logging
from app.state.redis_client import redis_client

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter - industry standard"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def check_and_allow(self, identifier: str) -> tuple[bool, int, int]:
        """
        Check if request is allowed and update counters.
        
        Returns:
            (is_allowed, current_count, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds
        key = f"ratelimit:{identifier}:{self.window_seconds}"
        
        try:
            # Single pipeline for atomic operation
            pipe = redis_client.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Get current count in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry (2x window to be safe)
            pipe.expire(key, self.window_seconds * 2)
            
            results = await pipe.execute()
            current_count = results[1]  # ZCARD result

            # NOTE: zcard above runs BEFORE this request's own zadd, so
            # current_count is the count *excluding* this request. This
            # request itself is always added to the set regardless of the
            # outcome below, so the comparison must be >= (not >) or the
            # max_requests-th request in a window gets admitted for free
            # before enforcement kicks in on the next one.
            if current_count >= self.max_requests:
                # Calculate retry time based on oldest request
                retry_after = await self._get_retry_after(key, now)
                return False, current_count, retry_after
            
            return True, current_count, 0
            
        except Exception as e:
            logger.error(f"Rate limiter failed: {e}")
            # Fail open (allow request) to avoid blocking during Redis issues
            return True, 0, 0
    
    async def _get_retry_after(self, key: str, now: float) -> int:
        """Calculate seconds until oldest request expires"""
        try:
            # Get the oldest request in the current window
            oldest = await redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]
                retry_after = int(oldest_timestamp + self.window_seconds - now)
                return max(1, retry_after)
        except Exception:
            pass
        return self.window_seconds


# Default limiters for different scenarios
minute_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)  # 60 req/min
second_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=1)   # 10 req/sec
strict_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)  # 30 req/min for high risk .