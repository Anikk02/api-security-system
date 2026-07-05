"""
Pydantic schemas for Debug Tools.
Pulls together RequestLog + DecisionLog + FeatureLog + MLPrediction —
the same explainability data the Security Engine already produces
(see app/explainability/explainer.py, app/db/models/decision_log.py).
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.developer.schemas.logs import GlobalLogEntry


class DebugRequestInfo(BaseModel):
    request_log: GlobalLogEntry
    decision: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    ml_prediction: Optional[Dict[str, Any]] = None


class RecentDecision(BaseModel):
    id: int
    action: str
    risk_score: Optional[float] = None
    created_at: datetime


class DebugIdentitySummary(BaseModel):
    identity_id: str
    client_id: Optional[int] = None
    total_requests: int
    blocked_count: int
    throttled_count: int
    allowed_count: int
    is_blocked: bool
    recent_decisions: List[RecentDecision]
