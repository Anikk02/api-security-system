import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.client import Client
from app.authentication.jwt_handler import decode_access_token

logger = logging.getLogger(__name__)


# ============================================================
# OAUTH2 SCHEME
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=True,  # Automatically returns 401 if no token
)

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


# ============================================================
# CORE DEPENDENCY: Get Current Client
# ============================================================

async def get_current_client(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Client:
    """
    Extract and validate JWT token, then fetch the client from DB.
    """
    payload = decode_access_token(token)
    
    client_id_str = payload.get("sub")
    if not client_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        client_id = int(client_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return client


# ============================================================
# DEPENDENCY: Require Active Client
# ============================================================

async def require_active_client(
    client: Client = Depends(get_current_client),
) -> Client:
    """
    Ensure the authenticated client has an 'active' status.
    """
    if not client.is_active:
        detail = "Account is not active"
        if client.status == "suspended":
            detail = "Account suspended. Contact support."
        elif client.status == "locked":
            detail = "Account locked due to too many failed login attempts."
        elif client.status == "inactive":
            detail = "Account is inactive."
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
    
    return client


# ============================================================
# DEPENDENCY: Require Admin Role
# ============================================================

async def require_admin(
    client: Client = Depends(require_active_client),
) -> Client:
    """
    Ensure the authenticated client has admin privileges.
    """
    if not client.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return client


# ============================================================
# DEPENDENCY: Require Super Admin
# ============================================================

async def require_super_admin(
    client: Client = Depends(require_active_client),
) -> Client:
    """
    Ensure the client has super_admin role.
    """
    if client.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    
    return client


# ============================================================
# DEPENDENCY: Optional Authentication
# ============================================================

async def get_current_client_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[Client]:
    """
    Optionally authenticate — returns None if no token provided.
    """
    if not token:
        return None
    
    try:
        return await get_current_client(token=token, db=db)
    except HTTPException:
        return None
