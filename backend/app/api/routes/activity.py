import logging
from fastapi import APIRouter, Depends, Query

from app.activity.schemas import ActivityResponse
from app.activity.service import ActivityService
from app.authentication.dependencies import require_active_client
from app.db.models.client import Client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Activity Intelligence"]
)


@router.get("/activity", response_model=ActivityResponse)
async def get_activity_intelligence(
    current_client: Client = Depends(require_active_client),
    window: int = Query(600, description="Time window in seconds"),
):
    """
    📊 Activity Intelligence Dashboard
    """
    return await ActivityService.get_activity(current_client.id, window)


@router.get("/activity/refresh-interval")
async def get_activity_refresh_interval():
    return {
        "interval": 600,
        "unit": "seconds",
        "human_readable": "10 minutes"
    }