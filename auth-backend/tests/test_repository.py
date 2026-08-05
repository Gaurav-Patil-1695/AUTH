"""Tests for app.auth.repository (uses async mocked AsyncConnection)"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.auth import repository
from app.auth.repository import (
    _row_to_password_reset,
    _row_to_refresh_token,
    _row_to_user,
    create_password_reset,
    create_refresh_token,
    create_user,
    get_password_reset_by_token_hash,
    get_refresh_token_by_token_hash,
    get_user_by_email,
    get_user_by_id,
    invalidate_password_resets_for_user,
    mark_password_reset_used,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token,
    rotate_refresh_token,
    update_user_password,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPIRY = datetime(2024, 12, 31, 0, 0, 0, tzinfo=timezone.utc)


def _make_row(**kwargs):
    """Create a fake SQLAlchemy row with a ._mapping attribute."""
    row = MagicMock()
    row._mapping = kwargs
    return row


def _make_conn(first_return=None):
    """Build an AsyncConnection mock whose execute().first() returns first_return."""
    result = MagicMock()
    result.first.return_value = first_return
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)
    return conn


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

class TestRowHelpers:
    def test_row_to_user_none(self):
        assert _row_to_user(None) is None

    def test_row_to_user_valid(self):
        row = _make_row(id=1, email="a@b.com")
        assert _row_to_user(row) == {"id": 1, "email": "a@b.com"}

    def test_row_to_password_reset_none(self):
        assert _row_to_password_reset(None) is None

    def test_row_to_password_reset_valid(self):
        row = _make_row(id=5, user_id=1)
        assert _row_to_password_reset(row) == {"id": 5, "user_id": 1}

    def test_row_to_refresh_token_none(self):
        assert _row_to_refresh_token(None) is None

    def test_row_to_refresh_token_valid(self):
        row = _make_row(id=3, user_id=2)
        assert _row_to_refresh_token(row) == {"id": 3, "user_id": 2}


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

class TestGetUserById:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        row = _make_row(id=1, email="a@b.com", full_name="Alice")
        conn = _make_conn(first_return=row)
        result = await get_user_by_id(conn, 1)
        assert result == {"id": 1, "email": "a@b.com", "full_name": "Alice"}

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = _make_conn(first_return=None)
        result = await get_user_by_id(conn, 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_user_id(self):
        conn = _make_conn(first_return=None)
        await get_user_by_id(conn, 42)
        _, kwargs = conn.execute.call_args
        # second positional arg is the params dict
        args = conn.execute.call_args[0]
        assert args[1] == {"id": 42}


# ---------------------------------------------------------------------------
# get_user_by_email
# ---------------------------------------------------------------------------

class TestGetUserByEmail:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        row = _make_row(id=2, email="bob@example.com")
        conn = _make_conn(first_return=row)
        result = await get_user_by_email(conn, "bob@example.com")
        assert result["email"] == "bob@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = _make_conn(first_return=None)
        result = await get_user_by_email(conn, "missing@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_email(self):
        conn = _make_conn(first_return=None)
        await get_user_by_email(conn, "test@example.com")
        args = conn.execute.call_args[0]
        assert args[1] == {"email": "test@example.com"}


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    @pytest.mark.asyncio
    async def test_returns_dict(self):
        row = _make_row(id=10, full_name="Alice", email="a@b.com",
                        password_hash="hash", is_active=True,
                        created_at=None, updated_at=None)
        conn = _make_conn(first_return=row)
        result = await create_user(
            conn,
            full_name="Alice",
            email="a@b.com",
            password_hash="hash",
        )
        assert result["id"] == 10
        assert result["email"] == "a@b.com"

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        row = _make_row(id=1, full_name="Bob", email="bob@test.com",
                        password_hash="h", is_active=True,
                        created_at=None, updated_at=None)
        conn = _make_conn(first_return=row)
        await create_user(conn, full_name="Bob", email="bob@test.com", password_hash="h")
        args = conn.execute.call_args[0]
        params = args[1]
        assert params["full_name"] == "Bob"
        assert params["email"] == "bob@test.com"
        assert params["password_hash"] == "h"


# ---------------------------------------------------------------------------
# update_user_password
# ---------------------------------------------------------------------------

class TestUpdateUserPassword:
    @pytest.mark.asyncio
    async def test_calls_execute(self):
        conn = _make_conn()
        await update_user_password(conn, 5, "new_hash")
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        conn = _make_conn()
        await update_user_password(conn, 5, "new_hash")
        args = conn.execute.call_args[0]
        params = args[1]
        assert params["id"] == 5
        assert params["password_hash"] == "new_hash"

    @pytest.mark.asyncio
    async def test_returns_none(self):
        conn = _make_conn()
        result = await update_user_password(conn, 5, "h")
        assert result is None


# ---------------------------------------------------------------------------
# create_password_reset
# ---------------------------------------------------------------------------

class TestCreatePasswordReset:
    @pytest.mark.asyncio
    async def test_returns_dict(self):
        row = _make_row(id=1, user_id=2, token_hash="th",
                        expires_at=EXPIRY, used_at=None, created_at=None)
        conn = _make_conn(first_return=row)
        result = await create_password_reset(
            conn, user_id=2, token_hash="th", expires_at=EXPIRY
        )
        assert result["token_hash"] == "th"

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        row = _make_row(id=1, user_id=3, token_hash="abc",
                        expires_at=EXPIRY, used_at=None, created_at=None)
        conn = _make_conn(first_return=row)
        await create_password_reset(conn, user_id=3, token_hash="abc", expires_at=EXPIRY)
        args = conn.execute.call_args[0]
        params = args[1]
        assert params["user_id"] == 3
        assert params["token_hash"] == "abc"
        assert params["expires_at"] == EXPIRY


# ---------------------------------------------------------------------------
# get_password_reset_by_token_hash
# ---------------------------------------------------------------------------

class TestGetPasswordResetByTokenHash:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        row = _make_row(id=7, user_id=1, token_hash="xyz",
                        expires_at=EXPIRY, used_at=None, created_at=None)
        conn = _make_conn(first_return=row)
        result = await get_password_reset_by_token_hash(conn, "xyz")
        assert result["token_hash"] == "xyz"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = _make_conn(first_return=None)
        result = await get_password_reset_by_token_hash(conn, "nope")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_token_hash_param(self):
        conn = _make_conn(first_return=None)
        await get_password_reset_by_token_hash(conn, "lookup_hash")
        args = conn.execute.call_args[0]
        assert args[1] == {"token_hash": "lookup_hash"}


# ---------------------------------------------------------------------------
# mark_password_reset_used
# ---------------------------------------------------------------------------

class TestMarkPasswordResetUsed:
    @pytest.mark.asyncio
    async def test_calls_execute(self):
        conn = _make_conn()
        await mark_password_reset_used(conn, 9)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_id(self):
        conn = _make_conn()
        await mark_password_reset_used(conn, 9)
        args = conn.execute.call_args[0]
        assert args[1] == {"id": 9}


# ---------------------------------------------------------------------------
# invalidate_password_resets_for_user
# ---------------------------------------------------------------------------

class TestInvalidatePasswordResetsForUser:
    @pytest.mark.asyncio
    async def test_calls_execute(self):
        conn = _make_conn()
        await invalidate_password_resets_for_user(conn, 3)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_user_id(self):
        conn = _make_conn()
        await invalidate_password_resets_for_user(conn, 3)
        args = conn.execute.call_args[0]
        assert args[1] == {"user_id": 3}


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------

class TestCreateRefreshToken:
    @pytest.mark.asyncio
    async def test_returns_dict(self):
        row = _make_row(id=11, user_id=2, token_hash="rth",
                        expires_at=EXPIRY, revoked_at=None,
                        remember_me=False, created_at=None)
        conn = _make_conn(first_return=row)
        result = await create_refresh_token(
            conn, user_id=2, token_hash="rth",
            expires_at=EXPIRY, remember_me=False
        )
        assert result["token_hash"] == "rth"

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        row = _make_row(id=1, user_id=5, token_hash="t",
                        expires_at=EXPIRY, revoked_at=None,
                        remember_me=True, created_at=None)
        conn = _make_conn(first_return=row)
        await create_refresh_token(
            conn, user_id=5, token_hash="t", expires_at=EXPIRY, remember_me=True
        )
        args = conn.execute.call_args[0]
        params = args[1]
        assert params["user_id"] == 5
        assert params["remember_me"] is True


# ---------------------------------------------------------------------------
# get_refresh_token_by_token_hash
# ---------------------------------------------------------------------------

class TestGetRefreshTokenByTokenHash:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        row = _make_row(id=20, user_id=1, token_hash="rh",
                        expires_at=EXPIRY, revoked_at=None,
                        remember_me=False, created_at=None)
        conn = _make_conn(first_return=row)
        result = await get_refresh_token_by_token_hash(conn, "rh")
        assert result["token_hash"] == "rh"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = _make_conn(first_return=None)
        result = await get_refresh_token_by_token_hash(conn, "missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_token_hash(self):
        conn = _make_conn(first_return=None)
        await get_refresh_token_by_token_hash(conn, "find_me")
        args = conn.execute.call_args[0]
        assert args[1] == {"token_hash": "find_me"}


# ---------------------------------------------------------------------------
# revoke_refresh_token
# ---------------------------------------------------------------------------

class TestRevokeRefreshToken:
    @pytest.mark.asyncio
    async def test_calls_execute(self):
        conn = _make_conn()
        await revoke_refresh_token(conn, 15)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_id(self):
        conn = _make_conn()
        await revoke_refresh_token(conn, 15)
        args = conn.execute.call_args[0]
        assert args[1] == {"id": 15}


# ---------------------------------------------------------------------------
# revoke_all_refresh_tokens_for_user
# ---------------------------------------------------------------------------

class TestRevokeAllRefreshTokensForUser:
    @pytest.mark.asyncio
    async def test_calls_execute(self):
        conn = _make_conn()
        await revoke_all_refresh_tokens_for_user(conn, 7)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_user_id(self):
        conn = _make_conn()
        await revoke_all_refresh_tokens_for_user(conn, 7)
        args = conn.execute.call_args[0]
        assert args[1] == {"user_id": 7}


# ---------------------------------------------------------------------------
# rotate_refresh_token
# ---------------------------------------------------------------------------

class TestRotateRefreshToken:
    @pytest.mark.asyncio
    async def test_calls_revoke_and_create(self):
        """
        rotate_refresh_token should:
          1. call revoke_refresh_token (one execute for UPDATE)
          2. call create_refresh_token (one execute for INSERT)
        total = 2 execute calls
        """
        new_row = _make_row(id=99, user_id=4, token_hash="new_hash",
                            expires_at=EXPIRY, revoked_at=None,
                            remember_me=False, created_at=None)
        # First execute (revoke) returns a generic result; second (create) returns new_row
        revoke_result = MagicMock()
        revoke_result.first.return_value = None
        create_result = MagicMock()
        create_result.first.return_value = new_row

        conn = AsyncMock()
        conn.execute = AsyncMock(side_effect=[revoke_result, create_result])

        result = await rotate_refresh_token(
            conn,
            old_token_id=50,
            user_id=4,
            new_token_hash="new_hash",
            expires_at=EXPIRY,
            remember_me=False,
        )
        assert conn.execute.await_count == 2
        assert result["token_hash"] == "new_hash"

    @pytest.mark.asyncio
    async def test_returns_new_token_dict(self):
        new_row = _make_row(id=100, user_id=8, token_hash="nt",
                            expires_at=EXPIRY, revoked_at=None,
                            remember_me=True, created_at=None)
        revoke_result = MagicMock()
        revoke_result.first.return_value = None
        create_result = MagicMock()
        create_result.first.return_value = new_row

        conn = AsyncMock()
        conn.execute = AsyncMock(side_effect=[revoke_result, create_result])

        result = await rotate_refresh_token(
            conn,
            old_token_id=1,
            user_id=8,
            new_token_hash="nt",
            expires_at=EXPIRY,
            remember_me=True,
        )
        assert result["remember_me"] is True
        assert result["id"] == 100
