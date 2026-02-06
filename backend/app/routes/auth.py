from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuthIdentity, User
from app.security import create_access_token, extract_user_uuid_from_auth_header, hash_password, verify_password


router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    displayName: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: dict


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _find_active_user_by_email(db: Session, email: str) -> User | None:
    normalized = _normalize_email(email)
    return (
        db.query(User)
        .filter(func.lower(User.email) == normalized)
        .filter(User.deleted_at.is_(None))
        .first()
    )


@router.post("/signup", response_model=AuthTokenResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)

    existing = _find_active_user_by_email(db, normalized_email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        display_name=payload.displayName,
        status="ACTIVE",
        is_email_verified=False,
    )
    db.add(user)
    db.flush()

    identity = AuthIdentity(
        user_uuid=user.uuid,
        provider="local",
        provider_user_id=normalized_email,
        provider_email=normalized_email,
        is_primary=True,
    )
    db.add(identity)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.uuid)
    return AuthTokenResponse(
        accessToken=token,
        user={
            "uuid": str(user.uuid),
            "email": user.email,
            "displayName": user.display_name,
            "status": user.status,
        },
    )


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _find_active_user_by_email(db, payload.email)
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_count = 0
    db.commit()

    token = create_access_token(user.uuid)
    return AuthTokenResponse(
        accessToken=token,
        user={
            "uuid": str(user.uuid),
            "email": user.email,
            "displayName": user.display_name,
            "status": user.status,
        },
    )


@router.get("/me")
def me(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_uuid = extract_user_uuid_from_auth_header(authorization)
    if user_uuid is None:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = db.query(User).filter(User.uuid == user_uuid).filter(User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "uuid": str(user.uuid),
        "email": user.email,
        "displayName": user.display_name,
        "status": user.status,
        "lastLoginAt": user.last_login_at,
    }
