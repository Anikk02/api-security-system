import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# ACCESS TOKEN (JWT)
# ============================================================

def create_access_token(
    client_id: int,
    role: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a short-lived JWT access token.
    
    Claims:
        sub: client ID (as string)
        role: client role
        iat: issued at
        exp: expiration
        jti: unique token ID
        type: token type (access)
    """
    now = datetime.now(timezone.utc)
    
    payload = {
        "sub": str(client_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid4()),  # Unique token ID for revocation tracking
        "type": "access",
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Validates:
        - Signature
        - Expiration
        - Token type
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify required claims
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    except ExpiredSignatureError:
        logger.debug("Access token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================
# REFRESH TOKEN (Opaque)
# ============================================================

def create_refresh_token_value() -> str:
    """
    Generate a cryptographically secure random refresh token value.
    
    This is NOT a JWT — it's an opaque string.
    """
    return secrets.token_urlsafe(48)  # 48 bytes → 64 chars base64


# ============================================================
# UTILITIES
# ============================================================

def extract_client_id_from_token(token: str) -> int:
    """Quick extraction of client_id from a valid access token."""
    payload = decode_access_token(token)
    return int(payload["sub"])


def extract_role_from_token(token: str) -> str:
    """Quick extraction of role from a valid access token."""
    payload = decode_access_token(token)
    return payload.get("role", "client")
