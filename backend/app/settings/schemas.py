from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


#  PROFILE

class ProfileResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    email: EmailStr


class UpdateProfileResponse(BaseModel):
    message: str


#  API KEY

class APIKeyResponse(BaseModel):
    api_key: Optional[str]  # masked key
    created_at: Optional[datetime]


class APIKeyRegenerateResponse(BaseModel):
    api_key: str  # full key (shown once)
    message: str


# SETTINGS OVERVIEW

class APIKeyOverview(BaseModel):
    masked: Optional[str]
    is_active: bool
    created_at: Optional[datetime]


class SettingsOverviewResponse(BaseModel):
    profile: ProfileResponse
    api_key: APIKeyOverview