# backend/app/authentication/admin_dependencies.py
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.admin import Admin
from app.authentication.jwt_handler import decode_access_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/admin/login",
    auto_error=True,
)


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """
    Extract and validate JWT token, then fetch the admin from DB.
    """
    try:
        payload = decode_access_token(token)
    except HTTPException:
        raise
    
    admin_id_str = payload.get("sub")
    if not admin_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        admin_id = int(admin_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(Admin).where(Admin.id == admin_id)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is not active",
        )
    
    return admin