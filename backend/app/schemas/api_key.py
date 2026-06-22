from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Label for the API Key")

class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_preview: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class APIKeyCreateResponse(APIKeyResponse):
    key: str
