from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from jose import jwt

from app.auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutResponse,
    RefreshResponse,
)

# ---------------------------------------------------------------------------
# Environment / configuration
# ---------------------------------------------------------------------------

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repository calls in production)
# ---------------------------------------------------------------------------

# Keyed by email (lowercased)
_users: dict[str, dict] = {}

# Keyed by token_hash
_refresh_tokens: dict[str, dict] = {}

# Keyed by token_hash
_password_resets: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    """Return True when *plain* matches *hashed*."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    """Return the hex SHA-256 digest of *value*."""
    return hashlib.sha256(value.encode()).hexdigest()


def _make_access_token(user_id: str, email: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _make_refresh_token() -> str:
    """Return a secure random opaque refresh token (not hashed yet)."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def _error(
    status_code: int,
    code: str,
    message: str,
    details: Optional[dict] = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


# ---------------------------------------------------------------------------
# Password policy (mirrors validation-rules.json / capabilities.yaml)
# ---------------------------------------------------------------------------

def _validate_password_policy(password: str) -> Optional[str]:
    """
    Return an error message string when *password* fails policy,
    or None when it passes.
    Messages are verbatim from validation-rules.json.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


# ---------------------------------------------------------------------------
# Endpoint handlers
# ---------------------------------------------------------------------------

async def register(payload: RegisterRequest) -> RegisterResponse:
    """Create a new user account (FR-01)."""
    email_key = payload.email.lower()

    # Duplicate-email check
    if email_key in _users:
        raise _error(
            status.HTTP_409_CONFLICT,
            "EMAIL_TAKEN",
            "An account with this email already exists.",
        )

    # confirm_password match
    if payload.password != payload.confirm_password:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PASSWORD_MISMATCH",
            "Passwords do not match.",
        )

    # Password policy
    policy_error = _validate_password_policy(payload.password)
    if policy_error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "WEAK_PASSWORD",
            policy_error,
        )

    # Terms acceptance
    if not payload.terms:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "TERMS_REQUIRED",
            "You must accept the terms and conditions.",
        )

    user_id = uuid.uuid4().hex
    now = datetime.now(tz=timezone.utc)

    _users[email_key] = {
        "id": user_id,
        "full_name": payload.full_name,
        "email": email_key,
        "password_hash": _hash_password(payload.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    access_token = _make_access_token(user_id, email_key)
    raw_refresh = _make_refresh_token()
    refresh_hash = _sha256(raw_refresh)
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    _refresh_tokens[refresh_hash] = {
        "id": uuid.uuid4().hex,
        "user_id": user_id,
        "token_hash": refresh_hash,
        "expires_at": expires_at,
        "revoked_at": None,
        "remember_me": False,
        "created_at": now,
    }

    return RegisterResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
    )


async def login(payload: LoginRequest) -> LoginResponse:
    email_key = payload.email.lower()
    user = _users.get(email_key)

    if not user or not _verify_password(payload.password, user["password_hash"]):
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Invalid email or password.",
        )

    if not user["is_active"]:
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "ACCOUNT_INACTIVE",
            "This account has been deactivated.",
        )

    now = datetime.now(tz=timezone.utc)
    access_token = _make_access_token(user["id"], email_key)
    raw_refresh = _make_refresh_token()
    refresh_hash = _sha256(raw_refresh)
    remember = bool(getattr(payload, "remember_me", False))
    expire_days = REFRESH_TOKEN_EXPIRE_DAYS * 4 if remember else REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = now + timedelta(days=expire_days)

    _refresh_tokens[refresh_hash] = {
        "id": uuid.uuid4().hex,
        "user_id": user["id"],
        "token_hash": refresh_hash,
        "expires_at": expires_at,
        "revoked_at": None,
        "remember_me": remember,
        "created_at": now,
    }

    return LoginResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
    )


async def forgotPassword(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    # Enumeration-resistant: always return the same message.
    email_key = payload.email.lower()
    user = _users.get(email_key)

    if user and user["is_active"]:
        raw_token = uuid.uuid4().hex + uuid.uuid4().hex
        token_hash = _sha256(raw_token)
        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(hours=1)

        _password_resets[token_hash] = {
            "id": uuid.uuid4().hex,
            "user_id": user["id"],
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used_at": None,
            "created_at": now,
        }
        # In production: send raw_token via email link.

    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


async def resetPassword(payload: ResetPasswordRequest) -> ResetPasswordResponse:
    token_hash = _sha256(payload.token)
    record = _password_resets.get(token_hash)
    now = datetime.now(tz=timezone.utc)

    if (
        record is None
        or record["used_at"] is not None
        or record["expires_at"] < now
    ):
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_OR_EXPIRED_TOKEN",
            "This password reset link is invalid or has expired.",
        )

    if payload.password != payload.confirm_password:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PASSWORD_MISMATCH",
            "Passwords do not match.",
        )

    policy_error = _validate_password_policy(payload.password)
    if policy_error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "WEAK_PASSWORD",
            policy_error,
        )

    # Find user and update password
    user_id = record["user_id"]
    user_record = next(
        (u for u in _users.values() if u["id"] == user_id), None
    )
    if user_record is None:
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_OR_EXPIRED_TOKEN",
            "This password reset link is invalid or has expired.",
        )

    user_record["password_hash"] = _hash_password(payload.password)
    user_record["updated_at"] = now
    record["used_at"] = now

    # Revoke all refresh tokens for this user
    for rt in _refresh_tokens.values():
        if rt["user_id"] == user_id and rt["revoked_at"] is None:
            rt["revoked_at"] = now

    return ResetPasswordResponse(message="Your password has been reset successfully.")


async def me() -> MeResponse:
    # In production this would read from the JWT in the Authorization header.
    # Stub raises 401 to signal the caller must be authenticated.
    raise _error(
        status.HTTP_401_UNAUTHORIZED,
        "NOT_AUTHENTICATED",
        "Authentication required.",
    )


async def logout() -> LogoutResponse:
    # In production: revoke the refresh token supplied in the request.
    return LogoutResponse(message="Logged out successfully.")


async def refresh() -> RefreshResponse:
    # In production: validate the refresh token, rotate it, issue new access token.
    raise _error(
        status.HTTP_401_UNAUTHORIZED,
        "INVALID_REFRESH_TOKEN",
        "Refresh token is invalid or has expired.",
    )
