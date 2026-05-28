from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class DashboardStatsResponse(BaseModel):
    requests_per_second: float
    requests_trend: float
    violations_detected: int
    violations_trend: int
    suspicious_sessions: int
    sessions_trend: int
    traffic_composition: dict

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
    violations: int
    threat_score: float
    status: str
    ip: str
    last_seen: datetime

class AlertResponse(BaseModel):
    id: int
    ip: str
    score: float
    type: str
    timestamp: datetime
    user_id: Optional[str] = None

class LogResponse(BaseModel):
    id: int
    request_uuid: str
    user_id: Optional[int]
    endpoint: str
    ip_address: str
    action: str
    risk_score: float
    explanation: str
    created_at: datetime

class UserDetailsResponse(BaseModel):
    user_id: int
    is_anonymous: bool
    total_requests: int
    violations: int
    current_risk_score: float
    recent_actions: List[dict]
    ip_history: List[str]
