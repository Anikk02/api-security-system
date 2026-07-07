from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# API KEY SCHEMA

class APIKeyResponse(BaseModel):
    api_key: Optional[str] # masked or full (only on regeneration)
    created_at: Optional[datetime]

class APIKeyRegenerateResponse(BaseModel):
    api_key: str
    message: str


# PROFILE SCHEMAS

class ProfileResponse(BaseModel):
    id: int # or UUID
    email: EmailStr
    created_at: datetime

class UpdateProfileRequest(BaseModel):
    email: EmailStr

class UpdateProfileResponse(BaseModel):
    message: str

# PASSWORD SCHEMAS

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    message: str

# SETTINGS OVERVIEW

class APIKeyMeta(BaseModel):
    masked: Optional[str]
    is_active: bool
    created_at: Optional[datetime]

class SettingsOverviewResponse(BaseModel):
    profile: ProfileResponse
    api_key: APIKeyMeta