import hashlib
import uuid
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.identity.api_key_cache import get_api_key_cached, invalidate_api_key_cache
import logging
from typing import Tuple, Optional

from app.db.models.api_key import APIKey

logger = logging.getLogger(__name__)


# ============================
# 🧠 Identity Model
# ============================
class Identity:
    def __init__(
        self,
        identity_id: str,
        client_id: int | None,
        api_key: str | None,
        is_anonymous: bool
    ):
        self.identity_id = identity_id
        self.client_id = client_id
        self.api_key = api_key
        self.is_anonymous = is_anonymous

        # Derived
        self.ip_address: str | None = None
        self.behavioral_fingerprint: str | None = None
        self.api_key_id: int | None = None
        
        # User identification metadata
        self.user_identifier_type: str | None = None  # "cookie", "jwt", "fingerprint", "uuid"
        self.user_identifier_value: str | None = None
        self.is_persistent: bool = False  # True for cookie/jwt, False for fingerprint


# ============================
# 🔍 Resolver
# ============================
async def resolve_identity(request: Request, db: AsyncSession) -> Identity:
    logger.info(f"[IDENTITY] Resolving path={request.url.path}")

    # ============================
    # 🌍 Extract IP
    # ============================
    forwarded_ip = request.headers.get("X-Forwarded-For")

    if forwarded_ip:
        ip = forwarded_ip.split(",")[0].strip()
        logger.debug(f"[IDENTITY] Forwarded IP → {ip}")
    else:
        ip = request.client.host if request.client else "unknown"
        logger.debug(f"[IDENTITY] Direct IP → {ip}")

    api_key = request.headers.get("X-API-KEY")

    # ============================
    # 🔐 AUTHENTICATED (API KEY)
    # ============================
    if api_key:
        logger.debug(f"[IDENTITY] API key received (masked) from ip={ip}")

        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

        api_key_obj = await get_api_key_cached(hashed_key, db)

        if api_key_obj:
            logger.info(
                f"[IDENTITY] Authenticated client_id={api_key_obj.client_id} ip={ip}"
            )

            # ============================
            # 👤 Get or create user identifier
            # ============================
            user_identifier, identifier_type, is_persistent = await _get_or_create_user_identifier(
                request, api_key_obj.id
            )
            
            # ============================
            # 🆔 Create composite identity ID
            # ============================
            identity_id = f"api:{api_key_obj.id}:user:{user_identifier}"
            
            logger.info(
                f"[IDENTITY] User identified → type={identifier_type}, "
                f"persistent={is_persistent}, id={user_identifier[:8]}..."
            )

            identity = Identity(
                identity_id=identity_id,
                client_id=api_key_obj.client_id,
                api_key=api_key,
                is_anonymous=False
            )
            
            identity.api_key_id = api_key_obj.id
            identity.ip_address = ip
            identity.user_identifier_type = identifier_type
            identity.user_identifier_value = user_identifier
            identity.is_persistent = is_persistent
            identity.behavioral_fingerprint = _generate_behavioral_fingerprint(
                request, identity
            )

            return identity

        else:
            logger.warning(f"[IDENTITY] Invalid API key from ip={ip}")

    # ============================
    # 🕶️ ANONYMOUS FALLBACK
    # ============================
    anon_id = _generate_anonymous_fingerprint(ip, request)

    logger.info(f"[IDENTITY] Anonymous identity assigned → {anon_id} ip={ip}")

    identity = Identity(
        identity_id=f"{anon_id}",
        client_id=None,
        api_key=None,
        is_anonymous=True
    )

    identity.ip_address = ip
    identity.behavioral_fingerprint = _generate_behavioral_fingerprint(
        request, identity
    )

    return identity


# ============================
# 👤 Get or Create User Identifier (Priority System)
# ============================
async def _get_or_create_user_identifier(
    request: Request, 
    api_key_id: int
) -> Tuple[str, str, bool]:
    """
    Returns: (user_identifier, identifier_type, is_persistent)
    
    Priority:
    1. Cookie "X-TrianSec-User-ID" → Persistent
    2. JWT from Authorization header → Persistent
    3. IP + User-Agent fingerprint → Non-persistent (fallback)
    4. Generate new UUID → Persistent (sets cookie)
    """
    
    # ============================
    # 🍪 PRIORITY 1: Cookie
    # ============================
    cookie_value = request.cookies.get("X-TrianSec-User-ID")
    if cookie_value:
        logger.debug(f"[IDENTITY] User identified via cookie: {cookie_value[:8]}...")
        return cookie_value, "cookie", True
    
    # ============================
    # 🔑 PRIORITY 2: JWT Token
    # ============================
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user_id = _extract_user_id_from_jwt(token)
        if user_id:
            logger.debug(f"[IDENTITY] User identified via JWT: {user_id[:8]}...")
            return user_id, "jwt", True
    
    # ============================
    # 🖐️ PRIORITY 3: IP + User-Agent Fingerprint
    # ============================
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    fingerprint = hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()
    logger.debug(f"[IDENTITY] User identified via fingerprint: {fingerprint[:8]}...")
    
    # ============================
    # 🆕 PRIORITY 4: Generate New UUID
    # ============================
    # Generate UUID for first-time users
    # This will be set as a cookie in the response
    new_uuid = str(uuid.uuid4())
    logger.debug(f"[IDENTITY] New UUID generated for first-time user: {new_uuid[:8]}...")
    
    # Note: The cookie will be set in the middleware/response handler
    # We need to store this so the response can set the cookie
    # Option 1: Store in request.state for middleware to access
    request.state.new_user_cookie = new_uuid
    request.state.should_set_cookie = True
    
    return new_uuid, "uuid", True  # Once cookie is set, it becomes persistent


# ============================
# 🔓 JWT Helper Functions
# ============================
def _extract_user_id_from_jwt(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token.
    You can implement this based on your JWT validation logic.
    """
    try:
        # Option 1: If you have a JWT validation function
        # decoded = validate_and_decode_jwt(token)
        # return decoded.get("sub") or decoded.get("user_id")
        
        # Option 2: Simple decode without validation (for development only)
        # import jwt
        # decoded = jwt.decode(token, options={"verify_signature": False})
        # return decoded.get("sub")
        
        # Placeholder - implement based on your JWT setup
        return None
    except Exception as e:
        logger.warning(f"[IDENTITY] Failed to extract user ID from JWT: {e}")
        return None


# ============================
# 🧠 Anonymous Identity
# ============================
def _generate_anonymous_fingerprint(ip: str, request: Request) -> str:
    if not ip:
        ip = "unknown"

    ua = request.headers.get("user-agent", "")

    raw = f"{ip}:{ua}"

    return hashlib.sha256(raw.encode()).hexdigest()


# ============================
# 🧠 Behavioral Fingerprint
# ============================
def _generate_behavioral_fingerprint(request: Request, identity: Identity) -> str:
    ua = request.headers.get("user-agent", "")
    accept_lang = request.headers.get("accept-language", "")
    accept_enc = request.headers.get("accept-encoding", "")
    path = request.url.path

    # Strong anchor if API key exists
    if identity.api_key:
        api_hash = hashlib.sha256(identity.api_key.encode()).hexdigest()
        raw = f"{api_hash}:{ua}:{accept_lang}:{accept_enc}:{path}"
    else:
        raw = f"{ua}:{accept_lang}:{accept_enc}:{path}"

    return hashlib.sha256(raw.encode()).hexdigest()


# ============================
# 🍪 Cookie Helper (To be used in middleware/response)
# ============================
def set_user_cookie_if_needed(request: Request, response: Response) -> None:
    """
    This function should be called in your middleware or response handler
    to set the user cookie for first-time visitors.
    """
    if hasattr(request.state, "should_set_cookie") and request.state.should_set_cookie:
        cookie_value = getattr(request.state, "new_user_cookie", None)
        if cookie_value:
            response.set_cookie(
                key="X-TrianSec-User-ID",
                value=cookie_value,
                max_age=365 * 24 * 60 * 60,  # 1 year
                httponly=True,               # Prevents XSS access
                secure=True,                 # Only send over HTTPS
                samesite="lax",              # CSRF protection
                path="/"                     # Available for all paths
            )
            logger.debug(f"[IDENTITY] Cookie set for user: {cookie_value[:8]}...")