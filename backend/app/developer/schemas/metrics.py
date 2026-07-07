"""
Pydantic schemas for Overview Dashboard, Traffic Analytics, and Abuse Monitoring.
Field shapes follow this project's existing schema style (see app/schemas/dashboard.py).
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# ── Overview ──────────────────────────────────────────────────────────────────

class TopConsumer(BaseModel):
    client_id: int
    email: Optional[str] = None
    company_name: Optional[str] = None
    request_count: int


class ThroughputPoint(BaseModel):
    time: datetime
    requests: int


class OverviewResponse(BaseModel):
    total_requests_all_time: int
    total_requests_today: int
    active_clients: int
    total_clients: int
    top_consumers: List[TopConsumer]
    throughput_last_24h: List[ThroughputPoint]


# ── Traffic Analytics ─────────────────────────────────────────────────────────

class EndpointCount(BaseModel):
    endpoint: str
    count: int


class ClientCount(BaseModel):
    client_id: int
    email: Optional[str] = None
    count: int


class TrendPoint(BaseModel):
    day: datetime
    count: int


class TrafficResponse(BaseModel):
    requests_by_endpoint: List[EndpointCount]
    requests_by_client: List[ClientCount]
    traffic_trend_7d: List[TrendPoint]
    load_distribution: List[EndpointCount]


# ── Abuse Monitoring ──────────────────────────────────────────────────────────

class AbusiveClient(BaseModel):
    client_id: int
    email: Optional[str] = None
    blocked_count: int


class BlockedIP(BaseModel):
    ip_address: str
    blocked_count: int


class HighFreqSource(BaseModel):
    identity_id: str
    client_id: Optional[int] = None
    total_requests: int


class EndpointAbuse(BaseModel):
    endpoint: str
    blocked_count: int


class AbuseResponse(BaseModel):
    top_abusive_clients: List[AbusiveClient]
    most_blocked_ips: List[BlockedIP]
    high_freq_sources: List[HighFreqSource]
    endpoint_abuse_patterns: List[EndpointAbuse]
