from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from app.db.session import get_db
from app.db.models.api_key import APIKey
from app.db.models.client import Client
from app.authentication.dependencies import require_active_client
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyCreateResponse
from typing import List

router = APIRouter(prefix="/api/client/keys", tags=["API Keys"])

@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_client: Client = Depends(require_active_client),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_client.id).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    
    response = []
    for k in keys:
        preview = f"{k.key[:8]}...{k.key[-4:]}" if len(k.key) > 12 else k.key
        response.append(
            APIKeyResponse(
                id=k.id,
                name=k.name,
                key_preview=preview,
                is_active=k.is_active,
                created_at=k.created_at,
                last_used_at=k.last_used_at
            )
        )
    return response

@router.post("", response_model=APIKeyCreateResponse)
async def generate_api_key(
    payload: APIKeyCreate,
    current_client: Client = Depends(require_active_client),
    db: AsyncSession = Depends(get_db)
):
    raw_key = f"ts_live_{secrets.token_hex(24)}"
    
    new_key = APIKey(
        key=raw_key,
        user_id=current_client.id,
        name=payload.name,
        is_active=True
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    preview = f"{raw_key[:8]}...{raw_key[-4:]}"
    return APIKeyCreateResponse(
        id=new_key.id,
        name=new_key.name,
        key_preview=preview,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        last_used_at=None,
        key=raw_key
    )

@router.put("/{key_id}/status", response_model=APIKeyResponse)
async def update_key_status(
    key_id: int,
    payload: APIKeyUpdate,
    current_client: Client = Depends(require_active_client),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_client.id)
    )
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    if payload.is_active is not None:
        key_obj.is_active = payload.is_active
    if payload.name is not None:
        key_obj.name = payload.name
        
    await db.commit()
    await db.refresh(key_obj)
    
    preview = f"{key_obj.key[:8]}...{key_obj.key[-4:]}" if len(key_obj.key) > 12 else key_obj.key
    return APIKeyResponse(
        id=key_obj.id,
        name=key_obj.name,
        key_preview=preview,
        is_active=key_obj.is_active,
        created_at=key_obj.created_at,
        last_used_at=key_obj.last_used_at
    )

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_client: Client = Depends(require_active_client),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_client.id)
    )
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    await db.delete(key_obj)
    await db.commit()
    return None
