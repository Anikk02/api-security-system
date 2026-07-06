# backend/app/authentication/admin_routes.py
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.admin import Admin
from app.db.models.admin_refresh_token import AdminRefreshToken
from app.authentication.jwt_handler import create_access_token, create_refresh_token_value
from app.authentication.password_handler import verify_password
from app.schemas.auth import AdminLogin, AdminTokenResponse, AdminProfileResponse, TokenRefreshRequest
from app.authentication.admin_dependencies import get_current_admin
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin Auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    request: AdminLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin login endpoint.
    """
    # Find admin by email
    result = await db.execute(
        select(Admin).where(Admin.email == request.email)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Verify password
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check if admin is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is not active",
        )
    
    # Update last login
    admin.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(admin)
    
    # Create JWT access token
    access_token = create_access_token(
        client_id=admin.id,
        role=admin.role,
        extra_claims={"admin": True, "name": admin.name}
    )
    
    # Create opaque refresh token
    refresh_token_value = create_refresh_token_value()
    
    # Store refresh token in database
    refresh_token_obj = AdminRefreshToken(
        admin_id=admin.id,
        refresh_token=refresh_token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token_obj)
    await db.commit()
    
    return AdminTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=AdminProfileResponse)
async def get_admin_me(
    current_admin: Admin = Depends(get_current_admin),
):
    """Get current admin profile."""
    return AdminProfileResponse(
        id=current_admin.id,
        email=current_admin.email,
        name=current_admin.name,
        role=current_admin.role,
        status=current_admin.status,
        created_at=current_admin.created_at,
        last_login_at=current_admin.last_login_at,
    )


@router.post("/refresh")
async def refresh_admin_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh admin access token using a valid refresh token.
    """
    # Find the refresh token in database
    result = await db.execute(
        select(AdminRefreshToken)
        .where(AdminRefreshToken.refresh_token == request.refresh_token)
        .where(AdminRefreshToken.revoked == False)
        .where(AdminRefreshToken.expires_at > datetime.now(timezone.utc))
    )
    token_obj = result.scalar_one_or_none()
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Get the admin
    result = await db.execute(
        select(Admin).where(Admin.id == token_obj.admin_id)
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive",
        )
    
    # Create new access token
    access_token = create_access_token(
        client_id=admin.id,
        role=admin.role,
        extra_claims={"admin": True, "name": admin.name}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def admin_logout(
    current_admin: Admin = Depends(get_current_admin),
    request: TokenRefreshRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout admin by revoking the refresh token.
    """
    if request and request.refresh_token:
        # Revoke the specific refresh token
        result = await db.execute(
            select(AdminRefreshToken)
            .where(AdminRefreshToken.refresh_token == request.refresh_token)
            .where(AdminRefreshToken.admin_id == current_admin.id)
        )
        token_obj = result.scalar_one_or_none()
        
        if token_obj:
            token_obj.revoked = True
            await db.commit()
            return {"message": "Logged out successfully"}
    
    return {"message": "Logged out successfully"}


@router.get("/health")
async def admin_health():
    """Admin API health check."""
    return {"status": "healthy", "service": "admin_auth"}