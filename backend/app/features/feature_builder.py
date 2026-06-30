import math
import time
import asyncio
from collections import Counter
from app.state.redis_client import redis_client

# Theoretical max entropy based on expected endpoint space(tunable)
MAX_ENDPOINT_ENTROPY = math.log2(50)

# Minimum baseline req/sec before burst ratio is meaningful
BURST_BASELINE_THRESHOLD = 0.1

# Sensitive endpoint definitions (matching risk_engine.py)
_SENSITIVE_EXACT = {
    "/login", "/auth", "/admin", "/payment", "/reset-password",
    "/api/data", "/api/secure",
}

_SENSITIVE_PREFIXES = (
    "/api/admin",
    "/api/user",
    "/api/secure",
    "/api/data",
)

class FeatureBuilder:

    def __init__(self, state_manager):
        self.state = state_manager

    async def build(self, identity, signals):
        # 🔥 UPDATED: use identity_id + client_id instead of user_id
        identity_id = identity.identity_id
        client_id = identity.client_id

        # 🔥 UPDATED: namespaced Redis key
        base_key = f"client:{client_id}:identity:{identity_id}"

        now = time.time()

        # SINGLE PIPELINE for all Redis reads
        pipe = redis_client.pipeline()

        # Request count (5 seconds)
        ts_key = f"{base_key}:timestamps"
        pipe.zcount(ts_key, now -5, now)

        # Request count (60 seconds)
        pipe.zcount(ts_key, now - 60, now)

        # Recent endpoints (60 seconds)
        endpoint_key = f"{base_key}:endpoints"
        pipe.zrangebyscore(endpoint_key, now - 60, now)

        # Error count (60 seconds)
        error_key = f"{base_key}:errors"
        pipe.get(error_key)

        # Request timestamps
        pipe.zrangebyscore(ts_key, now - 60, now, withscores=True)

        # IP changes (300 seconds)
        ip_key = f"{base_key}:ips"
        pipe.smembers(ip_key)

        #Execute all reads in one Redis call
        results = await pipe.execute()

        # Parse results with proper type conversion
        def to_int(value, default=0):
            if value is None:
                return default
            if isinstance(value, bytes):
                return int(value.decode())
            if isinstance(value, str):
                return int(value)
            if isinstance(value, (int, float)):
                return int(value)
            return default
        
        def to_float(value, default=0.0):
            if value is None:
                return default
            if isinstance(value, bytes):
                return float(value.decode())
            if isinstance(value, str):
                return float(value)
            if isinstance(value, (int, float)):
                return float(value)
            return default
        
        # Convert results
        req_per_5sec_raw = to_int(results[0])
        req_per_min = to_int(results[1])
        endpoints_raw = results[2] or []
        error_count_raw = to_int(results[3])
        timestamps_raw = results[4] or []
        ip_set = results[5] or set()

        # Parse endpoints (extract from ZSET values)
        endpoints = []
        for item in endpoints_raw:
            val = item.decode() if isinstance(item, bytes) else str(item)
            if "|" in val:
                endpoints.append(val.split("|", 1)[1])
            else:
                endpoints.append(val)
        
        # Parse timestamps
        request_timestamps = []
        for item in timestamps_raw:
            if isinstance(item, tuple) and len(item) ==2:
                request_timestamps.append(float(item[1]))
            elif isinstance(item, (int, float)):
                request_timestamps.append(float(item))
            elif isinstance(item, bytes):
                try:
                    request_timestamps.append(float(item.decode()))
                except:
                    pass
        
        ip_changes = len(ip_set) if ip_set else 0

        # BASIC RATE FEATURES
        req_per_sec = (req_per_5sec_raw or 0) / 5

        #Print occassionally to avoid log spam
        if hash(identity_id) % 100 == 0: #sample 1% of requests
            print("DEBUG -> req/sec:", req_per_sec)
            print("DEBUG -> req/min:", req_per_min)

        # ENDPOINT BEHAVIOR
        if not isinstance(endpoints, list):
            endpoints = []
        unique_endpoints = len(set(endpoints)) if endpoints else 0
        
        #Normalize against a fixed theoretical max, not the data's own max.
        raw_entropy = self._calculate_entropy(endpoints)
        endpoint_entropy = round(min(raw_entropy / MAX_ENDPOINT_ENTROPY, 1.0), 4)

        counter = Counter(endpoints)
        total = len(endpoints)
        
        # Require a minimum sample before trusting top_endpoint_ratio.
        # With < 10 requests any user trivially scores 1.0 (they hit one
        # endpoint once), making normal users look like endpoint-hammers.
        if total >= 10:
            top_count = max(counter.values())
            top_endpoint_ratio = round(top_count / total, 4)
        else:
            top_endpoint_ratio = 0.0

        # NEW: Count sensitive endpoint hits
        sensitive_hits = 0
        for endpoint in endpoints:
            if endpoint in _SENSITIVE_EXACT:
                sensitive_hits += 1
            else:
                for prefix in _SENSITIVE_PREFIXES:
                    if endpoint == prefix or endpoint.startswith(prefix + "/") or endpoint.startswith(prefix + "?"):
                        sensitive_hits += 1
                        break

        # ERROR ANALYSIS
        error_count = error_count_raw or 0
        total_requests = max(req_per_min, 1)

        error_rate = round(error_count / total_requests, 4)

        # BURST DETECTION
        avg_per_sec = req_per_min / 60 if req_per_min > 0 else 0

        # Proper burst ratio
        if avg_per_sec > BURST_BASELINE_THRESHOLD: # 0 -> 0.1
            burst_score = req_per_sec / avg_per_sec
        else:
            burst_score = 0.0

        # Normalize burst_score
        burst_score = round(math.log1p(burst_score) / math.log1p(10), 4) # scale factor (tunable)

        # USER AGENT ANALYSIS
        ua = (signals.user_agent or "").lower()

        is_bot = any(bot in ua for bot in ['curl', 'wget', 'bot', 'python', 'scrapy'])
        is_browser = any(b in ua for b in ['mozilla', 'chrome', 'safari', 'edge'])

        #request regularity score
        intervals = []
        if len(request_timestamps) >= 6: # need atleast 5 intervals
            intervals = [
                request_timestamps[i] - request_timestamps[i-1]
                for i in range(1, len(request_timestamps))
            ]
            
            if intervals:
                mean_i = sum(intervals) / len(intervals)

                if mean_i > 0:
                    # Clip extreme outliers (prevent distortion)
                    clipped = [min(i, 5 * mean_i) for i in intervals]

                    variance = sum((x - mean_i) **2 for x in clipped) / len(clipped)
                    std_dev = variance ** 0.5

                    # Coefficient of variation (scale-independent)
                    cv = std_dev / mean_i

                    #Final regularity score
                    regularity = 1 / (1 + cv)
                else:
                    regularity = 0.0
            else:
                regularity = 0.0
        else:
            regularity = 0.0

        # Only print occassionally
        if hash(identity_id) % 100 == 0:
            print("DeBUG -> user:", identity_id)
            print("DEBUG -> timestamps:", request_timestamps)

        time_variance = self._calculate_time_variance(request_timestamps)

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = 0

        # Normalize time variance (bounded)
        time_variance = min(time_variance, 1.0)

        # GEO/IP (placeholder)
        ip_address = signals.ip_address

        # FINAL FEATURE SET
        features = {
            # rate
            'req_per_sec': req_per_sec,
            'req_per_min': req_per_min,

            # endpoint behavior
            'unique_endpoints': unique_endpoints,
            'endpoint_entropy': round(endpoint_entropy, 4),
            'top_endpoint_ratio': top_endpoint_ratio,

            # NEW: sensitive hits count
            'sensitive_hits': sensitive_hits,

            # errors
            'error_rate': round(error_rate, 4),

            # burst
            'burst_score': round(burst_score, 4),

            # flags (now consistent)
            'is_rate_limited': int(req_per_min > 100),
            'is_burst': int(burst_score > 0.6),
            'is_suspicious_ua': int(is_bot and not is_browser),

            # identity stability
            'ip_changes': ip_changes,

            #request regularity score
            'request_regularity': round(regularity,4),

            # agent
            'is_bot': int(is_bot),
            'is_browser': int(is_browser),

            # timing
            'time_variance': round(time_variance, 6),

            #avg interval
            'time_mean': round(avg_interval,4),

            # raw
            'ip_address': ip_address,
        }

        return features

    # HELPERS
    def _calculate_entropy(self, values):
        if not values or not isinstance(values, list):
            return 0.0

        counter = Counter(values)
        total = len(values)

        entropy = 0.0
        for count in counter.values():
            p = count / total
            entropy -= p * math.log2(p)

        return entropy

    def _calculate_time_variance(self, timestamps):
        if not timestamps or len(timestamps) < 2:
            return 0.0

        intervals = [
            timestamps[i] - timestamps[i - 1]
            for i in range(1, len(timestamps))
        ]

        mean = sum(intervals) / len(intervals)
        if mean == 0:
            return 0.0
        
        #normalize interval
        normalized = [i / mean for i in intervals]

        variance = sum((x - 1) ** 2 for x in normalized) / len(normalized)

        return min(variance, 1.0)