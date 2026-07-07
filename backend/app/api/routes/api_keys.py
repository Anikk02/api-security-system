from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import hashlib

from app.db.session import get_db
from app.db.models.api_key import APIKey
from app.db.models.client import Client
from app.authentication.dependencies import require_active_client
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyCreateResponse
from typing import List

router = APIRouter(prefix="/api/client/keys", tags=["API Keys"])

def hash_api_key(raw_key: str) -> str:
    """Hash an API key using SHA-256"""
    return hashlib.sha256(raw_key.encode()).hexdigest()

@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_client: Client = Depends(require_active_client),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(APIKey.client_id == current_client.id).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    
    response = []
    for k in keys:
        # We don't have the raw key, only the hash, so we can't show a preview
        # Instead, show the key ID or a placeholder
        preview = f"key_{k.id}_{k.created_at.strftime('%Y%m%d')}"
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
    # Generate raw API key
    raw_key = f"ts_live_{secrets.token_hex(24)}"
    
    # Hash the key before storing
    hashed_key = hash_api_key(raw_key)
    
    new_key = APIKey(
        key_hash=hashed_key,  # Store the hash, not the raw key
        client_id=current_client.id,
        name=payload.name,
        is_active=True
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    # Return the raw key to the user (they need it for authentication)
    # Only return the full key once - after this, they must store it securely
    preview = f"{raw_key[:8]}...{raw_key[-4:]}"
    return APIKeyCreateResponse(
        id=new_key.id,
        name=new_key.name,
        key_preview=preview,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        last_used_at=None,
        key=raw_key  # Return the raw key here so the user can save it
    )

@router.put("/{key_id}/status", response_model=APIKeyResponse)
async def update_key_status(
    key_id: int,
    payload: APIKeyUpdate,
    current_client: Client = Depends(require_active_client),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.client_id == current_client.id)
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
    
    # We can't show the key preview anymore since we only have the hash
    preview = f"key_{key_obj.id}_{key_obj.created_at.strftime('%Y%m%d')}"
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
        select(APIKey).where(APIKey.id == key_id, APIKey.client_id == current_client.id)
    )
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    await db.delete(key_obj)
    await db.commit()
    return None