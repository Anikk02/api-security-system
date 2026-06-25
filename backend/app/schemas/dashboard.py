from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

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
    identity_id: str  # was missing entirely; route was passing it in and Pydantic silently dropped it
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
    identity_id: Optional[str] = None  # renamed from user_id (was already str-typed, just misnamed)

class LogResponse(BaseModel):
    id: int
    request_uuid: str
    identity_id: Optional[str]  # renamed from user_id; was Optional[int] but identity_id is a string
    endpoint: str
    ip_address: str
    action: str
    risk_score: float
    explanation: Dict[str, Any]
    created_at: datetime

class UserDetailsResponse(BaseModel):
    identity_id: str  # renamed from user_id: int
    client_id: Optional[int] = None  # was missing; route returns this
    is_anonymous: bool
    total_requests: int
    violations: int
    current_risk_score: float
    avg_risk_score: float  # was missing; route returns this
    is_blocked: bool = False  # was missing; route returns this
    recent_actions: List[dict]
    ip_history: List[str]