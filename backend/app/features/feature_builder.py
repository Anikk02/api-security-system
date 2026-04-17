import math
from collections import Counter

class FeatureBuilder:

    def __init__(self, state_manager):
        self.state = state_manager

    async def build(self, identity, signals):
        user_id = identity.user_id

        # BASIC RATE FEATURES
        req_per_5sec = await self.state.get_request_count(user_id, window=5)
        req_per_sec = req_per_5sec / 5
        req_per_min = await self.state.get_request_count(user_id, window=60)

        print("DEBUG -> req/sec:", req_per_sec)
        print("DEBUG -> req/min:", req_per_min)

        # ENDPOINT BEHAVIOR
        endpoints = await self.state.get_recent_endpoints(user_id, window=60)
        if not isinstance(endpoints, list):
            endpoints = []
        unique_endpoints = len(set(endpoints)) if endpoints else 0

        endpoint_entropy = self._calculate_entropy(endpoints)

        # Normalize entropy (0–1)
        max_entropy = math.log2(len(set(endpoints))) if endpoints and len(set(endpoints)) > 1 else 1
        endpoint_entropy = endpoint_entropy / max_entropy if max_entropy > 0 else 0.0

        # ERROR ANALYSIS
        error_count = await self.state.get_error_count(user_id, window=60)
        total_requests = max(req_per_min, 1)

        error_rate = (error_count + 1) / (total_requests + 5)

        # BURST DETECTION
        avg_per_sec = req_per_min / 60 if req_per_min > 0 else 0

        # Proper burst ratio
        if avg_per_sec > 0:
            burst_score = req_per_sec / avg_per_sec
        else:
            burst_score = 0.0

        # Normalize burst_score
        burst_score = math.log1p(burst_score) / math.log1p(10) # scale factor (tunable)

        # IP BEHAVIOR
        ip_changes = await self.state.get_ip_change_count(user_id, window=300)

        # USER AGENT ANALYSIS
        ua = (signals.user_agent or "").lower()

        is_bot = any(bot in ua for bot in ['curl', 'wget', 'bot', 'python', 'scrapy'])
        is_browser = any(b in ua for b in ['mozilla', 'chrome', 'safari', 'edge'])

        # TIME PATTERN FEATURES
        request_timestamps = await self.state.get_request_timestamps(user_id, window=60)

        #request regularity score
        intervals = []
        if len(request_timestamps) > 2:
            intervals = [
                request_timestamps[i] - request_timestamps[i-1]
                for i in range(1, len(request_timestamps))
            ]
            min_i, max_i = min(intervals), max(intervals)
            regularity = 1 - (min_i / max_i if max_i > 0 else 0)
        else:
            regularity = 0

        print("DeBUG -> user:", user_id)
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