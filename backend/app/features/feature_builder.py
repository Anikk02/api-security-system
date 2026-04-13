import math
from collections import Counter

class FeatureBuilder:

    def __init__(self, state_manager):
        self.state = state_manager

    async def build_features(self, identity, signals):
        user_id = identity.user_id

        #Basic Rate Features
        req_per_sec = await self.state.get_request_count(user_id, window=1)
        req_per_min = await self.state.get_request_count(user_id, window=60)

        #Endpoint behavior
        endpoints = await self.state.get_recent_endpoints(user_id, window=60)
        unique_endpoints = len(set(endpoints)) if endpoints else 0

        endpoint_entropy = self._calculate_entropy(endpoints)

        #Error Analysis
        error_count = await self.state.get_error_count(user_id, window=60)
        total_requests = max(req_per_min, 1)
        error_rate = error_count / total_requests

        #Burst Detection
        burst_score = req_per_sec / max(req_per_min / 60, 1)

        #IP Behavior
        ip_changes = await self.state.get_ip_change_count(user_id, window=300)

        #User Agent Analysis
        ua = (signals.user_agent or "").lower()

        is_bot = any(bot in ua for bot in ['curl', 'wget','bot','python','scrapy'])
        is_browser = any(b in ua for b in ['mozilla','chrome','safari','edge'])

        #Time pattern features
        request_timestamps = await self.state.get_request_timestamps(user_id, window=60)

        time_variance = self._calculate_time_variance(request_timestamps)

        # GEO/ IP (placeholder)

        ip_address = signals.ip_address

        #Final Feature Set
        features = {
            #rate
            'req_per_sec': req_per_sec,
            'req_per_min': req_per_min,

            #Endpoint behavior
            'unique_endpoints':unique_endpoints,
            'endpoint_entropy': endpoint_entropy,

            #Errors
            'error_rate': error_rate,

            #Burst 
            'burst_score': burst_score,

            #Identity stability
            'ip_changes':ip_changes,

            #Agent
            'is_bot': int(is_bot),
            'is_browser': int(is_browser),

            #Timing
            'time_variance':time_variance,

            #raw
            'ip_address': ip_address,
        }

        return features
    
    #HELPERS
    def _calculate_entropy(self, values):
        '''
        It measures randomness of endpoint access
        High entropy - > diverse behavior
        Low entropy - > repetitive (bot-like)'''

        if not values:
            return 0.0
        
        counter = Counter(values)
        total = len(values)

        entropy = 0.0
        for count in counter.values():
            p = count / total
            entropy -= p*math.log2(p)

        return entropy
    
    def _calculate_time_variance(self, timestamps):
        '''
        It measures regularity of requests
        Low variance - > bot-like fixed intervals
        High variance - > human-like randomness'''

        if not timestamps or len(timestamps) < 2:
            return 0.0
        
        intervals = [
            timestamps[i] - timestamps[i-1]
            for i in range(1, len(timestamps))
        ]

        mean = sum(intervals) / len(intervals)

        variance = sum((x-mean)**2 for x in intervals) / len(intervals)

        return variance