import base64
import hashlib
import hmac
import os
import uuid as uuid_lib
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException

from app.config import AUTH_ACCESS_TOKEN_EXPIRES_MINUTES, AUTH_ALGORITHM, AUTH_SECRET_KEY


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64d(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 210_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64e(salt)}${_b64e(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iter_str, salt_b64, digest_b64 = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = _b64d(salt_b64)
        expected = _b64d(digest_b64)
    except Exception:
        return False

    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(computed, expected)


def create_access_token(user_uuid: uuid_lib.UUID, expires_minutes: int | None = None) -> str:
    expire_delta = timedelta(minutes=expires_minutes or AUTH_ACCESS_TOKEN_EXPIRES_MINUTES)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_uuid),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expire_delta).timestamp()),
    }
    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)


def extract_user_uuid_from_auth_header(authorization: str | None) -> uuid_lib.UUID | None:
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = parts[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(status_code=401, detail="Invalid token subject")
        return uuid_lib.UUID(subject)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")


def require_user_uuid_from_auth_header(authorization: str | None) -> uuid_lib.UUID:
    user_uuid = extract_user_uuid_from_auth_header(authorization)
    if user_uuid is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    return user_uuid
