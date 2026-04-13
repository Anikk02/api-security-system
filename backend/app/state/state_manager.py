import time
from app.state.redis_client import redis_client

WINDOW_SIZE = 60
MAX_REQUESTS = 100

class StateManager:

    # ---------------------------
    # RATE LIMITING
    # ---------------------------
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

    # ---------------------------
    # BLOCK MANAGEMENT
    # ---------------------------
    @staticmethod
    async def block_user(user_id: int, duration: int = 3600):
        key = f"user:{user_id}:blocked"
        await redis_client.set(key, "1", ex=duration)

    @staticmethod
    async def is_blocked(user_id: int) -> bool:
        key = f"user:{user_id}:blocked"
        return await redis_client.exists(key) == 1

    # ---------------------------
    # REQUEST TRACKING
    # ---------------------------
    @staticmethod
    async def log_request(user_id: int, endpoint: str, status_code: int, ip: str):
        ts = time.time()

        # timestamps
        await redis_client.zadd(
            f"user:{user_id}:timestamps",
            {str(ts): ts}
        )
        await redis_client.expire(f"user:{user_id}:timestamps", 300)

        # endpoints
        await redis_client.lpush(f"user:{user_id}:endpoints", endpoint)
        await redis_client.ltrim(f"user:{user_id}:endpoints", 0, 100)
        await redis_client.expire(f"user:{user_id}:endpoints", 300)

        # errors ONLY if status known
        if status_code and status_code >= 400:
            await redis_client.incr(f"user:{user_id}:errors")
            await redis_client.expire(f"user:{user_id}:errors", 300)

        # IP tracking
        if ip:
            await redis_client.sadd(f"user:{user_id}:ips", ip)
            await redis_client.expire(f"user:{user_id}:ips", 300)
    # ---------------------------
    # FEATURE BUILDER SUPPORT
    # ---------------------------
    @staticmethod
    async def get_request_count(user_id: int, window: int) -> int:
        now = time.time()
        key = f"user:{user_id}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)
        return await redis_client.zcount(key, now-window, now)

    @staticmethod
    async def get_recent_endpoints(user_id: int, window: int):
        data = await redis_client.lrange(f"user:{user_id}:endpoints", 0, -1)
        return [d.decode() if isinstance(d, bytes) else d for d in data]

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
    async def track_request(user_id: int, endpoint: str, ip: str):
        ts = time.time()

        # timestamps
        await redis_client.zadd(f"user:{user_id}:timestamps", {str(ts): ts})
        await redis_client.expire(f"user:{user_id}:timestamps", 300)

        # endpoints
        await redis_client.lpush(f"user:{user_id}:endpoints", endpoint)
        await redis_client.ltrim(f"user:{user_id}:endpoints", 0, 100)
        await redis_client.expire(f"user:{user_id}:endpoints", 300)

        # ip tracking
        await redis_client.sadd(f"user:{user_id}:ips", ip)
        await redis_client.expire(f"user:{user_id}:ips", 300)
    
    @staticmethod
    async def increment_error(user_id: int):
        key = f"user:{user_id}:errors"
        await redis_client.incr(key)
        await redis_client.expire(key, 300)