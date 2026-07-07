import time
import json
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from app.state.redis_client import redis_client
from app.activity.schemas import SpikeCorrelation

def compute_risk(blocked: int, total: int):
    if total == 0:
        return "LOW", 0.0
    
    percent = (blocked / total) * 100
    
    if percent < 30:
        return "LOW", percent
    elif percent < 60:
        return "MEDIUM", percent
    return "HIGH", percent

def compute_health(allowed: int, blocked: int):
    total = allowed + blocked
    if total == 0:
        return "HEALTHY", 100.0
    
    score = (allowed / total) * 100
    
    if score > 80:
        status = "HEALTHY"
    elif score > 50:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    return status, score

def compute_severity(blocked: int):
    if blocked > 100:
        return "SEVERE"
    elif blocked > 50:
        return "HIGH"
    elif blocked > 20:
        return "MEDIUM"
    return "LOW"

async def detect_spike_correlations(client_id: int, time_window: int = 600) -> List[SpikeCorrelation]:
    """
    Detect and correlate traffic spikes with endpoint targeting
    Optimized for 10-minute windows
    """
    correlations = []
    
    try:
        # Get minute-by-minute data for the last 10 minutes
        minute_data = await get_minute_aggregates(client_id, time_window)
        
        if not minute_data:
            return correlations
        
        # Calculate baseline (average traffic)
        all_requests = [m.get('total', 0) for m in minute_data if m.get('total', 0) > 0]
        
        if not all_requests:
            return correlations
            
        avg_traffic = sum(all_requests) / len(all_requests)
        
        # Detect spikes (> 2x average)
        for minute in minute_data:
            total = minute.get('total', 0)
            
            if total > avg_traffic * 2 and total > 20:  # Minimum threshold
                # Find top endpoint in this minute
                endpoints = minute.get('endpoints', {})
                if endpoints:
                    top_endpoint = max(endpoints.items(), key=lambda x: x[1].get('requests', 0))
                    
                    correlations.append(
                        SpikeCorrelation(
                            peak_time=minute.get('timestamp', ''),
                            blocked=top_endpoint[1].get('blocked', 0),
                            target=top_endpoint[0],
                        )
                    )
        
        # Sort by blocked count (most severe first)
        correlations.sort(key=lambda x: x.blocked, reverse=True)
        
        # Limit to top 5 correlations
        return correlations[:5]
        
    except Exception as e:
        # Return empty list on error
        return []

async def get_minute_aggregates(client_id: int, time_window: int = 600) -> List[Dict]:
    """
    Get per-minute aggregates for the specified time window
    """
    now = time.time()
    start_time = now - time_window
    
    # Get trend data from Redis
    trend_key = f"client:{client_id}:trend"
    raw_trend = await redis_client.lrange(trend_key, 0, 50)
    
    if not raw_trend:
        return []
    
    # Group by minute
    minute_buckets = defaultdict(lambda: {'total': 0, 'endpoints': defaultdict(lambda: {'requests': 0, 'blocked': 0})})
    
    for item in raw_trend:
        try:
            data = json.loads(item) if isinstance(item, str) else json.loads(item.decode())
            
            # Parse timestamp
            ts = int(data.get('time', 0))
            minute_key = int(ts / 60) * 60  # Round down to minute
            
            # Add to bucket
            minute_buckets[minute_key]['total'] += 1
            
            # Track endpoints (would need endpoint data in trend)
            # This is a simplification; actual implementation would need endpoint info
            
        except Exception:
            continue
    
    # Convert to list and format
    result = []
    for minute_ts, data in minute_buckets.items():
        result.append({
            'timestamp': datetime.fromtimestamp(minute_ts).strftime('%H:%M'),
            'total': data['total'],
            'endpoints': dict(data['endpoints'])
        })
    
    # Sort by timestamp
    result.sort(key=lambda x: x['timestamp'])
    
    return result

async def get_hourly_patterns(client_id: int) -> Dict[str, float]:
    """
    Get attack patterns across endpoints for the last hour
    """
    patterns = {}
    
    try:
        # Get endpoint data from Redis
        endpoints_key = f"client:{client_id}:endpoints"
        endpoint_data = await redis_client.zrevrange(endpoints_key, 0, 10, withscores=True)
        
        if endpoint_data:
            total = sum(int(score) for _, score in endpoint_data)
            
            for ep, score in endpoint_data:
                ep_name = ep.decode() if isinstance(ep, bytes) else ep
                count = int(score)
                percentage = (count / total * 100) if total else 0
                patterns[ep_name] = round(percentage, 2)
    
    except Exception:
        pass
    
    return patterns