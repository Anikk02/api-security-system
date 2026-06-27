import time
import json
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

    # ✅ NEW: unified key builder
    @staticmethod
    def _base(client_id: int | None, identity_id: str) -> str:
        return f"client:{client_id}:identity:{identity_id}"

    # ─────────────────────────────────────────────────────────────
    # FAST DECISION PATH (aligned with identity model)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_decision_signals(identity, fingerprint: str = None):
        client_id = identity.client_id
        identity_id = identity.identity_id
        ip = identity.ip_address

        base = StateManager._base(client_id, identity_id)

        pipe = redis_client.pipeline()

        pipe.exists(f"{base}:blocked")
        pipe.get(f"{base}:risk_score")
        pipe.exists(f"{base}:throttled")

        # IP Block
        if ip:
            pipe.exists(f"ip:{ip}:blocked")

        # Fingerprint Block
        if fingerprint:
            pipe.exists(f"fp:{fingerprint}:blocked")
            pipe.get(f"rep:fp:{fingerprint}")

        try:
            results = await pipe.execute()

            blocked = bool(results[0])
            risk_raw = results[1]
            throttled = bool(results[2])

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
                    raw = results[idx]
                    idx += 1

                    if raw:
                        try:
                            val = raw.decode() if isinstance(raw, bytes) else raw
                            fp_rep = float(val)
                        except:
                            fp_rep = 0.0

            blocked = blocked or ip_blocked or fp_blocked

            risk_score = 0.0
            if risk_raw is not None:
                try:
                    val = risk_raw.decode() if isinstance(risk_raw, bytes) else risk_raw
                    risk_score = float(val)
                except:
                    risk_score = 0.0

            risk_score = min(1.0, risk_score + (fp_rep * 0.2))

            return blocked, risk_score, throttled

        except Exception as e:
            logger.error(f"get_decision_signals pipeline failed: {e}")
            return False, 0.0, False

    # ─────────────────────────────────────────────────────────────
    # REQUEST TRACKING (aligned keys)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def track_request_async(identity, endpoint: str, status_code: int | None):
        ts = time.time()

        client_id = identity.client_id
        identity_id = identity.identity_id
        ip = identity.ip_address

        base = StateManager._base(client_id, identity_id)

        pipe = redis_client.pipeline()

        key_ts = f"{base}:timestamps"
        key_ep = f"{base}:endpoints"
        key_ip = f"{base}:ips"
        key_err = f"{base}:errors"

        pipe.zadd(key_ts, {str(ts): ts})
        pipe.zremrangebyscore(key_ts, 0, ts - 300)
        pipe.expire(key_ts, 300)

        pipe.zadd(key_ep, {f"{ts}|{endpoint}": ts})
        pipe.zremrangebyscore(key_ep, 0, ts - 300)
        pipe.expire(key_ep, 300)

        pipe.sadd(key_ip, ip)
        pipe.expire(key_ip, 300)

        if status_code is not None and status_code >= 400:
            pipe.incr(key_err)
            pipe.expire(key_err, 300)

        # ---- CLIENT-LEVEL ANALYTICS ---- #
        client_stats_key = f"client:{client_id}:stats"
        client_endpoints_key = f"client:{client_id}:endpoints"
        client_trend_key = f"client:{client_id}:trend"

        # -- total requests --
        pipe.hincrby(client_stats_key, "total", 1)

        # --- allowed / blocked ---
        is_blocked = False

        if status_code is not None:
            if status_code >= 400:
                pipe.hincrby(client_stats_key, "blocked", 1)
                is_blocked = True
            else:
                pipe.hincrby(client_stats_key, "allowed", 1)
        
        # --- endpoint tracking ---
        if endpoint:
            pipe.zincrby(client_endpoints_key, 1, endpoint)
        
        # --- trend tracking (time-series) ---
        trend_point = {
            "time": str(int(ts)),
            "allowed": 1 if status_code and status_code < 400 else 0,
            "blocked": 1 if status_code and status_code >= 400 else 0,
            "throttled":0 # to be extended later
        }

        pipe.lpush(client_trend_key, json.dumps(trend_point))
        pipe.ltrim(client_trend_key, 0, 50)

        # PEAK TRACKING 

        if is_blocked:
            peak_blocked_key = f"{client_stats_key}:peak_blocked"

            # increment current blocked window counter
            pipe.incr(peak_blocked_key)
            pipe.expire(peak_blocked_key, 60)

            # store snapshot reference
            pipe.hset(client_stats_key, "peak_time", str(int(ts)))
            pipe.hset(client_stats_key, "peak_endpoint", endpoint or "unknown")


        try:
            await pipe.execute()
        except Exception as e:
            logger.error(f"track_request_async pipeline failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # RATE LIMITING
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_request_count(identity, window: int):
        now = time.time()

        base = StateManager._base(identity.client_id, identity.identity_id)
        key = f"{base}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)

        result = await safe_redis_call(
            redis_client.zcount(key, now - window, now)
        )

        return result or 0

    @staticmethod
    async def is_rate_limited(identity) -> bool:
        count = await StateManager.get_request_count(identity, WINDOW_SIZE)
        return count > MAX_REQUESTS

    # ─────────────────────────────────────────────────────────────
    # BLOCK MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def block_identity(identity, duration: int = 3600):
        max_ttl = 60 * 60 * 12
        duration = min(duration, max_ttl)

        base = StateManager._base(identity.client_id, identity.identity_id)

        await redis_client.set(f"{base}:blocked", "1", ex=duration)

    @staticmethod
    async def block_ip(ip: str, duration: int = 3600):
        duration = min(duration, 60 * 60 * 12)
        await redis_client.set(f"ip:{ip}:blocked", "1", ex=duration)

    @staticmethod
    async def block_fingerprint(fingerprint: str, duration: int = 3600):
        duration = min(duration, 60 * 60 * 12)
        await redis_client.set(f"fp:{fingerprint}:blocked", "1", ex=duration)

    # ─────────────────────────────────────────────────────────────
    # FEATURE HELPERS (aligned with FeatureBuilder)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def get_recent_endpoints(identity, window: int):
        now = time.time()
        base = StateManager._base(identity.client_id, identity.identity_id)
        key = f"{base}:endpoints"

        await redis_client.zremrangebyscore(key, 0, now - window)
        data = await redis_client.zrange(key, 0, -1)

        endpoints = []
        for d in data or []:
            val = d.decode() if isinstance(d, bytes) else str(d)
            if "|" in val:
                endpoints.append(val.split("|", 1)[1])
            else:
                endpoints.append(val)

        return endpoints

    @staticmethod
    async def get_request_timestamps(identity, window: int):
        now = time.time()
        base = StateManager._base(identity.client_id, identity.identity_id)
        key = f"{base}:timestamps"

        await redis_client.zremrangebyscore(key, 0, now - window)
        data = await redis_client.zrange(key, 0, -1, withscores=True)

        return [score for _, score in data]

    # ─────────────────────────────────────────────────────────────
    # ERROR TRACKING
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def get_error_count(identity):
        base = StateManager._base(identity.client_id, identity.identity_id)
        val = await redis_client.get(f"{base}:errors")
        return int(val) if val else 0
    
    
    @staticmethod
    async def increment_error(identity):
        base = StateManager._base(identity.client_id, identity.identity_id)
        key = f"{base}:errors"

        await redis_client.incr(key)
        await redis_client.expire(key, WINDOW_SIZE)

    # ─────────────────────────────────────────────────────────────
    # IP BEHAVIOR (SESSION-BASED)
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def get_ip_change_count(identity):
        base = StateManager._base(identity.client_id, identity.identity_id)
        key = f"{base}:ips"
        ips = await redis_client.smembers(key)
        return len(ips) if ips else 0
    
    @staticmethod
    async def track_ip(identity, ip: str):
        base = StateManager._base(identity.client_id, identity.identity_id)
        key = f"{base}:ips"

        await redis_client.sadd(key, ip)
        await redis_client.expire(key, 300)
    
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
    # BLOCK CHECK
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    async def is_blocked(identity) -> bool:
        base = StateManager._base(identity.client_id, identity.identity_id)
        return await redis_client.exists(f"{base}:blocked") == 1
    
    # ─────────────────────────────────────────────────────────────
    # VIOLATIONS (WINDOW-ALIGNED)
    # ─────────────────────────────────────────────────────────────
    @classmethod
    async def increment_violation(cls, identity):
        base = cls._base(identity.client_id, identity.identity_id)
        key = f"{base}:violations"

        val = await redis_client.incr(key)
        await redis_client.expire(key, 1800)  # same TTL

        return val

    @staticmethod
    async def get_violations(identity):
        base = StateManager._base(identity.client_id, identity.identity_id)
        val = await redis_client.get(f"{base}:violations")

        return int(val) if val else 0