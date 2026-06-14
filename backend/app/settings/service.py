from fastapi import APIRouter, Depends

from core.auth import get_current_client
from db.session import get_db

from settings import service as settings_service
from settings.schemas import (
    SettingsOverviewResponse,
    APIKeyResponse,
    APIKeyRegenerateResponse,
    ProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse
)

router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"]
)

#  OVERVIEW

@router.get("/overview", response_model=SettingsOverviewResponse)
async def get_overview(
    client=Depends(get_current_client),
    db=Depends(get_db)
):
    return await settings_service.get_settings_overview(db, client.id)


#  API KEY

@router.get("/api-key", response_model=APIKeyResponse)
async def get_api_key(
    client=Depends(get_current_client),
    db=Depends(get_db)
):
    return await settings_service.get_api_key(db, client.id)


@router.post("/api-key/regenerate", response_model=APIKeyRegenerateResponse)
async def regenerate_api_key(
    client=Depends(get_current_client),
    db=Depends(get_db)
):
    return await settings_service.regenerate_api_key(db, client.id)


#  PROFILE

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    client=Depends(get_current_client),
    db=Depends(get_db)
):
    return await settings_service.get_profile(db, client.id)


@router.put("/profile", response_model=UpdateProfileResponse)
async def update_profile(
    data: UpdateProfileRequest,
    client=Depends(get_current_client),
    db=Depends(get_db)
):
    return await settings_service.update_profile(
        db,
        client.id,
        data.email
    )