"""Unit tests for the reset-password flow (work item: backend-resetPassword).

External I/O (database) is mocked via unittest.mock so no real DB is needed.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _make_reset_row(
    *,
    row_id: int = 1,
    user_id: int = 42,
    expires_at: datetime | None = None,
    used_at: datetime | None = None,
):
    """Return a dict-like object that mimics an asyncpg Record."""
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return {
        "id": row_id,
        "user_id": user_id,
        "expires_at": expires_at,
        "used_at": used_at,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def service():
    """Return a fresh AuthService instance (no DB)."""
    # Import here so env vars are read at import time with defaults.
    from app.auth.service import AuthService
    return AuthService()


# ---------------------------------------------------------------------------
# Helper: build a context-manager mock for get_connection
# ---------------------------------------------------------------------------

def _conn_ctx(conn_mock):
    """Wrap *conn_mock* in an async context-manager mock."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=conn_mock)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# ===========================================================================
# service.reset_password (and its alias resetPassword)
# ===========================================================================

class TestResetPassword:
    """Tests for AuthService.reset_password."""

    @pytest.mark.asyncio
    async def test_valid_token_resets_password(self, service):
        """Happy path: valid, unused, non-expired token."""
        raw_token = "valid-raw-token-abc123"
        reset_row = _make_reset_row()

        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=reset_row)
        conn.execute = AsyncMock()

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token=raw_token,
            password="newpassword1",
            confirmPassword="newpassword1",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            result = await service.reset_password(body)

        assert result.message == "Your password has been reset successfully."
        # Three UPDATE/INSERT statements must have been fired
        assert conn.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_token_hashed_before_db_lookup(self, service):
        """The service must look up the SHA-256 hash of the raw token, not the raw token."""
        raw_token = "some-random-token"
        expected_hash = _sha256(raw_token)

        reset_row = _make_reset_row()
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=reset_row)
        conn.execute = AsyncMock()

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token=raw_token,
            password="password123",
            confirmPassword="password123",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            await service.reset_password(body)

        # The first argument to fetchrow after the SQL string must be the hash
        call_args = conn.fetchrow.call_args
        assert call_args[0][1] == expected_hash

    @pytest.mark.asyncio
    async def test_invalid_token_raises_400(self, service):
        """Token not found in DB → 400 INVALID_RESET_TOKEN."""
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="nonexistent-token",
            password="password123",
            confirmPassword="password123",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_RESET_TOKEN"

    @pytest.mark.asyncio
    async def test_already_used_token_raises_400(self, service):
        """Token already consumed → 400 RESET_TOKEN_USED."""
        used_row = _make_reset_row(
            used_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=used_row)

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="used-token",
            password="password123",
            confirmPassword="password123",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "RESET_TOKEN_USED"

    @pytest.mark.asyncio
    async def test_expired_token_raises_400(self, service):
        """Token past expiry → 400 RESET_TOKEN_EXPIRED."""
        expired_row = _make_reset_row(
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=expired_row)

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="expired-token",
            password="password123",
            confirmPassword="password123",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "RESET_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_token_expiry_boundary_just_valid(self, service):
        """Token expiring exactly 1 second in the future should succeed."""
        row = _make_reset_row(
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=1)
        )
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        conn.execute = AsyncMock()

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="almost-expired",
            password="newpassword1",
            confirmPassword="newpassword1",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            result = await service.reset_password(body)

        assert result.message == "Your password has been reset successfully."

    @pytest.mark.asyncio
    async def test_refresh_tokens_revoked_after_reset(self, service):
        """All active refresh tokens for the user must be revoked."""
        user_id = 99
        row = _make_reset_row(user_id=user_id)

        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        conn.execute = AsyncMock()

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="good-token",
            password="newpassword1",
            confirmPassword="newpassword1",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            await service.reset_password(body)

        # Collect all SQL strings passed to execute()
        sql_calls = [call[0][0] for call in conn.execute.call_args_list]
        revoke_calls = [s for s in sql_calls if "revoked_at" in s and "refresh_tokens" in s]
        assert len(revoke_calls) >= 1, "Expected at least one refresh-token revocation query"

    @pytest.mark.asyncio
    async def test_reset_token_marked_used(self, service):
        """The password_resets row must be stamped with used_at."""
        reset_id = 7
        row = _make_reset_row(row_id=reset_id)

        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        conn.execute = AsyncMock()

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="mark-used-token",
            password="newpassword1",
            confirmPassword="newpassword1",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            await service.reset_password(body)

        # At least one execute call should reference password_resets + used_at
        sql_calls = [call[0][0] for call in conn.execute.call_args_list]
        mark_used = [
            s for s in sql_calls
            if "password_resets" in s and "used_at" in s
        ]
        assert len(mark_used) >= 1

    @pytest.mark.asyncio
    async def test_alias_resetPassword_delegates(self, service):
        """resetPassword (camelCase alias) must behave identically to reset_password."""
        row = _make_reset_row()
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        conn.execute = AsyncMock()

        from app.auth.schemas import ResetPasswordRequest

        body = ResetPasswordRequest(
            token="alias-test-token",
            password="newpassword1",
            confirmPassword="newpassword1",
        )

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            result = await service.resetPassword(body)

        assert result.message == "Your password has been reset successfully."


# ===========================================================================
# service.forgot_password (and alias)
# ===========================================================================

class TestForgotPassword:
    """Tests for AuthService.forgot_password."""

    @pytest.mark.asyncio
    async def test_existing_user_stores_token(self, service):
        """When the user exists, a token hash row must be inserted."""
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value={"id": 5})
        conn.execute = AsyncMock()

        from app.auth.schemas import ForgotPasswordRequest

        body = ForgotPasswordRequest(email="user@example.com")

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            result = await service.forgot_password(body)

        assert "password reset link" in result.message.lower() or "account with that email" in result.message
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_generic_message(self, service):
        """Unknown email must return the same generic response (no leakage)."""
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        from app.auth.schemas import ForgotPasswordRequest

        body = ForgotPasswordRequest(email="nobody@example.com")

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            result = await service.forgot_password(body)

        # Must NOT call execute (no DB write for unknown user)
        conn.execute.assert_not_called()
        assert result.message  # non-empty generic message

    @pytest.mark.asyncio
    async def test_alias_forgotPassword_delegates(self, service):
        """forgotPassword alias must behave identically."""
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value={"id": 3})
        conn.execute = AsyncMock()

        from app.auth.schemas import ForgotPasswordRequest

        body = ForgotPasswordRequest(email="a@b.com")

        with patch("app.auth.service.get_connection", return_value=_conn_ctx(conn)):
            result = await service.forgotPassword(body)

        assert result.message


# ===========================================================================
# Router integration via TestClient (no real DB)
# ===========================================================================

class TestResetPasswordRoute:
    """Integration smoke-tests through the FastAPI router."""

    @pytest.fixture(autouse=True)
    def _app(self):
        """Build a minimal app with only the auth router mounted."""
        from fastapi import FastAPI
        from app.auth.router import router

        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app, raise_server_exceptions=False)

    def _override_service(self, mock_service):
        from fastapi import FastAPI
        from app.auth.router import router, get_auth_service

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_auth_service] = lambda: mock_service
        return TestClient(app, raise_server_exceptions=True)

    def test_reset_password_200_on_success(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ResetPasswordResponse

        mock_svc = MagicMock(spec=AuthService)
        mock_svc.resetPassword = AsyncMock(
            return_value=ResetPasswordResponse(
                message="Your password has been reset successfully."
            )
        )
        client = self._override_service(mock_svc)

        resp = client.post(
            "/auth/reset-password",
            json={
                "token": "abc",
                "password": "newpassword1",
                "confirmPassword": "newpassword1",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Your password has been reset successfully."

    def test_reset_password_400_on_invalid_token(self):
        from app.auth.service import AuthService

        mock_svc = MagicMock(spec=AuthService)
        mock_svc.resetPassword = AsyncMock(
            side_effect=HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": {},
                    }
                },
            )
        )
        client = self._override_service(mock_svc)

        resp = client.post(
            "/auth/reset-password",
            json={
                "token": "bad",
                "password": "newpassword1",
                "confirmPassword": "newpassword1",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "INVALID_RESET_TOKEN"

    def test_forgot_password_202_on_success(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ForgotPasswordResponse

        mock_svc = MagicMock(spec=AuthService)
        mock_svc.forgotPassword = AsyncMock(
            return_value=ForgotPasswordResponse(
                message="If an account with that email exists, a password reset link has been sent."
            )
        )
        client = self._override_service(mock_svc)

        resp = client.post(
            "/auth/forgot-password",
            json={"email": "user@example.com"},
        )
        assert resp.status_code == 202
        assert "password reset link" in resp.json()["message"]


# ===========================================================================
# _hash_token helper
# ===========================================================================

class TestHashToken:
    def test_known_value(self):
        from app.auth.service import _hash_token

        raw = "hello"
        expected = hashlib.sha256(b"hello").hexdigest()
        assert _hash_token(raw) == expected

    def test_different_inputs_produce_different_hashes(self):
        from app.auth.service import _hash_token

        assert _hash_token("token-a") != _hash_token("token-b")

    def test_deterministic(self):
        from app.auth.service import _hash_token

        val = "some-token"
        assert _hash_token(val) == _hash_token(val)

    def test_returns_hex_string_of_correct_length(self):
        from app.auth.service import _hash_token

        result = _hash_token("anything")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 → 32 bytes → 64 hex chars


# ===========================================================================
# Schemas
# ===========================================================================

class TestResetPasswordRequest:
    def test_valid_schema(self):
        from app.auth.schemas import ResetPasswordRequest

        req = ResetPasswordRequest(
            token="tok",
            password="password123",
            confirmPassword="password123",
        )
        assert req.token == "tok"
        assert req.password == "password123"

    def test_password_too_short_raises(self):
        from app.auth.schemas import ResetPasswordRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                token="tok",
                password="short",
                confirmPassword="short",
            )

    def test_token_required(self):
        from app.auth.schemas import ResetPasswordRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                password="password123",
                confirmPassword="password123",
            )


class TestForgotPasswordRequest:
    def test_valid_email(self):
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="a@b.com")
        assert req.email == "a@b.com"

    def test_invalid_email_raises(self):
        from app.auth.schemas import ForgotPasswordRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email="not-an-email")


class TestResetPasswordResponse:
    def test_message_field(self):
        from app.auth.schemas import ResetPasswordResponse

        resp = ResetPasswordResponse(message="done")
        assert resp.message == "done"


class TestForgotPasswordResponse:
    def test_message_field(self):
        from app.auth.schemas import ForgotPasswordResponse

        resp = ForgotPasswordResponse(message="check your inbox")
        assert resp.message == "check your inbox"
