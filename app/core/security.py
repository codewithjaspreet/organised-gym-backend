from datetime import datetime, timedelta
from typing import Optional, Dict

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core import config


# -----------------------------
# Security Scheme (JWT Bearer)
# -----------------------------
security = HTTPBearer()


# -----------------------------
# Password Utilities
# -----------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


# -----------------------------
# Token Creation
# -----------------------------
def create_access_token(
    data: Dict,
    expire_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()

    expire = (
        datetime.utcnow() + expire_delta
        if expire_delta
        else datetime.utcnow()
        + timedelta(minutes=config.settings.access_token_expire_minutes)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        config.settings.secret_key,
        algorithm=config.settings.algorithm,
    )


def create_refresh_token(
    data: Dict,
    expire_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()

    expire = (
        datetime.utcnow() + expire_delta
        if expire_delta
        else datetime.utcnow()
        + timedelta(days=config.settings.refresh_token_expire_days)
    )

    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        config.settings.secret_key,
        algorithm=config.settings.algorithm,
    )


# -----------------------------
# Token Decode
# -----------------------------
def decode_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(
            token,
            config.settings.secret_key,
            algorithms=[config.settings.algorithm],
        )
        return payload
    except JWTError:
        return None


# -----------------------------
# Auth Dependency (Swagger + API)
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload
