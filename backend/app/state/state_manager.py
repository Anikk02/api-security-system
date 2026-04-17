import time
import logging
from app.state.redis_client import redis_client

WINDOW_SIZE = 60
MAX_REQUESTS = 100

logger = logging.getLogger(__name__)

async def safe_redis_call(coro):
    try:
        return await coro
    except Exception as e:
        logger.error(f"Redis failure: {e}")
        return None
class StateManager:

    # RATE LIMITING
    @staticmethod
    async def increment_request(user_id: int) -> int:
        key = f"user:{user_id}:count"

        current = await redis_client.get(key)

        if current is None:
            await redis_client.set(key, 1, ex=WINDOW_SIZE)
            return 1
        
        return await redis_client.incr(key)

    @staticmethod
    async def is_rate_limited(user_id: int) -> bool:
        req_per_min = await StateManager.get_request_count(user_id, 60)
        return req_per_min > MAX_REQUESTS

    # BLOCK MANAGEMENT
    @staticmethod
    async def block_user(user_id: int, duration: int = 3600):
        key = f"user:{user_id}:blocked"
        await redis_client.set(key, "1", ex=duration)

    @staticmethod
    async def is_blocked(user_id: int) -> bool:
        key = f"user:{user_id}:blocked"
        return await redis_client.exists(key) == 1

    # REQUEST TRACKING
    '''@staticmethod
    async def log_request(user_id: int, endpoint: str, status_code: int, ip: str):
        ts = time.time()

        try:
            pipe = redis_client.pipeline()

            # 🔹 TIMESTAMPS (for sliding window)
            key_ts = f"user:{user_id}:timestamps"
            pipe.zadd(key_ts, {str(ts): ts})
            pipe.zremrangebyscore(key_ts, 0, ts - 300)  # keep last 5 min clean
            pipe.expire(key_ts, 300)

            # 🔹 ENDPOINTS
            key_ep = f"user:{user_id}:endpoints"
            pipe.lpush(key_ep, endpoint)
            pipe.ltrim(key_ep, 0, 100)  # keep last 100
            pipe.expire(key_ep, 300)

            # 🔹 ERRORS
            if status_code and status_code >= 400:
                key_err = f"user:{user_id}:errors"
                pipe.incr(key_err)
                pipe.expire(key_err, 300)

            # 🔹 IP TRACKING
            if ip:
                key_ip = f"user:{user_id}:ips"
                pipe.sadd(key_ip, ip)
                pipe.expire(key_ip, 300)

            # 🔹 EXECUTE SAFELY
            await safe_redis_call(pipe.execute())

        except Exception as e:
            logger.error(f"log_request failed: {e}")'''

    # FEATURE BUILDER SUPPORT
    @staticmethod
    async def get_request_count(user_id: int, window: int) -> int:
        now = time.time()
        key = f"user:{user_id}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)
        count = await safe_redis_call(redis_client.zcount(key, now-window, now))
        return count or 0

    @staticmethod
    async def get_recent_endpoints(user_id: int, window: int):
        try:
            now = time.time()
            key = f"user:{user_id}:endpoints"

            await redis_client.zremrangebyscore(key, 0, now - window)

            data = await redis_client.zrange(key, 0, -1)

            if not data:
                return []

            endpoints = []

            for d in data:
                #  CRITICAL: skip invalid types
                if isinstance(d, int):
                    continue

                val = d.decode() if isinstance(d, bytes) else str(d)

                # extract endpoint safely
                if "|" in val:
                    parts = val.split("|", 1)
                    if len(parts) == 2:
                        endpoints.append(parts[1])
                else:
                    endpoints.append(val)

            return endpoints

        except Exception as e:
            logger.error(f"get_recent_endpoints failed: {e}")
            return []

            
    @staticmethod
    async def get_error_count(user_id: int, window: int):
        val = await redis_client.get(f"user:{user_id}:errors")
        return int(val) if val else 0

    @staticmethod
    async def get_request_timestamps(user_id: int, window: int):
        now = time.time()
        key = f"user:{user_id}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)

        data = await redis_client.zrange(key, 0, -1, withscores=True)
        return [score for _, score in data]

    @staticmethod
    async def get_ip_change_count(user_id: int, window: int):
        key = f"user:{user_id}:ips"
        ips = await redis_client.smembers(key)
        return len(ips)

    @staticmethod
    async def track_ip(user_id: int, ip: str):
        key = f"user:{user_id}:ips"
        await redis_client.sadd(key, ip)
        await redis_client.expire(key, 300)

    @classmethod
    async def increment_violation(user_id: int):
        key = f"user:{user_id}:violations"
        val = await redis_client.incr(key)
        await redis_client.expire(key, 3600)
        return val

    @staticmethod
    async def get_violations(user_id: int):
        val = await redis_client.get(f"user:{user_id}:violations")
        return int(val) if val else 0
    
    @staticmethod
    async def track_request(user_id: int, endpoint: str, ip: str, status_code: int):
        ts = time.time()

        key_ts = f"user:{user_id}:timestamps"
        key_ep = f"user:{user_id}:endpoints"
        key_ip = f"user:{user_id}:ips"
        key_err = f"user:{user_id}:errors"

        pipe = redis_client.pipeline()

        #  timestamps
        pipe.zadd(key_ts, {str(ts): ts})
        pipe.zremrangebyscore(key_ts, 0, ts - 300)   # ✅ sliding window cleanup
        pipe.expire(key_ts, 300)

        #  endpoints
        pipe.zadd(key_ep, {f"{ts}|{endpoint}":ts})
        pipe.zremrangebyscore(key_ep, 0,ts - 300)
        pipe.expire(key_ep, 300)

        #  ip tracking
        pipe.sadd(key_ip, ip)
        pipe.expire(key_ip, 300)

        #  USE status_code
        if status_code and status_code >= 400:
            pipe.incr(key_err)
            pipe.expire(key_err, 300)

        await safe_redis_call(pipe.execute())
    @staticmethod
    async def increment_error(user_id: int):
        key = f"user:{user_id}:errors"
        await redis_client.incr(key)
        await redis_client.expire(key, 300)

    @staticmethod
    async def get(key: str):
        try:
            value = await redis_client.get(key)
            return value.decode() if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Redis GET failed: {e}")
            return None


    @staticmethod
    async def set(key: str, value, ttl: int = None):
        try:
            if ttl:
                await redis_client.set(key, value, ex=ttl)
            else:
                await redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET failed: {e}")