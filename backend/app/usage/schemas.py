from pydantic import BaseModel
from typing import List


# =========================================
# 📊 METRICS
# =========================================

class UsageMetrics(BaseModel):
    total_requests: int
    avg_rps: float
    unique_ips: int
    success_rate: float


# =========================================
# 📈 TREND
# =========================================

class UsageTrendPoint(BaseModel):
    time: str
    requests: int


# =========================================
# 🎯 ENDPOINT USAGE
# =========================================

class EndpointUsage(BaseModel):
    endpoint: str
    requests: int


# =========================================
# 🚀 FINAL RESPONSE
# =========================================

class UsageResponse(BaseModel):
    metrics: UsageMetrics
    trend: List[UsageTrendPoint]
    endpoints: List[EndpointUsage]