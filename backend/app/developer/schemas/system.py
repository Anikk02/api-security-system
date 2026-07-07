"""
Pydantic schema for System Health.
"""
from pydantic import BaseModel
from typing import Optional


class SystemHealthResponse(BaseModel):
    db_status: str          # healthy | down
    redis_status: str       # healthy | down
    avg_latency_ms: Optional[float] = None
    error_rate_pct: float
    total_requests_today: int
    blocked_today: int
    throttled_today: int
    allowed_today: int
