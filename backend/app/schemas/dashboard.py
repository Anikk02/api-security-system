from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

class TrafficComposition(BaseModel):
    normal: int
    suspicious: int
    high_risk: int
    critical: Optional[int] = 0

class DashboardStatsResponse(BaseModel):
    # Existing fields
    requests_per_second: float
    requests_trend: float # This is RPS trend(last minute)
    violations_detected: int
    violations_trend: int
    suspicious_sessions: int
    sessions_trend: int
    traffic_composition: dict
    
    # New fields for frontend
    avg_risk_score: float
    risk_trend: float
    avg_latency: str
    latency_trend: float
    active_users_15m: int
    active_users_trend: float
    blocked_trend: float
    throttled_trend: float 
    decisions_last_min: Dict[str, int]  # {allowed: 220, throttled: 15, blocked: 5}
    total_requests_15m: int  # Trend for last 15 min
    total_requests_trend: float # Trend for total requests
    blocked_count_15m: int  # 
    throttled_count_15m: int

class TrafficDataPoint(BaseModel):
    time: datetime
    requests: int
    anomalies: int
    blocked: int

class TrafficResponse(BaseModel):
    data: List[TrafficDataPoint]
    timeframe: str

class SuspiciousUserResponse(BaseModel):
    id: str
    identity_id: str
    violations: int
    threat_score: float
    status: str
    ip: str
    last_seen: datetime
    reason: str
    is_blocked: bool = False

class AlertResponse(BaseModel):
    id: int
    ip: str
    score: float
    type: str
    timestamp: datetime
    identity_id: Optional[str] = None

class LogResponse(BaseModel):
    id: int
    request_uuid: str
    identity_id: Optional[str]
    endpoint: str
    ip_address: str
    action: str
    risk_score: float
    explanation: Dict[str, Any]
    created_at: datetime

class UserDetailsResponse(BaseModel):
    identity_id: str
    client_id: Optional[int] = None
    is_anonymous: bool
    total_requests: int
    violations: int
    current_risk_score: float
    avg_risk_score: float
    is_blocked: bool = False
    recent_actions: List[dict]
    ip_history: List[str]

# Policy-related schemas
class PolicyStats(BaseModel):
    name: str
    trigger_count: int
    percentage: float
    avg_risk_score: float
    allowed: int
    blocked: int
    throttled: int