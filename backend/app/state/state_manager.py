import time
import logging
import hashlib
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

    # ─────────────────────────────────────────────────────────────
    # FAST DECISION PATH (single Redis round-trip)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_decision_signals(user_id: int, ip: str = None, fingerprint: str = None):
        pipe = redis_client.pipeline()

        pipe.exists(f"user:{user_id}:blocked")
        pipe.get(f"user:{user_id}:risk_score")
        pipe.exists(f"user:{user_id}:throttled")

        
        # IP Block Check
        if ip:
            pipe.exists(f"ip:{ip}:blocked")
        
        if fingerprint:
            pipe.exists(f"fp:{fingerprint}:blocked")
            pipe.get(f"rep:fp:{fingerprint}")
        try:
            results = await pipe.execute()

            user_blocked = bool(results[0])
            risk_raw = results[1]
            user_throttled = bool(results[2])

            idx = 3
            ip_blocked = False
            fp_blocked = False
            fp_rep = 0.0

            if ip:
                ip_blocked = bool(results[idx])
                idx += 1
            if fingerprint:
                fp_blocked = bool(results[idx])
                idx += 1
                
                if len(results) > idx:
                    fp_rep_raw = results[idx]
                    idx += 1

                    if fp_rep_raw:
                        try:
                            val = fp_rep_raw.decode() if isinstance(fp_rep_raw, bytes) else fp_rep_raw
                            fp_rep = float(val)
                        except:
                            fp_rep = 0.0


            #Combine block status
            blocked = user_blocked or ip_blocked or fp_blocked
            throttled = user_throttled

            risk_score = 0.0
            if risk_raw is not None:
                try:
                    val = risk_raw.decode() if isinstance(risk_raw, bytes) else risk_raw
                    risk_score = float(val)
                except Exception:
                    risk_score = 0.0
            risk_score = min(1.0, risk_score + (fp_rep * 0.2))

            return blocked, risk_score, throttled
        
        except Exception as e:
            logger.error(f"get_decision_signals pipeline failed: {e}")
            return False, 0.0, False

    # ─────────────────────────────────────────────────────────────
    # REQUEST TRACKING (ZSET-based sliding window)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def track_request_async(user_id: int, endpoint: str, ip: str, status_code: int | None):
        ts = time.time()

        pipe = redis_client.pipeline()

        key_ts = f"user:{user_id}:timestamps"
        key_ep = f"user:{user_id}:endpoints"
        key_ip = f"user:{user_id}:ips"
        key_err = f"user:{user_id}:errors"

        pipe.zadd(key_ts, {str(ts): ts})
        pipe.zremrangebyscore(key_ts, 0, ts - 300)
        pipe.expire(key_ts, 300)

        pipe.zadd(key_ep, {f"{ts}|{endpoint}": ts})
        pipe.zremrangebyscore(key_ep, 0, ts - 300)
        pipe.expire(key_ep, 300)

        # IP tracking (session-based diversity signal)
        pipe.sadd(key_ip, ip)
        pipe.expire(key_ip, 300)

        # error tracking
        if status_code is not None and status_code >= 400:
            pipe.incr(key_err)
            pipe.expire(key_err, 300)

        try:
            await pipe.execute()
        except Exception as e:
            logger.error(f"track_request_async pipeline failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def delete(key: str):
        try:
            await redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # RATE LIMITING (SINGLE SOURCE OF TRUTH: ZSET)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_request_count(user_id: int, window: int):
        now = time.time()
        key = f"user:{user_id}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)

        result = await safe_redis_call(
            redis_client.zcount(key, now - window, now)
        )

        return result or 0

    @staticmethod
    async def is_rate_limited(user_id: int) -> bool:
        count = await StateManager.get_request_count(user_id, WINDOW_SIZE)
        return count > MAX_REQUESTS

    # ─────────────────────────────────────────────────────────────
    # BLOCK MANAGEMENT (CAP: 12 HOURS MAX TTL)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def block_user(user_id: int, duration: int = 3600):
        max_ttl = 60 * 60 * 12  # 12 hours
        duration = min(duration, max_ttl)

        await redis_client.set(
            f"user:{user_id}:blocked",
            "1",
            ex=duration
        )

    @staticmethod
    async def block_ip(ip: str, duration: int = 3600):
        max_ttl = 60 * 60 * 12  # 12 hours
        duration = min(duration, max_ttl)

        await redis_client.set(
            f"ip:{ip}:blocked",
            "1",
            ex=duration
        )
    
    @staticmethod
    async def block_fingerprint(fingerprint: str, duration: int = 3600):
        max_ttl = 60 * 60 * 12
        duration = min(duration, max_ttl)

        await redis_client.set(f"fp:{fingerprint}:blocked", "1", ex=duration)

    @staticmethod
    async def is_blocked(user_id: int) -> bool:
        return await redis_client.exists(f"user:{user_id}:blocked") == 1

    # ─────────────────────────────────────────────────────────────
    # FEATURE BUILDING
    # ─────────────────────────────────────────────────────────────
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
                val = d.decode() if isinstance(d, bytes) else str(d)
                if "|" in val:
                    endpoints.append(val.split("|", 1)[1])
                else:
                    endpoints.append(val)

            return endpoints

        except Exception as e:
            logger.error(f"get_recent_endpoints failed: {e}")
            return []

    @staticmethod
    async def get_request_timestamps(user_id: int, window: int):
        now = time.time()
        key = f"user:{user_id}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)
        data = await redis_client.zrange(key, 0, -1, withscores=True)

        return [score for _, score in data]

    # ─────────────────────────────────────────────────────────────
    # ERROR TRACKING (TTL ALIGNED WITH WINDOW)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_error_count(user_id: int, window: int):
        val = await redis_client.get(f"user:{user_id}:errors")
        return int(val) if val else 0

    @staticmethod
    async def increment_error(user_id: int):
        key = f"user:{user_id}:errors"
        await redis_client.incr(key)
        await redis_client.expire(key, WINDOW_SIZE)

    # ─────────────────────────────────────────────────────────────
    # IP BEHAVIOR (SESSION-BASED)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_ip_change_count(user_id: int, window: int):
        key = f"user:{user_id}:ips"
        ips = await redis_client.smembers(key)
        return len(ips) if ips else 0

    @staticmethod
    async def track_ip(user_id: int, ip: str):
        key = f"user:{user_id}:ips"
        await redis_client.sadd(key, ip)
        await redis_client.expire(key, 300)

    # ─────────────────────────────────────────────────────────────
    # VIOLATIONS (WINDOW-ALIGNED)
    # ─────────────────────────────────────────────────────────────
    @classmethod
    async def increment_violation(cls, user_id: int):
        key = f"user:{user_id}:violations"
        val = await redis_client.incr(key)
        await redis_client.expire(key, 1800)  # aligned with long window
        return val

    @staticmethod
    async def get_violations(user_id: int):
        val = await redis_client.get(f"user:{user_id}:violations")
        return int(val) if val else 0

    # ─────────────────────────────────────────────────────────────
    # GENERIC HELPERS
    # ─────────────────────────────────────────────────────────────
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
