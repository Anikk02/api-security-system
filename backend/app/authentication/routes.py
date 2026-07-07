import logging
from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    ClientRegister,
    ClientRegisterResponse,
    ClientLogin,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    LogoutRequest,
    LogoutResponse,
    ClientProfile,
    ChangePasswordRequest,
    ChangePasswordResponse,
    AuthError,
    ChangeEmailRequest,
    ChangeEmailResponse,
    ChangeEmailConfirmRequest,
)
from app.authentication.service import (
    register_client,
    login_client,
    refresh_access_token,
    forgot_password,
    reset_password,
    logout_client,
    logout_all_devices,
    request_email_change,
    confirm_email_change,
)
from app.authentication.dependencies import (
    get_current_client,
    require_active_client,
)
from app.authentication.password_handler import (
    verify_password,
    hash_password,
)
from app.db.models.client import Client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication", "control"],
    responses={
        401: {"model": AuthError, "description": "Unauthorized"},
        403: {"model": AuthError, "description": "Forbidden"},
    },
)


# ============================================================
# 1. REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=ClientRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new client",
)
async def register(
    data: ClientRegister,
    db: AsyncSession = Depends(get_db),
):
    """Create a new client account."""
    return await register_client(db, data)


# ============================================================
# 2. LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get tokens",
)
async def login(
    data: ClientLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and get access + refresh tokens."""
    ip_address = request.client.host if request.client else None
    device_info = request.headers.get("User-Agent", "")[:500]
    
    return await login_client(
        db, data,
        ip_address=ip_address,
        device_info=device_info,
    )


# ============================================================
# 3. REFRESH TOKEN
# ============================================================

@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh access token",
)
async def refresh(
    data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get a new access token using refresh token."""
    return await refresh_access_token(db, data)


# ============================================================
# 4. LOGOUT
# ============================================================

@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout (revoke refresh token)",
)
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_client: Client = Depends(get_current_client),
):
    """Revoke the current refresh token."""
    return await logout_client(db, data)


# ============================================================
# 5. LOGOUT ALL DEVICES
# ============================================================

@router.post(
    "/logout-all",
    response_model=LogoutResponse,
    summary="Logout from all devices",
)
async def logout_all(
    db: AsyncSession = Depends(get_db),
    current_client: Client = Depends(require_active_client),
):
    """Revoke all active refresh sessions."""
    return await logout_all_devices(db, current_client.id)


# ============================================================
# 6. FORGOT PASSWORD
# ============================================================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request password reset",
)
async def forgot_pw(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a password reset token."""
    return await forgot_password(db, data)


# ============================================================
# 7. RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset password with token",
)
async def reset_pw(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token."""
    return await reset_password(db, data)


# ============================================================
# 8. GET CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=ClientProfile,
    summary="Get current user profile",
)
async def get_me(
    current_client: Client = Depends(require_active_client),
):
    """Get profile of current client."""
    return ClientProfile.model_validate(current_client)


# ============================================================
# 9. CHANGE PASSWORD (Authenticated)
# ============================================================

@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    summary="Change password",
)
async def change_pw(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_client: Client = Depends(require_active_client),
):
    """Change password while logged in."""
    
    # Verify current password
    if not verify_password(data.current_password, current_client.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Hash and update
    current_client.password_hash = hash_password(data.new_password)
    await db.commit()
    
    logger.info(f"Password changed for client: {current_client.email}")
    
    return ChangePasswordResponse(message="Password changed successfully")

@router.post("/change-email")
async def change_email(
    data: ChangeEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_client: Client = Depends(require_active_client),
):
    return await request_email_change(db, current_client, data)

@router.post("/confirm-email")
async def confirm_email(
    data: ChangeEmailConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    return await confirm_email_change(db, data)
