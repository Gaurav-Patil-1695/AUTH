from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.password_reset import PasswordReset


# ---------------------------------------------------------------------------
# Internal row-to-dict helpers
# ---------------------------------------------------------------------------

def _row_to_user(row) -> Optional[dict]:
    if row is None:
        return None
    return dict(row._mapping)


def _row_to_password_reset(row) -> Optional[dict]:
    if row is None:
        return None
    return dict(row._mapping)


def _row_to_refresh_token(row) -> Optional[dict]:
    if row is None:
        return None
    return dict(row._mapping)


# ---------------------------------------------------------------------------
# User repository
# ---------------------------------------------------------------------------

async def get_user_by_id(
    conn: AsyncConnection, user_id: int
) -> Optional[dict]:
    result = await conn.execute(
        text(
            "SELECT id, full_name, email, password_hash, is_active, "
            "created_at, updated_at "
            "FROM users WHERE id = :id"
        ),
        {"id": user_id},
    )
    return _row_to_user(result.first())


async def get_user_by_email(
    conn: AsyncConnection, email: str
) -> Optional[dict]:
    result = await conn.execute(
        text(
            "SELECT id, full_name, email, password_hash, is_active, "
            "created_at, updated_at "
            "FROM users WHERE email = :email"
        ),
        {"email": email},
    )
    return _row_to_user(result.first())


async def create_user(
    conn: AsyncConnection,
    *,
    full_name: str,
    email: str,
    password_hash: str,
) -> dict:
    result = await conn.execute(
        text(
            "INSERT INTO users (full_name, email, password_hash, is_active) "
            "VALUES (:full_name, :email, :password_hash, TRUE) "
            "RETURNING id, full_name, email, password_hash, is_active, "
            "created_at, updated_at"
        ),
        {
            "full_name": full_name,
            "email": email,
            "password_hash": password_hash,
        },
    )
    row = result.first()
    return dict(row._mapping)


async def update_user_password(
    conn: AsyncConnection, user_id: int, password_hash: str
) -> None:
    await conn.execute(
        text(
            "UPDATE users "
            "SET password_hash = :password_hash, updated_at = NOW() "
            "WHERE id = :id"
        ),
        {"password_hash": password_hash, "id": user_id},
    )


# ---------------------------------------------------------------------------
# PasswordReset repository
# ---------------------------------------------------------------------------

async def create_password_reset(
    conn: AsyncConnection,
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> dict:
    result = await conn.execute(
        text(
            "INSERT INTO password_resets (user_id, token_hash, expires_at) "
            "VALUES (:user_id, :token_hash, :expires_at) "
            "RETURNING id, user_id, token_hash, expires_at, used_at, created_at"
        ),
        {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        },
    )
    row = result.first()
    return dict(row._mapping)


async def get_password_reset_by_token_hash(
    conn: AsyncConnection, token_hash: str
) -> Optional[dict]:
    result = await conn.execute(
        text(
            "SELECT id, user_id, token_hash, expires_at, used_at, created_at "
            "FROM password_resets "
            "WHERE token_hash = :token_hash"
        ),
        {"token_hash": token_hash},
    )
    return _row_to_password_reset(result.first())


async def mark_password_reset_used(
    conn: AsyncConnection, reset_id: int
) -> None:
    await conn.execute(
        text(
            "UPDATE password_resets "
            "SET used_at = NOW() "
            "WHERE id = :id"
        ),
        {"id": reset_id},
    )


async def invalidate_password_resets_for_user(
    conn: AsyncConnection, user_id: int
) -> None:
    """Mark all unused resets for a user as used (burn-on-password-change)."""
    await conn.execute(
        text(
            "UPDATE password_resets "
            "SET used_at = NOW() "
            "WHERE user_id = :user_id AND used_at IS NULL"
        ),
        {"user_id": user_id},
    )


# ---------------------------------------------------------------------------
# RefreshToken repository
# ---------------------------------------------------------------------------

async def create_refresh_token(
    conn: AsyncConnection,
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    remember_me: bool,
) -> dict:
    result = await conn.execute(
        text(
            "INSERT INTO refresh_tokens "
            "(user_id, token_hash, expires_at, remember_me) "
            "VALUES (:user_id, :token_hash, :expires_at, :remember_me) "
            "RETURNING id, user_id, token_hash, expires_at, "
            "revoked_at, remember_me, created_at"
        ),
        {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "remember_me": remember_me,
        },
    )
    row = result.first()
    return dict(row._mapping)


async def get_refresh_token_by_token_hash(
    conn: AsyncConnection, token_hash: str
) -> Optional[dict]:
    result = await conn.execute(
        text(
            "SELECT id, user_id, token_hash, expires_at, "
            "revoked_at, remember_me, created_at "
            "FROM refresh_tokens "
            "WHERE token_hash = :token_hash"
        ),
        {"token_hash": token_hash},
    )
    return _row_to_refresh_token(result.first())


async def revoke_refresh_token(
    conn: AsyncConnection, token_id: int
) -> None:
    await conn.execute(
        text(
            "UPDATE refresh_tokens "
            "SET revoked_at = NOW() "
            "WHERE id = :id"
        ),
        {"id": token_id},
    )


async def revoke_all_refresh_tokens_for_user(
    conn: AsyncConnection, user_id: int
) -> None:
    """Revoke every active refresh token for a user (logout-all)."""
    await conn.execute(
        text(
            "UPDATE refresh_tokens "
            "SET revoked_at = NOW() "
            "WHERE user_id = :user_id AND revoked_at IS NULL"
        ),
        {"user_id": user_id},
    )


async def rotate_refresh_token(
    conn: AsyncConnection,
    *,
    old_token_id: int,
    user_id: int,
    new_token_hash: str,
    expires_at: datetime,
    remember_me: bool,
) -> dict:
    """Revoke the old token and issue a new one atomically (within the same connection)."""
    await revoke_refresh_token(conn, old_token_id)
    return await create_refresh_token(
        conn,
        user_id=user_id,
        token_hash=new_token_hash,
        expires_at=expires_at,
        remember_me=remember_me,
    )
