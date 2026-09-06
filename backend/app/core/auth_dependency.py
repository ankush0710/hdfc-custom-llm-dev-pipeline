import logging
import os
import time
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.dbConfig.database_config import get_db
from app.model.user_model import User_Model

_logger = logging.getLogger(__name__)

# JWT Configuration — JWT_SECRET_KEY MUST be set in the environment.
# Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY env var is required and not set. "
        "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

security = HTTPBearer(auto_error=False)


STRICT_SESSION_ROLES = {"VIEWER", "REVIEWER"}
STRICT_SESSION_MAX_MINUTES = 30

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "ADMIN": {
        "*",  # Wildcard grants all operational and administrative permissions
    },
    "DS": {
        "dataset:*",
        "training:*",
        "evaluation:*",
        "model:*",
        "deployment:*",
        "inference:execute",
        "monitoring:read",
        "auth:me",
        "auth:logout",
    },
    "REVIEWER": {
        "dataset:read",
        "training:read",
        "evaluation:read",
        "evaluation:create",
        "evaluation:start",
        "model:read",
        "deployment:read",
        "inference:execute",
        "monitoring:read",
        "auth:me",
        "auth:logout",
    },
    "VIEWER": {
        "dataset:read",
        "training:read",
        "evaluation:read",
        "model:read",
        "deployment:read",
        "inference:execute",
        "monitoring:read",
        "auth:me",
        "auth:logout",
    },
}


def check_permission(arg1, arg2) -> bool:
    """Evaluate permission against granted set supporting '*' and 'domain:*' wildcards."""
    if isinstance(arg1, str) and isinstance(arg2, (set, list, tuple)):
        required_permission, granted_permissions = arg1, arg2
    else:
        granted_permissions, required_permission = arg1, arg2

    perms = set(granted_permissions) if isinstance(granted_permissions, (set, list, tuple)) else {str(granted_permissions)}
    if "*" in perms:
        return True
    if required_permission in perms:
        return True
    if ":" in required_permission:
        domain = required_permission.split(":", 1)[0]
        if f"{domain}:*" in perms:
            return True
    return False


def hash_password(password: str) -> str:
    """Hash plain text password securely using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token with strict absolute expiration for VIEWER/REVIEWER."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    raw_role = (data.get("role") or "").upper().strip()
    norm_role = "DS" if raw_role in {"DATA_SCIENTIST", "DS"} else raw_role

    if norm_role in STRICT_SESSION_ROLES:
        # Strictly enforce non-sliding 30-minute absolute session lifetime
        session_duration = timedelta(minutes=STRICT_SESSION_MAX_MINUTES)
        expire = now + session_duration
        current_time = time.time()
        abs_exp_ts = int(current_time + STRICT_SESSION_MAX_MINUTES * 60)
        to_encode["abs_exp"] = abs_exp_ts
        to_encode["session_start"] = int(current_time)
    else:
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate signature & expiration of JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature or payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    token: Optional[str] = None,
) -> User_Model:
    """Dependency to extract and validate current authenticated user from Bearer token."""
    raw_token = token or (auth.credentials if auth and hasattr(auth, "credentials") else None)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User_Model).filter(User_Model.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists in system.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact system administrator.",
        )

    # 1. Authoritative DB Role check: prevent stale JWT role from privilege escalation
    token_role = (payload.get("role") or "").upper().strip()
    norm_token_role = "DS" if token_role in {"DATA_SCIENTIST", "DS"} else token_role
    db_raw_role = (user.role or "").upper().strip()
    norm_db_role = "DS" if db_raw_role in {"DATA_SCIENTIST", "DS"} else db_raw_role

    if norm_token_role != norm_db_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalidated: User role or permissions have been updated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Server-side strict 30-minute absolute session verification for VIEWER / REVIEWER
    if norm_db_role in STRICT_SESSION_ROLES:
        abs_exp = payload.get("abs_exp")
        now_ts = int(time.time())
        if not abs_exp or now_ts >= abs_exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired: Maximum 30-minute session limit reached for your role. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


def require_permission(permission: str):
    """FastAPI dependency generator requiring a specific granular permission."""
    def permission_checker(current_user: User_Model = Depends(get_current_user)) -> User_Model:
        raw_role = (current_user.role or "").upper().strip()
        user_role = "DS" if raw_role in {"DATA_SCIENTIST", "DS"} else raw_role

        user_perms = ROLE_PERMISSIONS.get(user_role, set())
        if not check_permission(user_perms, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Action requires '{permission}' permission, which is not granted to role '{user_role}'.",
            )
        return current_user

    return permission_checker


def require_roles(*allowed_roles: str):
    """Dependency generator for Role-Based Access Control (RBAC)."""
    normalized_roles = {
        ("DS" if r.upper() in {"DATA_SCIENTIST", "DS"} else r.upper())
        for r in allowed_roles
    }

    def role_checker(current_user: User_Model = Depends(get_current_user)) -> User_Model:
        raw_role = (current_user.role or "").upper()
        user_role = "DS" if raw_role in {"DATA_SCIENTIST", "DS"} else raw_role

        # ADMIN inherently has all operational and pipeline access permissions
        if user_role == "ADMIN":
            return current_user

        if user_role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Action requires one of {sorted(normalized_roles)} roles, but your current role is '{user_role}'.",
            )
        return current_user

    return role_checker
