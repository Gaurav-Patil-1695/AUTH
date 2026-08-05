import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, Response, status
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.user import User

# ---------------------------------------------------------------------------
# Environment / config
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "changeme")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
PASSWORD_RESET_EXPIRE_MINUTES: int = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_sha256(value: str) -> str:
    """Return the SHA-256 hex digest of *value*."""
    return hashlib.sha256(value.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token() -> str:
    """Return a URL-safe random token (not yet hashed)."""
    return secrets.token_urlsafe(48)


async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

async def register(body: RegisterRequest, db: AsyncSession) -> RegisterResponse:
    existing = await _get_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": {},
                }
            },
        )

    user = User(
        full_name=body.full_name,
        email=body.email,
        password_hash=_hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
    )


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

async def login(
    body: LoginRequest, response: Response, db: AsyncSession
) -> LoginResponse:
    user = await _get_user_by_email(db, body.email)
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "details": {},
            }
        },
    )
    if user is None or not _verify_password(body.password, user.password_hash):
        raise invalid_exc
    if not user.is_active:
        raise invalid_exc

    access_token = _create_access_token(str(user.id), user.email)

    raw_refresh = _create_refresh_token()
    remember = body.remember_me if body.remember_me is not None else False
    expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_sha256(raw_refresh),
        expires_at=expires_at,
        remember_me=remember,
    )
    db.add(rt)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=int(timedelta(days=expire_days).total_seconds()),
        path="/auth/refresh",
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=MeResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
        ),
    )


# ---------------------------------------------------------------------------
# me
# ---------------------------------------------------------------------------

async def me(current_user: User, db: AsyncSession) -> MeResponse:
    return MeResponse(
        id=str(current_user.id),
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
    )


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

async def logout(
    body: LogoutRequest,
    response: Response,
    current_user: User,
    db: AsyncSession,
) -> LogoutResponse:
    if body.refresh_token:
        token_hash = _hash_sha256(body.refresh_token)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == current_user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    response.delete_cookie(key="refresh_token", path="/auth/refresh")
    return LogoutResponse(message="Logged out successfully.")


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------

async def refresh(
    body: RefreshRequest, response: Response, db: AsyncSession
) -> RefreshResponse:
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Invalid or expired refresh token.",
                "details": {},
            }
        },
    )

    token_hash = _hash_sha256(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        raise invalid_exc
    if rt.expires_at < datetime.now(timezone.utc):
        raise invalid_exc

    # Revoke old token (rotation)
    rt.revoked_at = datetime.now(timezone.utc)

    user = await _get_user_by_id(db, str(rt.user_id))
    if user is None or not user.is_active:
        raise invalid_exc

    access_token = _create_access_token(str(user.id), user.email)

    raw_refresh = _create_refresh_token()
    expire_days = REFRESH_TOKEN_REMEMBER_DAYS if rt.remember_me else REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_sha256(raw_refresh),
        expires_at=expires_at,
        remember_me=rt.remember_me,
    )
    db.add(new_rt)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=int(timedelta(days=expire_days).total_seconds()),
        path="/auth/refresh",
    )

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
    )


# ---------------------------------------------------------------------------
# forgotPassword
# ---------------------------------------------------------------------------

async def forgotPassword(
    body: ForgotPasswordRequest, db: AsyncSession
) -> ForgotPasswordResponse:
    # Enumeration resistance: always return the same message
    generic_response = ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )

    user = await _get_user_by_email(db, body.email)
    if user is None or not user.is_active:
        return generic_response

    # Invalidate any existing unused tokens for this user
    existing_result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.user_id == user.id,
            PasswordReset.used_at.is_(None),
        )
    )
    existing_tokens = existing_result.scalars().all()
    now = datetime.now(timezone.utc)
    for old_token in existing_tokens:
        old_token.used_at = now

    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_sha256(raw_token)
    expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

    pr = PasswordReset(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(pr)
    await db.commit()

    # In a real system, send raw_token via email here.
    # We do not log or expose it in any response.

    return generic_response


# ---------------------------------------------------------------------------
# resetPassword
# ---------------------------------------------------------------------------

async def resetPassword(
    body: ResetPasswordRequest, db: AsyncSession
) -> ResetPasswordResponse:
    invalid_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": "INVALID_RESET_TOKEN",
                "message": "This password reset link is invalid or has expired.",
                "details": {},
            }
        },
    )

    token_hash = _hash_sha256(body.token)
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token_hash == token_hash,
            PasswordReset.used_at.is_(None),
        )
    )
    pr = result.scalar_one_or_none()
    if pr is None:
        raise invalid_exc

    now = datetime.now(timezone.utc)
    if pr.expires_at < now:
        raise invalid_exc

    user = await _get_user_by_id(db, str(pr.user_id))
    if user is None or not user.is_active:
        raise invalid_exc

    # Update password
    user.password_hash = _hash_password(body.password)
    user.updated_at = now

    # Mark token as used
    pr.used_at = now

    # Revoke all active refresh tokens for this user (security: sessions invalidated)
    refresh_result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    active_refresh_tokens = refresh_result.scalars().all()
    for rt in active_refresh_tokens:
        rt.revoked_at = now

    await db.commit()

    return ResetPasswordResponse(message="Your password has been reset successfully.")
