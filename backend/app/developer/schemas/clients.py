"""
Pydantic schemas for Client Management.
Mirrors app/db/models/clients.py (Client) and app/db/models/api_key.py (APIKey).
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class DeveloperAPIKeyInfo(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeveloperClientInfo(BaseModel):
    id: int
    email: str
    company_name: Optional[str] = None
    role: str
    status: str  # active | inactive | suspended | locked
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    total_requests: int
    api_keys: List[DeveloperAPIKeyInfo]

    class Config:
        from_attributes = True


class DeveloperClientsResponse(BaseModel):
    total: int
    clients: List[DeveloperClientInfo]


class ClientStatusUpdate(BaseModel):
    status: str  # active | inactive | suspended | locked
