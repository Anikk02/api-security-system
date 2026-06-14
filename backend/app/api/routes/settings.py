from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_client
from db.session import get_db

from settings import service as settings_service
from settings.schemas import (
    SettingsOverviewResponse,
    APIKeyRegenerateResponse,
    UpdateProfileRequest,
    UpdateProfileResponse
)

router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"]
)

# =========================================
# ⚙️ OVERVIEW (MAIN DATA SOURCE)
# =========================================

@router.get("/overview", response_model=SettingsOverviewResponse)
async def get_overview(
    client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    return await settings_service.get_settings_overview(db=db, client_id=client.id)


# =========================================
# 🔑 API KEY
# =========================================

@router.post("/api-key/regenerate", response_model=APIKeyRegenerateResponse)
async def regenerate_api_key(
    client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    return await settings_service.regenerate_api_key(db=db, client_id=client.id)


# =========================================
# 👤 PROFILE
# =========================================

@router.put("/profile", response_model=UpdateProfileResponse)
async def update_profile(
    data: UpdateProfileRequest,
    client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    return await settings_service.update_profile(
        db=db,
        client_id=client.id,
        email=data.email
    )