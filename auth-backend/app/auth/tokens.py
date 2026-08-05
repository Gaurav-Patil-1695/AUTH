from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config.settings import settings

# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TTL: timedelta = timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

# Refresh token TTL — standard vs. extended (rememberMe)
REFRESH_TOKEN_TTL_STANDARD: timedelta = timedelta(
    minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
)
REFRESH_TOKEN_TTL_EXTENDED: timedelta = timedelta(
    minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME
)

# Password-reset token TTL
RESET_TOKEN_TTL: timedelta = timedelta(
    minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
)

# JWT algorithm
ALGORITHM: str = "HS256"


# ---------------------------------------------------------------------------
# Raw token generation
# ---------------------------------------------------------------------------

def _generate_opaque_token(nbytes: int = 32) -> str:
    """Return a URL-safe, cryptographically random token string."""
    return secrets.token_urlsafe(nbytes)


# ---------------------------------------------------------------------------
# Hashing (SHA-256) — used for refresh and reset tokens stored in the DB
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    """Return the hex-encoded SHA-256 digest of *token*."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Access token (JWT)
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> tuple[str, datetime]:
    """Create a signed JWT access token for *user_id*.

    Returns
    -------
    tuple[str, datetime]
        The encoded JWT string and its UTC expiry datetime.
    """
    expires_at = _utcnow() + ACCESS_TOKEN_TTL
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": _utcnow(),
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> int | None:
    """Decode and verify *token*; return user_id or None on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Refresh token (opaque, stored hashed)
# ---------------------------------------------------------------------------

def create_refresh_token(
    *, remember_me: bool = False
) -> tuple[str, str, datetime]:
    """Create a new opaque refresh token.

    Parameters
    ----------
    remember_me:
        When True the TTL is extended (``REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME``).

    Returns
    -------
    tuple[str, str, datetime]
        ``(raw_token, token_hash, expires_at)`` where *raw_token* is sent to
        the client and *token_hash* is stored in the database.
    """
    ttl = REFRESH_TOKEN_TTL_EXTENDED if remember_me else REFRESH_TOKEN_TTL_STANDARD
    expires_at = _utcnow() + ttl
    raw = _generate_opaque_token()
    token_hash = hash_token(raw)
    return raw, token_hash, expires_at


# ---------------------------------------------------------------------------
# Password-reset token (opaque, stored hashed)
# ---------------------------------------------------------------------------

def create_reset_token() -> tuple[str, str, datetime]:
    """Create a new opaque password-reset token.

    Returns
    -------
    tuple[str, str, datetime]
        ``(raw_token, token_hash, expires_at)``.
    """
    expires_at = _utcnow() + RESET_TOKEN_TTL
    raw = _generate_opaque_token()
    token_hash = hash_token(raw)
    return raw, token_hash, expires_at


# ---------------------------------------------------------------------------
# Rotation helpers
# ---------------------------------------------------------------------------

def rotate_refresh_token(
    *, remember_me: bool = False
) -> tuple[str, str, datetime]:
    """Convenience wrapper — generate a fresh refresh token for rotation.

    Rotation (revoke old + insert new) is carried out by
    ``repository.rotate_refresh_token``; this function only produces the
    new token material.

    Returns
    -------
    tuple[str, str, datetime]
        ``(raw_token, new_token_hash, expires_at)``.
    """
    return create_refresh_token(remember_me=remember_me)


# ---------------------------------------------------------------------------
# Revocation check helpers
# ---------------------------------------------------------------------------

def is_refresh_token_valid(token_row: dict) -> bool:
    """Return True when the DB row represents a usable refresh token.

    A token is invalid if it has been revoked (``revoked_at`` is set) or has
    passed its ``expires_at`` deadline.
    """
    if token_row.get("revoked_at") is not None:
        return False
    expires_at: datetime = token_row["expires_at"]
    # Ensure comparison is timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return _utcnow() < expires_at


def is_reset_token_valid(token_row: dict) -> bool:
    """Return True when the DB row represents a usable password-reset token.

    A token is invalid if it has been used (``used_at`` is set) or has passed
    its ``expires_at`` deadline.
    """
    if token_row.get("used_at") is not None:
        return False
    expires_at: datetime = token_row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return _utcnow() < expires_at


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)
