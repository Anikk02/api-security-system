"""
Pydantic schemas for the Global Logs module.
Maps 1:1 onto app/db/models/request_log.py columns.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class GlobalLogEntry(BaseModel):
    id: int
    request_uuid: Optional[str] = None
    client_id: Optional[int] = None
    identity_id: Optional[str] = None
    api_key_id: Optional[int] = None
    endpoint: str
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    action: Optional[str] = None  # allow | throttle | block
    created_at: datetime

    class Config:
        from_attributes = True


class GlobalLogsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    logs: List[GlobalLogEntry]
