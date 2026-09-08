"""Small dependency-free token and password layer for the local ULPF service."""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .db_models import DBUser

SECRET = os.getenv("ULPF_AUTH_SECRET", "change-this-local-secret")
ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"pbkdf2_sha256$210000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _encode_part(value: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).decode().rstrip("=")


def _decode_part(value: str) -> dict[str, Any]:
    padding = "=" * (-len(value) % 4)
    parsed = json.loads(base64.urlsafe_b64decode((value + padding).encode()))
    if not isinstance(parsed, dict):
        raise ValueError("Invalid token")
    return parsed


def create_access_token(user_id: int, expires_minutes: int = 720) -> str:
    header = _encode_part({"alg": ALGORITHM, "typ": "JWT"})
    payload = _encode_part({"sub": str(user_id), "exp": int((datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)).timestamp())})
    unsigned = f"{header}.{payload}"
    signature = hmac.new(SECRET.encode(), unsigned.encode(), hashlib.sha256).digest()
    return f"{unsigned}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def _user_from_token(db: Session, token: str) -> DBUser:
    try:
        header, payload, signature = token.split(".", 2)
        unsigned = f"{header}.{payload}"
        expected = hmac.new(SECRET.encode(), unsigned.encode(), hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode((signature + "=" * (-len(signature) % 4)).encode())
        claims = _decode_part(payload)
        if not hmac.compare_digest(actual, expected) or int(claims["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Expired token")
        user_id = int(claims["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None
    user = db.get(DBUser, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> DBUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    return _user_from_token(db, credentials.credentials)


def authenticate(db: Session, email: str, password: str) -> DBUser | None:
    user = db.scalar(select(DBUser).where(DBUser.email == email.lower().strip()))
    return user if user and verify_password(password, user.password_hash) else None
