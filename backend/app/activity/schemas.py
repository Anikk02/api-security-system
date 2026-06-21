from pydantic import BaseModel
from typing import List, Optional


class ThreatEvent(BaseModel):
    time: str
    event: str
    description: str
    severity: str
    ip: Optional[str]


class DecisionTrendPoint(BaseModel):
    time: str
    allowed: int
    throttled: int
    blocked: int


class EndpointActivity(BaseModel):
    endpoint: str
    percentage: float
    requests: int
    blocked: int
    risk: str


class ActivityInsights(BaseModel):
    attackStatus: str
    anomalyScore: float
    riskLevel: str


class ActivityMetrics(BaseModel):
    totalRequests: int
    blockedRequests: int
    throttledRequests: int
    successRate: float


class PeakAttack(BaseModel):
    time: Optional[str]
    blocked: int
    endpoint: Optional[str]


class ActivityResponse(BaseModel):
    timeline: List[ThreatEvent]
    endpoints: List[EndpointActivity]
    trend: List[DecisionTrendPoint]

    insights: ActivityInsights
    metrics: ActivityMetrics
    peak: PeakAttack

    patterns: List[dict]
    correlations: List[dict]