import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config.settings import settings


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Token hashing (SHA-256) — for reset tokens and refresh tokens
# ---------------------------------------------------------------------------


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a raw token string."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def compare_token(plain_token: str, token_hash: str) -> bool:
    """Constant-time comparison of a raw token against its stored SHA-256 hash."""
    expected = hash_token(plain_token)
    return hmac.compare_digest(expected, token_hash)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str | int,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a signed JWT access token.

    Args:
        subject: The ``sub`` claim value (typically a user id).
        additional_claims: Optional extra claims merged into the payload.
        expires_delta: Custom expiry; defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        A compact, signed JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: The compact JWT string.

    Returns:
        The decoded payload as a dict.

    Raises:
        jose.JWTError: If the token is invalid, expired, or has wrong type.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if payload.get("type") != "access":
        raise JWTError("Token type is not 'access'.")
    return payload


def create_refresh_token(
    subject: str | int,
    remember_me: bool = False,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a signed JWT refresh token.

    Args:
        subject: The ``sub`` claim value (typically a user id).
        remember_me: When True a longer expiry is used.
        expires_delta: Custom expiry; overrides the remember_me logic when given.

    Returns:
        A compact, signed JWT string.
    """
    if expires_delta is None:
        if remember_me:
            expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER)
        else:
            expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "refresh",
        "remember_me": remember_me,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT refresh token.

    Args:
        token: The compact JWT string.

    Returns:
        The decoded payload as a dict.

    Raises:
        jose.JWTError: If the token is invalid, expired, or has wrong type.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if payload.get("type") != "refresh":
        raise JWTError("Token type is not 'refresh'.")
    return payload
