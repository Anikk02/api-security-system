from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_client
from app.db.session import get_db

from app.usage import service as usage_service
from app.usage.schemas import UsageResponse

router = APIRouter(
    prefix="/api/usage",
    tags=["Usage"]
)

@router.get("/", response_model=UsageResponse)
async def get_usage(
    client=Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    return await usage_service.get_usage_data(db, client.id)
