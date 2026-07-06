# backend/app/schemas/__init__.py
from .dashboard import (
    DashboardStatsResponse,
    TrafficDataPoint,
    TrafficResponse,
    SuspiciousUserResponse,
    AlertResponse,
    LogResponse,
    UserDetailsResponse
)
from .auth import (
    # Client schemas
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
    AuthError,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ChangeEmailRequest,
    ChangeEmailConfirmRequest,
    ChangeEmailResponse,
    # Admin schemas
    AdminLogin,
    AdminTokenResponse,
    AdminProfileResponse,
)

__all__ = [
    # Dashboard
    "DashboardStatsResponse",
    "TrafficDataPoint",
    "TrafficResponse",
    "SuspiciousUserResponse",
    "AlertResponse",
    "LogResponse",
    "UserDetailsResponse",
    # Auth
    "ClientRegister",
    "ClientRegisterResponse",
    "ClientLogin",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "LogoutRequest",
    "LogoutResponse",
    "ClientProfile",
    "AuthError",
    "ChangePasswordRequest",
    "ChangePasswordResponse",
    "ChangeEmailRequest",
    "ChangeEmailConfirmRequest",
    "ChangeEmailResponse",
    # Admin
    "AdminLogin",
    "AdminTokenResponse",
    "AdminProfileResponse",
]