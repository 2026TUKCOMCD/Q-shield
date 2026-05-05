from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import (
    FRONTEND_AUTH_CALLBACK_URL,
    GITHUB_OAUTH_CLIENT_ID,
    GITHUB_OAUTH_CLIENT_SECRET,
    GITHUB_OAUTH_REDIRECT_URI,
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI,
)
from app.db import get_db
from app.models import AuthIdentity, User
from app.security import (
    create_access_token,
    create_oauth_state,
    extract_user_uuid_from_auth_header,
    hash_password,
    verify_oauth_state,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{3,}$")


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    displayName: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: dict


class OAuthProfile(BaseModel):
    provider: str
    provider_user_id: str
    email: str | None = None
    email_verified: bool = False
    name: str | None = None
    avatar_url: str | None = None


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_signup_email(email: str) -> str:
    normalized = _normalize_email(email)
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Enter a valid email address like name@example.com.")
    return normalized


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _validate_username(username: str) -> str:
    normalized = _normalize_username(username)
    if not re.fullmatch(r"[a-z0-9_][a-z0-9_.-]{2,49}", normalized):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-50 characters and use letters, numbers, dot, dash, or underscore",
        )
    return normalized


def _find_active_user_by_username(db: Session, username: str) -> User | None:
    normalized = _normalize_username(username)
    return (
        db.query(User)
        .filter(func.lower(User.username) == normalized)
        .filter(User.deleted_at.is_(None))
        .first()
    )


def _user_payload(user: User, provider: str | None = None) -> dict[str, Any]:
    return {
        "uuid": str(user.uuid),
        "username": user.username,
        "email": user.email,
        "displayName": user.display_name,
        "avatarUrl": user.avatar_url,
        "status": user.status,
        "provider": provider,
    }


def _frontend_redirect(**params: str) -> RedirectResponse:
    separator = "&" if "?" in FRONTEND_AUTH_CALLBACK_URL else "?"
    return RedirectResponse(f"{FRONTEND_AUTH_CALLBACK_URL}{separator}{urlencode(params)}")


def _frontend_error_redirect(message: str) -> RedirectResponse:
    return _frontend_redirect(error=message)


def _require_oauth_config(provider: str) -> None:
    if provider == "google" and not (GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET):
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in backend/.env, then restart the backend.",
        )
    if provider == "github" and not (GITHUB_OAUTH_CLIENT_ID and GITHUB_OAUTH_CLIENT_SECRET):
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth is not configured. Set GITHUB_OAUTH_CLIENT_ID and GITHUB_OAUTH_CLIENT_SECRET in backend/.env, then restart the backend.",
        )


def _build_auth_url(provider: str) -> str:
    state = create_oauth_state(provider)
    if provider == "google":
        params = {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    params = {
        "client_id": GITHUB_OAUTH_CLIENT_ID,
        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


def _exchange_google_code(code: str) -> OAuthProfile:
    with httpx.Client(timeout=15.0) as client:
        token_response = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="Google OAuth token response is missing access token")

        user_response = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_response.raise_for_status()
        profile = user_response.json()

    return OAuthProfile(
        provider="google",
        provider_user_id=str(profile["id"]),
        email=_normalize_email(profile["email"]) if profile.get("email") else None,
        email_verified=bool(profile.get("verified_email")),
        name=profile.get("name"),
        avatar_url=profile.get("picture"),
    )


def _select_github_email(emails: list[dict[str, Any]]) -> tuple[str | None, bool]:
    primary = next((email for email in emails if email.get("primary")), None)
    selected = primary or next((email for email in emails if email.get("verified")), None)
    if not selected:
        return None, False
    return selected.get("email"), bool(selected.get("verified"))


def _exchange_github_code(code: str) -> OAuthProfile:
    with httpx.Client(timeout=15.0) as client:
        token_response = client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_OAUTH_CLIENT_ID,
                "client_secret": GITHUB_OAUTH_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="GitHub OAuth token response is missing access token")

        user_response = client.get(
            GITHUB_USER_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        user_response.raise_for_status()
        github_user = user_response.json()

        email = github_user.get("email")
        email_verified = bool(email)
        if not email:
            emails_response = client.get(
                GITHUB_EMAILS_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {access_token}",
                },
            )
            emails_response.raise_for_status()
            email, email_verified = _select_github_email(emails_response.json())

    return OAuthProfile(
        provider="github",
        provider_user_id=str(github_user["id"]),
        email=_normalize_email(email) if email else None,
        email_verified=email_verified,
        name=github_user.get("name") or github_user.get("login"),
        avatar_url=github_user.get("avatar_url"),
    )


def _upsert_oauth_user(db: Session, profile: OAuthProfile) -> User:
    identity = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == profile.provider)
        .filter(AuthIdentity.provider_user_id == profile.provider_user_id)
        .filter(AuthIdentity.deleted_at.is_(None))
        .first()
    )

    if identity:
        user = identity.user
        if not user or user.deleted_at is not None:
            raise HTTPException(status_code=401, detail="OAuth identity is inactive")
    else:
        user = User(
            username=None,
            email=profile.email,
            display_name=profile.name,
            avatar_url=profile.avatar_url,
            status="ACTIVE",
            is_email_verified=profile.email_verified,
        )
        db.add(user)
        db.flush()

        identity = AuthIdentity(
            user_uuid=user.uuid,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            provider_email=profile.email,
            is_primary=user.password_hash is None,
        )
        db.add(identity)

    user.email = user.email or profile.email
    user.display_name = profile.name or user.display_name
    user.avatar_url = profile.avatar_url or user.avatar_url
    user.is_email_verified = user.is_email_verified or profile.email_verified
    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_count = 0
    identity.provider_email = profile.email
    db.commit()
    db.refresh(user)
    return user


def _complete_oauth_login(db: Session, provider: str, code: str, state: str) -> RedirectResponse:
    try:
        verify_oauth_state(state, provider)
        profile = _exchange_google_code(code) if provider == "google" else _exchange_github_code(code)
        user = _upsert_oauth_user(db, profile)
        token = create_access_token(user.uuid, email=user.email, provider=provider, username=user.username)
    except httpx.HTTPError:
        return _frontend_error_redirect("OAuth provider request failed")
    except HTTPException as exc:
        return _frontend_error_redirect(str(exc.detail))

    # TODO: Prefer an httpOnly secure cookie in production. The current frontend auth
    # stack stores Bearer tokens in localStorage, so the OAuth callback mirrors it.
    return _frontend_redirect(accessToken=token, tokenType="Bearer")


@router.post("/signup", response_model=AuthTokenResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    username = _validate_username(payload.username)
    normalized_email = _validate_signup_email(payload.email)

    existing = _find_active_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already registered")

    user = User(
        username=username,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        display_name=payload.displayName or username,
        status="ACTIVE",
        is_email_verified=False,
    )
    db.add(user)
    db.flush()

    identity = AuthIdentity(
        user_uuid=user.uuid,
        provider="local",
        provider_user_id=username,
        provider_email=normalized_email,
        is_primary=True,
    )
    db.add(identity)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.uuid, email=user.email, provider="local", username=user.username)
    return AuthTokenResponse(
        accessToken=token,
        user=_user_payload(user, provider="local"),
    )


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    username = _validate_username(payload.username)
    user = _find_active_user_by_username(db, username)
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_count = 0
    db.commit()

    token = create_access_token(user.uuid, email=user.email, provider="local", username=user.username)
    return AuthTokenResponse(
        accessToken=token,
        user=_user_payload(user, provider="local"),
    )


@router.get("/google/login")
def google_login():
    try:
        _require_oauth_config("google")
    except HTTPException as exc:
        return _frontend_error_redirect(str(exc.detail))
    return RedirectResponse(_build_auth_url("google"))


@router.get("/google/callback")
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return _frontend_error_redirect(error)
    if not code or not state:
        return _frontend_error_redirect("Missing Google OAuth callback parameters")
    return _complete_oauth_login(db, "google", code, state)


@router.get("/github/login")
def github_login():
    try:
        _require_oauth_config("github")
    except HTTPException as exc:
        return _frontend_error_redirect(str(exc.detail))
    return RedirectResponse(_build_auth_url("github"))


@router.get("/github/callback")
def github_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return _frontend_error_redirect(error)
    if not code or not state:
        return _frontend_error_redirect("Missing GitHub OAuth callback parameters")
    return _complete_oauth_login(db, "github", code, state)


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

    payload = _user_payload(user)
    payload["lastLoginAt"] = user.last_login_at
    return payload
