"""Unit tests for auth router and service.

External I/O (get_connection) is mocked so no real DB or network is needed.
"""
import hashlib
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Helpers / constants mirrored from the module under test
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("JWT_SECRET", "change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
BCRYPT_ROUNDS = 4  # fewer rounds to keep tests fast


def _make_access_token(user_id: int, email: str, expired: bool = False) -> str:
    delta = timedelta(minutes=-1) if expired else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + delta
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


# ---------------------------------------------------------------------------
# Fake async context-manager connection factory
# ---------------------------------------------------------------------------

def make_fake_conn(**method_returns: Any):
    """Return a fake asyncpg-like connection object."""
    conn = MagicMock()
    conn.fetchrow = AsyncMock(side_effect=method_returns.get("fetchrow_side_effect",
                              [method_returns.get("fetchrow")]))
    conn.execute = AsyncMock(return_value=None)
    return conn


@asynccontextmanager
async def fake_get_connection_ctx(conn):
    yield conn


def patch_get_connection(conn):
    """Return a context-manager patch that yields *conn*."""
    @asynccontextmanager
    async def _ctx():
        yield conn
    return patch("app.auth.service.get_connection", return_value=_ctx())


# ---------------------------------------------------------------------------
# Schemas smoke-tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_register_request_alias(self):
        from app.auth.schemas import RegisterRequest
        req = RegisterRequest(
            fullName="Alice",
            email="alice@example.com",
            password="secret123",
            confirmPassword="secret123",
            acceptTerms=True,
        )
        assert req.full_name == "Alice"
        assert req.accept_terms is True

    def test_register_response_alias(self):
        from app.auth.schemas import RegisterResponse
        resp = RegisterResponse(id=1, fullName="Alice", email="alice@example.com", createdAt="2024-01-01T00:00:00")
        assert resp.full_name == "Alice"
        assert resp.created_at == "2024-01-01T00:00:00"

    def test_login_request_defaults(self):
        from app.auth.schemas import LoginRequest
        req = LoginRequest(email="alice@example.com", password="secret123")
        assert req.remember_me is False

    def test_login_response(self):
        from app.auth.schemas import LoginResponse
        r = LoginResponse(accessToken="tok", tokenType="bearer", user={"id": 1})
        assert r.access_token == "tok"

    def test_forgot_password_response(self):
        from app.auth.schemas import ForgotPasswordResponse
        r = ForgotPasswordResponse(message="ok")
        assert r.message == "ok"

    def test_reset_password_request(self):
        from app.auth.schemas import ResetPasswordRequest
        r = ResetPasswordRequest(token="abc", password="newpass1", confirmPassword="newpass1")
        assert r.token == "abc"

    def test_me_response(self):
        from app.auth.schemas import MeResponse
        r = MeResponse(id=5, fullName="Bob", email="bob@example.com", createdAt="2024-01-01T00:00:00")
        assert r.full_name == "Bob"

    def test_logout_response(self):
        from app.auth.schemas import LogoutResponse
        r = LogoutResponse(message="Logged out successfully.")
        assert r.message == "Logged out successfully."

    def test_refresh_response(self):
        from app.auth.schemas import RefreshResponse
        r = RefreshResponse(accessToken="t", tokenType="bearer", user={"id": 2})
        assert r.access_token == "t"


# ---------------------------------------------------------------------------
# Service tests — register
# ---------------------------------------------------------------------------

class TestAuthServiceRegister:
    @pytest.mark.asyncio
    async def test_register_success(self):
        from app.auth.service import AuthService
        from app.auth.schemas import RegisterRequest

        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        inserted_row = {"id": 1, "full_name": "Alice", "email": "alice@example.com", "created_at": created_at}

        conn = MagicMock()
        # first fetchrow → no existing user; second fetchrow → inserted row
        conn.fetchrow = AsyncMock(side_effect=[None, inserted_row])
        conn.execute = AsyncMock(return_value=None)

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = RegisterRequest(
                fullName="Alice",
                email="alice@example.com",
                password="secret123",
                confirmPassword="secret123",
                acceptTerms=True,
            )
            resp = await service.register(body)

        assert resp.id == 1
        assert resp.email == "alice@example.com"
        assert resp.full_name == "Alice"
        assert "2024" in resp.created_at

    @pytest.mark.asyncio
    async def test_register_email_taken(self):
        from app.auth.service import AuthService
        from app.auth.schemas import RegisterRequest

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value={"id": 99})
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = RegisterRequest(
                fullName="Alice",
                email="alice@example.com",
                password="secret123",
                confirmPassword="secret123",
                acceptTerms=True,
            )
            with pytest.raises(HTTPException) as exc_info:
                await service.register(body)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"]["code"] == "EMAIL_TAKEN"


# ---------------------------------------------------------------------------
# Service tests — login
# ---------------------------------------------------------------------------

class TestAuthServiceLogin:
    @pytest.mark.asyncio
    async def test_login_success(self):
        from app.auth.service import AuthService
        from app.auth.schemas import LoginRequest

        pw_hash = _bcrypt_hash("secret123")
        user_row = {
            "id": 1,
            "full_name": "Alice",
            "email": "alice@example.com",
            "password_hash": pw_hash,
            "is_active": True,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=user_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        response = MagicMock()
        response.set_cookie = MagicMock()

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = LoginRequest(email="alice@example.com", password="secret123")
            result = await service.login(body, response)

        assert result.access_token
        assert result.token_type == "bearer"
        assert result.user["email"] == "alice@example.com"
        response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        from app.auth.service import AuthService
        from app.auth.schemas import LoginRequest

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        response = MagicMock()
        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = LoginRequest(email="nobody@example.com", password="secret123")
            with pytest.raises(HTTPException) as exc_info:
                await service.login(body, response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        from app.auth.service import AuthService
        from app.auth.schemas import LoginRequest

        pw_hash = _bcrypt_hash("correct_password")
        user_row = {
            "id": 1,
            "full_name": "Alice",
            "email": "alice@example.com",
            "password_hash": pw_hash,
            "is_active": True,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=user_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        response = MagicMock()
        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = LoginRequest(email="alice@example.com", password="wrong_password")
            with pytest.raises(HTTPException) as exc_info:
                await service.login(body, response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_inactive_account(self):
        from app.auth.service import AuthService
        from app.auth.schemas import LoginRequest

        pw_hash = _bcrypt_hash("secret123")
        user_row = {
            "id": 1,
            "full_name": "Alice",
            "email": "alice@example.com",
            "password_hash": pw_hash,
            "is_active": False,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=user_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        response = MagicMock()
        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = LoginRequest(email="alice@example.com", password="secret123")
            with pytest.raises(HTTPException) as exc_info:
                await service.login(body, response)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "ACCOUNT_INACTIVE"

    @pytest.mark.asyncio
    async def test_login_remember_me_sets_longer_cookie(self):
        from app.auth.service import AuthService
        from app.auth.schemas import LoginRequest
        import app.auth.service as svc_module

        pw_hash = _bcrypt_hash("secret123")
        user_row = {
            "id": 1,
            "full_name": "Alice",
            "email": "alice@example.com",
            "password_hash": pw_hash,
            "is_active": True,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=user_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        response = MagicMock()
        response.set_cookie = MagicMock()

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = LoginRequest(email="alice@example.com", password="secret123", rememberMe=True)
            await service.login(body, response)

        call_kwargs = response.set_cookie.call_args
        # max_age should be REFRESH_TOKEN_REMEMBER_DAYS * 86400
        expected_max_age = svc_module.REFRESH_TOKEN_REMEMBER_DAYS * 86400
        assert call_kwargs.kwargs["max_age"] == expected_max_age


# ---------------------------------------------------------------------------
# Service tests — forgot_password / forgotPassword alias
# ---------------------------------------------------------------------------

class TestAuthServiceForgotPassword:
    @pytest.mark.asyncio
    async def test_forgot_password_user_not_found_returns_generic(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ForgotPasswordRequest

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            resp = await service.forgot_password(ForgotPasswordRequest(email="ghost@example.com"))

        assert "email exists" in resp.message
        conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_forgot_password_user_found_inserts_token(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ForgotPasswordRequest

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value={"id": 7})
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            resp = await service.forgot_password(ForgotPasswordRequest(email="alice@example.com"))

        assert "email exists" in resp.message
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_forgot_password_alias_calls_forgot_password(self):
        """forgotPassword is an alias for forgot_password."""
        from app.auth.service import AuthService
        from app.auth.schemas import ForgotPasswordRequest

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            resp = await service.forgotPassword(ForgotPasswordRequest(email="ghost@example.com"))

        assert resp.message  # generic message returned


# ---------------------------------------------------------------------------
# Service tests — reset_password / resetPassword alias
# ---------------------------------------------------------------------------

class TestAuthServiceResetPassword:
    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ResetPasswordRequest

        raw_token = "valid_token"
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        reset_row = {
            "id": 10,
            "user_id": 1,
            "expires_at": future,
            "used_at": None,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=reset_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = ResetPasswordRequest(token=raw_token, password="newpass1", confirmPassword="newpass1")
            resp = await service.reset_password(body)

        assert "reset successfully" in resp.message
        assert conn.execute.call_count == 3  # update users, update reset, revoke refresh tokens

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ResetPasswordRequest

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = ResetPasswordRequest(token="bad", password="newpass1", confirmPassword="newpass1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_RESET_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_password_used_token(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ResetPasswordRequest

        used_row = {
            "id": 10,
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used_at": datetime.now(timezone.utc) - timedelta(minutes=1),
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=used_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = ResetPasswordRequest(token="used", password="newpass1", confirmPassword="newpass1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "RESET_TOKEN_USED"

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ResetPasswordRequest

        expired_row = {
            "id": 10,
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) - timedelta(hours=2),
            "used_at": None,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=expired_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = ResetPasswordRequest(token="expired", password="newpass1", confirmPassword="newpass1")
            with pytest.raises(HTTPException) as exc_info:
                await service.reset_password(body)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "RESET_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_reset_password_alias(self):
        from app.auth.service import AuthService
        from app.auth.schemas import ResetPasswordRequest

        future = datetime.now(timezone.utc) + timedelta(hours=1)
        reset_row = {"id": 10, "user_id": 1, "expires_at": future, "used_at": None}

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=reset_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            body = ResetPasswordRequest(token="valid", password="newpass1", confirmPassword="newpass1")
            resp = await service.resetPassword(body)

        assert "reset successfully" in resp.message


# ---------------------------------------------------------------------------
# Service tests — me
# ---------------------------------------------------------------------------

class TestAuthServiceMe:
    @pytest.mark.asyncio
    async def test_me_no_credentials(self):
        from app.auth.service import AuthService

        service = AuthService()
        with pytest.raises(HTTPException) as exc_info:
            await service.me(None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_me_expired_token(self):
        from app.auth.service import AuthService

        token = _make_access_token(1, "alice@example.com", expired=True)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        service = AuthService()
        with pytest.raises(HTTPException) as exc_info:
            await service.me(creds)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_me_invalid_token(self):
        from app.auth.service import AuthService

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.jwt")

        service = AuthService()
        with pytest.raises(HTTPException) as exc_info:
            await service.me(creds)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_me_user_not_found(self):
        from app.auth.service import AuthService

        token = _make_access_token(99, "ghost@example.com")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=None)

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            with pytest.raises(HTTPException) as exc_info:
                await service.me(creds)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_me_inactive_user(self):
        from app.auth.service import AuthService

        token = _make_access_token(1, "alice@example.com")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        user_row = {
            "id": 1,
            "full_name": "Alice",
            "email": "alice@example.com",
            "is_active": False,
            "created_at": created_at,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=user_row)

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            with pytest.raises(HTTPException) as exc_info:
                await service.me(creds)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_me_success(self):
        from app.auth.service import AuthService

        token = _make_access_token(1, "alice@example.com")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        user_row = {
            "id": 1,
            "full_name": "Alice",
            "email": "alice@example.com",
            "is_active": True,
            "created_at": created_at,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=user_row)

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            resp = await service.me(creds)

        assert resp.id == 1
        assert resp.email == "alice@example.com"
        assert resp.full_name == "Alice"


# ---------------------------------------------------------------------------
# Service tests — logout
# ---------------------------------------------------------------------------

class TestAuthServiceLogout:
    @pytest.mark.asyncio
    async def test_logout_with_cookie_revokes_token(self):
        from app.auth.service import AuthService

        raw_refresh = "some_refresh_token"

        conn = MagicMock()
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/logout",
            "query_string": b"",
            "headers": [(b"cookie", f"refresh_token={raw_refresh}".encode())],
        }
        request = Request(scope)
        response = MagicMock()
        response.delete_cookie = MagicMock()

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            resp = await service.logout(request, response, None)

        conn.execute.assert_called_once()
        response.delete_cookie.assert_called_once()
        assert resp.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_without_cookie_clears_cookie(self):
        from app.auth.service import AuthService

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/logout",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        response = MagicMock()
        response.delete_cookie = MagicMock()

        service = AuthService()
        resp = await service.logout(request, response, None)

        response.delete_cookie.assert_called_once()
        assert resp.message == "Logged out successfully."


# ---------------------------------------------------------------------------
# Service tests — refresh
# ---------------------------------------------------------------------------

class TestAuthServiceRefresh:
    @pytest.mark.asyncio
    async def test_refresh_no_cookie_raises(self):
        from app.auth.service import AuthService

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        response = MagicMock()

        service = AuthService()
        with pytest.raises(HTTPException) as exc_info:
            await service.refresh(request, response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_raises(self):
        from app.auth.service import AuthService

        raw_refresh = "unknown_token"
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "query_string": b"",
            "headers": [(b"cookie", f"refresh_token={raw_refresh}".encode())],
        }
        request = Request(scope)
        response = MagicMock()

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=None)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            with pytest.raises(HTTPException) as exc_info:
                await service.refresh(request, response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_revoked_token_raises_and_revokes_all(self):
        from app.auth.service import AuthService

        raw_refresh = "revoked_token"
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "query_string": b"",
            "headers": [(b"cookie", f"refresh_token={raw_refresh}".encode())],
        }
        request = Request(scope)
        response = MagicMock()
        response.delete_cookie = MagicMock()

        token_row = {
            "id": 5,
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "revoked_at": datetime.now(timezone.utc) - timedelta(minutes=1),
            "remember_me": False,
            "email": "alice@example.com",
            "full_name": "Alice",
            "is_active": True,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=token_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            with pytest.raises(HTTPException) as exc_info:
                await service.refresh(request, response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "REFRESH_TOKEN_REUSE"
        # All tokens for user should be revoked
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_expired_token_raises(self):
        from app.auth.service import AuthService

        raw_refresh = "expired_refresh"
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "query_string": b"",
            "headers": [(b"cookie", f"refresh_token={raw_refresh}".encode())],
        }
        request = Request(scope)
        response = MagicMock()

        token_row = {
            "id": 5,
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
            "revoked_at": None,
            "remember_me": False,
            "email": "alice@example.com",
            "full_name": "Alice",
            "is_active": True,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=token_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            with pytest.raises(HTTPException) as exc_info:
                await service.refresh(request, response)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "REFRESH_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_refresh_inactive_user_raises(self):
        from app.auth.service import AuthService

        raw_refresh = "active_token"
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "query_string": b"",
            "headers": [(b"cookie", f"refresh_token={raw_refresh}".encode())],
        }
        request = Request(scope)
        response = MagicMock()

        token_row = {
            "id": 5,
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "revoked_at": None,
            "remember_me": False,
            "email": "alice@example.com",
            "full_name": "Alice",
            "is_active": False,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=token_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            with pytest.raises(HTTPException) as exc_info:
                await service.refresh(request, response)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "ACCOUNT_INACTIVE"

    @pytest.mark.asyncio
    async def test_refresh_success_rotates_token(self):
        from app.auth.service import AuthService

        raw_refresh = "valid_refresh"
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "query_string": b"",
            "headers": [(b"cookie", f"refresh_token={raw_refresh}".encode())],
        }
        request = Request(scope)
        response = MagicMock()
        response.set_cookie = MagicMock()

        token_row = {
            "id": 5,
            "user_id": 1,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "revoked_at": None,
            "remember_me": False,
            "email": "alice@example.com",
            "full_name": "Alice",
            "is_active": True,
        }

        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value=token_row)
        conn.execute = AsyncMock()

        @asynccontextmanager
        async def _fake_conn():
            yield conn

        with patch("app.auth.service.get_connection", return_value=_fake_conn()):
            service = AuthService()
            resp = await service.refresh(request, response)

        assert resp.access_token
        assert resp.token_type == "bearer"
        assert resp.user["email"] == "alice@example.com"
        # old token revoked + new token inserted = 2 execute calls
        assert conn.execute.call_count == 2
        response.set_cookie.assert_called_once()


# ---------------------------------------------------------------------------
# Private helper function unit tests
# ---------------------------------------------------------------------------

class TestPrivateHelpers:
    def test_hash_token_deterministic(self):
        from app.auth.service import _hash_token
        h1 = _hash_token("abc")
        h2 = _hash_token("abc")
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex

    def test_hash_token_different_inputs(self):
        from app.auth.service import _hash_token
        assert _hash_token("a") != _hash_token("b")

    def test_generate_access_token_decodable(self):
        from app.auth.service import _generate_access_token
        token = _generate_access_token(42, "user@example.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "42"
        assert payload["email"] == "user@example.com"

    def test_generate_refresh_token_is_string(self):
        from app.auth.service import _generate_refresh_token
        t = _generate_refresh_token()
        assert isinstance(t, str)
        assert len(t) == 64  # sha256 hex of 64 random bytes

    def test_generate_refresh_token_is_random(self):
        from app.auth.service import _generate_refresh_token
        tokens = {_generate_refresh_token() for _ in range(10)}
        assert len(tokens) == 10  # all unique

    def test_set_refresh_cookie_remember_me(self):
        from app.auth.service import _set_refresh_cookie, REFRESH_TOKEN_REMEMBER_DAYS
        response = MagicMock()
        response.set_cookie = MagicMock()
        _set_refresh_cookie(response, "tok", remember_me=True)
        call_kwargs = response.set_cookie.call_args.kwargs
        assert call_kwargs["max_age"] == REFRESH_TOKEN_REMEMBER_DAYS * 86400

    def test_set_refresh_cookie_no_remember(self):
        from app.auth.service import _set_refresh_cookie, REFRESH_TOKEN_EXPIRE_DAYS
        response = MagicMock()
        response.set_cookie = MagicMock()
        _set_refresh_cookie(response, "tok", remember_me=False)
        call_kwargs = response.set_cookie.call_args.kwargs
        assert call_kwargs["max_age"] == REFRESH_TOKEN_EXPIRE_DAYS * 86400

    def test_clear_refresh_cookie(self):
        from app.auth.service import _clear_refresh_cookie
        response = MagicMock()
        response.delete_cookie = MagicMock()
        _clear_refresh_cookie(response)
        response.delete_cookie.assert_called_once_with(key="refresh_token", path="/")


# ---------------------------------------------------------------------------
# Router integration tests via TestClient
# ---------------------------------------------------------------------------

class TestRouterEndpoints:
    """Light-weight router smoke tests — service is fully mocked."""

    def _make_app(self):
        from fastapi import FastAPI
        from app.auth.router import router
        app = FastAPI()
        app.include_router(router)
        return app

    def test_register_endpoint_calls_service(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import RegisterResponse

        fake_resp = RegisterResponse(
            id=1,
            fullName="Alice",
            email="alice@example.com",
            createdAt="2024-01-01T00:00:00",
        )

        mock_service = MagicMock()
        mock_service.register = AsyncMock(return_value=fake_resp)
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app)
        payload = {
            "fullName": "Alice",
            "email": "alice@example.com",
            "password": "secret123",
            "confirmPassword": "secret123",
            "acceptTerms": True,
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "alice@example.com"

    def test_login_endpoint_calls_service(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import LoginResponse

        fake_resp = LoginResponse(
            accessToken="tok",
            tokenType="bearer",
            user={"id": 1, "fullName": "Alice", "email": "alice@example.com"},
        )

        mock_service = MagicMock()
        mock_service.login = AsyncMock(return_value=fake_resp)
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app)
        resp = client.post("/auth/login", json={"email": "alice@example.com", "password": "secret123"})
        assert resp.status_code == 200
        assert resp.json()["accessToken"] == "tok"

    def test_forgot_password_endpoint(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import ForgotPasswordResponse

        fake_resp = ForgotPasswordResponse(message="If an account with that email exists, a password reset link has been sent.")
        mock_service = MagicMock()
        mock_service.forgotPassword = AsyncMock(return_value=fake_resp)
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app)
        resp = client.post("/auth/forgot-password", json={"email": "alice@example.com"})
        assert resp.status_code == 202

    def test_reset_password_endpoint(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import ResetPasswordResponse

        fake_resp = ResetPasswordResponse(message="Your password has been reset successfully.")
        mock_service = MagicMock()
        mock_service.resetPassword = AsyncMock(return_value=fake_resp)
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app)
        resp = client.post("/auth/reset-password", json={"token": "t", "password": "newpass1", "confirmPassword": "newpass1"})
        assert resp.status_code == 200

    def test_me_endpoint_no_auth_header(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import MeResponse

        mock_service = MagicMock()
        mock_service.me = AsyncMock(
            side_effect=HTTPException(
                status_code=401,
                detail={"error": {"code": "MISSING_TOKEN", "message": "Authentication required.", "details": {}}},
            )
        )
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_logout_endpoint(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import LogoutResponse

        fake_resp = LogoutResponse(message="Logged out successfully.")
        mock_service = MagicMock()
        mock_service.logout = AsyncMock(return_value=fake_resp)
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app)
        resp = client.post("/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully."

    def test_refresh_endpoint(self):
        app = self._make_app()
        from app.auth.router import get_auth_service
        from app.auth.schemas import RefreshResponse

        fake_resp = RefreshResponse(
            accessToken="new_tok",
            tokenType="bearer",
            user={"id": 1, "fullName": "Alice", "email": "alice@example.com"},
        )
        mock_service = MagicMock()
        mock_service.refresh = AsyncMock(return_value=fake_resp)
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        client = TestClient(app)
        resp = client.post("/auth/refresh")
        assert resp.status_code == 200
        assert resp.json()["accessToken"] == "new_tok"
