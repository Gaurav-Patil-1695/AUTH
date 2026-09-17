"""Unit tests for forgot-password and reset-password flows."""
import hashlib
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Minimal app bootstrap (avoids real DB imports at module level)
# ---------------------------------------------------------------------------
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("REFRESH_TOKEN_REMEMBER_DAYS", "30")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # fast for tests
os.environ.setdefault("COOKIE_SECURE", "false")

from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest  # noqa: E402
from app.auth.service import AuthService, _hash_token  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(**kwargs):
    """Return a dict that supports attribute-style AND key-style access."""
    class Row(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)
    return Row(kwargs)


@asynccontextmanager
async def _fake_conn_ctx(conn):
    """Async context manager that yields a mock connection."""
    yield conn


def _patch_conn(conn):
    """Patch app.auth.service.get_connection to return *conn*."""
    return patch(
        "app.auth.service.get_connection",
        return_value=_fake_conn_ctx(conn),
    )


# ===========================================================================
# _hash_token
# ===========================================================================

class TestHashToken:
    def test_returns_sha256_hex(self):
        token = "hello"
        expected = hashlib.sha256(b"hello").hexdigest()
        assert _hash_token(token) == expected

    def test_different_inputs_produce_different_hashes(self):
        assert _hash_token("aaa") != _hash_token("bbb")

    def test_deterministic(self):
        assert _hash_token("x") == _hash_token("x")


# ===========================================================================
# AuthService.forgot_password  (also via forgotPassword alias)
# ===========================================================================

class TestForgotPassword:
    """Tests for AuthService.forgot_password / forgotPassword."""

    @pytest.fixture()
    def service(self):
        return AuthService()

    @pytest.fixture()
    def generic_message(self):
        return (
            "If an account with that email exists, a password reset link"
            " has been sent."
        )

    # ------------------------------------------------------------------
    # Happy path: active user found
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_known_email_returns_generic_message(self, service, generic_message):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=_make_row(id=42))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="user@example.com")
            result = await service.forgot_password(body)

        assert result.message == generic_message

    @pytest.mark.asyncio
    async def test_known_email_inserts_password_reset_row(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=_make_row(id=7))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="user@example.com")
            await service.forgot_password(body)

        conn.execute.assert_awaited_once()
        call_args = conn.execute.call_args
        sql = call_args[0][0]  # first positional arg
        assert "INSERT INTO password_resets" in sql

    @pytest.mark.asyncio
    async def test_known_email_passes_user_id_to_insert(self, service):
        user_id = 99
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=_make_row(id=user_id))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="user@example.com")
            await service.forgot_password(body)

        call_args = conn.execute.call_args[0]  # positional tuple
        # args: (sql, user_id, token_hash, expires_at)
        assert call_args[1] == user_id

    @pytest.mark.asyncio
    async def test_known_email_token_hash_is_sha256(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=_make_row(id=1))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="user@example.com")
            await service.forgot_password(body)

        call_args = conn.execute.call_args[0]
        token_hash = call_args[2]  # (sql, user_id, token_hash, expires_at)
        assert len(token_hash) == 64  # SHA-256 hex digest length

    @pytest.mark.asyncio
    async def test_known_email_expires_at_approx_one_hour(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=_make_row(id=1))
        conn.execute = AsyncMock()

        before = datetime.now(timezone.utc)
        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="user@example.com")
            await service.forgot_password(body)
        after = datetime.now(timezone.utc)

        call_args = conn.execute.call_args[0]
        expires_at = call_args[3]  # (sql, user_id, token_hash, expires_at)
        expected_min = before + timedelta(hours=1) - timedelta(seconds=2)
        expected_max = after + timedelta(hours=1) + timedelta(seconds=2)
        assert expected_min <= expires_at <= expected_max

    # ------------------------------------------------------------------
    # Unknown / inactive email — still returns generic message, no INSERT
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_unknown_email_returns_generic_message(self, service, generic_message):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="nobody@example.com")
            result = await service.forgot_password(body)

        assert result.message == generic_message

    @pytest.mark.asyncio
    async def test_unknown_email_does_not_insert(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="nobody@example.com")
            await service.forgot_password(body)

        conn.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_forgot_password_queries_active_users_only(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="user@example.com")
            await service.forgot_password(body)

        sql = conn.fetchrow.call_args[0][0]
        assert "is_active" in sql.lower() or "is_active = TRUE" in sql

    # ------------------------------------------------------------------
    # forgotPassword alias delegates to forgot_password
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_forgot_password_alias_works(self, service, generic_message):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=_make_row(id=5))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ForgotPasswordRequest(email="alias@example.com")
            result = await service.forgotPassword(body)

        assert result.message == generic_message


# ===========================================================================
# AuthService.reset_password  (also via resetPassword alias)
# ===========================================================================

class TestResetPassword:
    """Tests for AuthService.reset_password / resetPassword."""

    @pytest.fixture()
    def service(self):
        return AuthService()

    def _make_valid_reset_row(
        self,
        *,
        id: int = 1,
        user_id: int = 42,
        used_at=None,
        expires_at: datetime | None = None,
    ):
        if expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return _make_row(
            id=id,
            user_id=user_id,
            used_at=used_at,
            expires_at=expires_at,
        )

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_valid_token_returns_success_message(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=self._make_valid_reset_row())
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="goodtoken", password="newpassword1", confirmPassword="newpassword1")
            result = await service.reset_password(body)

        assert "reset successfully" in result.message.lower()

    @pytest.mark.asyncio
    async def test_valid_token_updates_password(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=self._make_valid_reset_row(user_id=7))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="tok", password="newpassword1", confirmPassword="newpassword1")
            await service.reset_password(body)

        # First execute call should be UPDATE users SET password_hash
        first_call_sql = conn.execute.call_args_list[0][0][0]
        assert "UPDATE users" in first_call_sql
        assert "password_hash" in first_call_sql

    @pytest.mark.asyncio
    async def test_valid_token_marks_reset_token_used(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=self._make_valid_reset_row(id=99))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="tok", password="newpassword1", confirmPassword="newpassword1")
            await service.reset_password(body)

        # Second execute call should mark used_at
        second_call_sql = conn.execute.call_args_list[1][0][0]
        assert "UPDATE password_resets" in second_call_sql
        assert "used_at" in second_call_sql
        # Correct id passed
        second_call_id = conn.execute.call_args_list[1][0][1]
        assert second_call_id == 99

    @pytest.mark.asyncio
    async def test_valid_token_revokes_refresh_tokens(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=self._make_valid_reset_row(user_id=42))
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="tok", password="newpassword1", confirmPassword="newpassword1")
            await service.reset_password(body)

        # Third execute call revokes refresh tokens
        third_call_sql = conn.execute.call_args_list[2][0][0]
        assert "refresh_tokens" in third_call_sql
        assert "revoked_at" in third_call_sql

    @pytest.mark.asyncio
    async def test_token_hashed_before_lookup(self, service):
        """The service must look up by SHA-256 hash, not raw token."""
        raw_token = "my-raw-token"
        expected_hash = _hash_token(raw_token)

        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=self._make_valid_reset_row())
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ResetPasswordRequest(token=raw_token, password="newpassword1", confirmPassword="newpassword1")
            await service.reset_password(body)

        lookup_hash = conn.fetchrow.call_args[0][1]
        assert lookup_hash == expected_hash

    # ------------------------------------------------------------------
    # Error: token not found
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_invalid_token_raises_400(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="bad", password="newpassword1", confirmPassword="newpassword1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_token_error_code(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="bad", password="newpassword1", confirmPassword="newpassword1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        detail = exc_info.value.detail
        assert detail["error"]["code"] == "INVALID_RESET_TOKEN"

    # ------------------------------------------------------------------
    # Error: token already used
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_used_token_raises_400(self, service):
        used_row = self._make_valid_reset_row(
            used_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=used_row)

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="used", password="newpassword1", confirmPassword="newpassword1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_used_token_error_code(self, service):
        used_row = self._make_valid_reset_row(
            used_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=used_row)

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="used", password="newpassword1", confirmPassword="newpassword1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        detail = exc_info.value.detail
        assert detail["error"]["code"] == "RESET_TOKEN_USED"

    # ------------------------------------------------------------------
    # Error: token expired
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_expired_token_raises_400(self, service):
        expired_row = self._make_valid_reset_row(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=expired_row)

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="expired", password="newpassword1", confirmPassword="newpassword1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_expired_token_error_code(self, service):
        expired_row = self._make_valid_reset_row(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=expired_row)

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="expired", password="newpassword1", confirmPassword="newpassword1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        detail = exc_info.value.detail
        assert detail["error"]["code"] == "RESET_TOKEN_EXPIRED"

    # ------------------------------------------------------------------
    # resetPassword alias delegates to reset_password
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_reset_password_alias_works(self, service):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=self._make_valid_reset_row())
        conn.execute = AsyncMock()

        with _patch_conn(conn):
            body = ResetPasswordRequest(token="tok", password="newpassword1", confirmPassword="newpassword1")
            result = await service.resetPassword(body)

        assert "reset successfully" in result.message.lower()


# ===========================================================================
# HTTP layer — router integration via TestClient
# ===========================================================================

class TestForgotPasswordRouter:
    """Integration-style tests for the /auth/forgot-password endpoint."""

    @pytest.fixture()
    def client(self):
        from fastapi import FastAPI
        from app.auth.router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture(autouse=True)
    def _patch_service(self):
        """Replace AuthService with a mock for router-level tests."""
        from app.auth import router as router_module

        mock_service = MagicMock(spec=AuthService)

        from app.auth.schemas import ForgotPasswordResponse
        mock_service.forgotPassword = AsyncMock(
            return_value=ForgotPasswordResponse(
                message=(
                    "If an account with that email exists, a password reset link"
                    " has been sent."
                )
            )
        )
        with patch.object(router_module, "get_auth_service", return_value=mock_service):
            self._mock_service = mock_service
            yield

    def test_forgot_password_status_202(self, client):
        response = client.post(
            "/auth/forgot-password",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 202

    def test_forgot_password_response_body(self, client):
        response = client.post(
            "/auth/forgot-password",
            json={"email": "user@example.com"},
        )
        data = response.json()
        assert "message" in data

    def test_forgot_password_invalid_email_422(self, client):
        response = client.post(
            "/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_forgot_password_missing_email_422(self, client):
        response = client.post(
            "/auth/forgot-password",
            json={},
        )
        assert response.status_code == 422


class TestResetPasswordRouter:
    """Integration-style tests for the /auth/reset-password endpoint."""

    @pytest.fixture()
    def client(self):
        from fastapi import FastAPI
        from app.auth.router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture(autouse=True)
    def _patch_service_ok(self):
        from app.auth import router as router_module
        from app.auth.schemas import ResetPasswordResponse

        mock_service = MagicMock(spec=AuthService)
        mock_service.resetPassword = AsyncMock(
            return_value=ResetPasswordResponse(
                message="Your password has been reset successfully."
            )
        )
        with patch.object(router_module, "get_auth_service", return_value=mock_service):
            self._mock_service = mock_service
            yield

    def test_reset_password_status_200(self, client):
        response = client.post(
            "/auth/reset-password",
            json={
                "token": "sometoken",
                "password": "newpassword1",
                "confirmPassword": "newpassword1",
            },
        )
        assert response.status_code == 200

    def test_reset_password_response_body(self, client):
        response = client.post(
            "/auth/reset-password",
            json={
                "token": "sometoken",
                "password": "newpassword1",
                "confirmPassword": "newpassword1",
            },
        )
        data = response.json()
        assert data["message"] == "Your password has been reset successfully."

    def test_reset_password_missing_token_422(self, client):
        response = client.post(
            "/auth/reset-password",
            json={"password": "newpassword1", "confirmPassword": "newpassword1"},
        )
        assert response.status_code == 422

    def test_reset_password_short_password_422(self, client):
        response = client.post(
            "/auth/reset-password",
            json={"token": "t", "password": "short", "confirmPassword": "short"},
        )
        assert response.status_code == 422
