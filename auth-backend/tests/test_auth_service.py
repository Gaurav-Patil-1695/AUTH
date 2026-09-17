"""Unit tests for app.auth.service and app.auth.router (via TestClient).

External I/O (database via get_connection) is mocked; the module under test is
never patched itself.
"""
import hashlib
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from starlette.responses import Response
from starlette.requests import Request

# ── helpers to build fake DB rows ────────────────────────────────────────────

def _make_row(**kw):
    """Return a dict-like object whose keys are accessible via []."""
    return kw


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _pw_hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=4)).decode()


# ── make a fake async context-manager connection ─────────────────────────────

def _make_conn(fetchrow_return=None, execute_return=None):
    conn = AsyncMock()
    if isinstance(fetchrow_return, list):
        conn.fetchrow.side_effect = fetchrow_return
    else:
        conn.fetchrow.return_value = fetchrow_return
    conn.execute.return_value = execute_return
    return conn


@asynccontextmanager
async def _ctx(conn):
    yield conn


def _patch_conn(conn):
    """Return a patch for app.auth.service.get_connection that yields `conn`."""
    return patch("app.auth.service.get_connection", return_value=_ctx(conn))


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def service():
    from app.auth.service import AuthService
    return AuthService()


@pytest.fixture()
def client():
    """TestClient wrapping the full FastAPI app (router wired in)."""
    from fastapi import FastAPI
    from app.auth.router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────────────────────
# Helper schemas
# ─────────────────────────────────────────────────────────────────────────────

from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)


def _register_body(**kw):
    defaults = dict(
        fullName="Jane Doe",
        email="jane@example.com",
        password="password123",
        confirmPassword="password123",
        acceptTerms=True,
    )
    defaults.update(kw)
    return RegisterRequest(**defaults)


def _login_body(**kw):
    defaults = dict(email="jane@example.com", password="password123")
    defaults.update(kw)
    return LoginRequest(**defaults)


# ═════════════════════════════════════════════════════════════════════════════
# Pure-function / helper tests
# ═════════════════════════════════════════════════════════════════════════════

class TestHelpers:
    def test_hash_token_is_deterministic(self):
        from app.auth.service import _hash_token
        assert _hash_token("abc") == _hash_token("abc")

    def test_hash_token_differs_for_different_inputs(self):
        from app.auth.service import _hash_token
        assert _hash_token("abc") != _hash_token("xyz")

    def test_hash_token_is_sha256_hex(self):
        from app.auth.service import _hash_token
        result = _hash_token("test")
        assert len(result) == 64
        int(result, 16)  # must be valid hex

    def test_generate_access_token_decodes(self):
        from app.auth.service import _generate_access_token, SECRET_KEY, ALGORITHM
        token = _generate_access_token(42, "u@example.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "42"
        assert payload["email"] == "u@example.com"
        assert "exp" in payload
        assert "iat" in payload

    def test_generate_refresh_token_is_64_hex_chars(self):
        from app.auth.service import _generate_refresh_token
        tok = _generate_refresh_token()
        assert len(tok) == 64
        int(tok, 16)

    def test_generate_refresh_token_is_random(self):
        from app.auth.service import _generate_refresh_token
        assert _generate_refresh_token() != _generate_refresh_token()

    def test_set_refresh_cookie_remember_me_true(self):
        from app.auth.service import (
            _set_refresh_cookie,
            REFRESH_TOKEN_REMEMBER_DAYS,
            COOKIE_NAME,
        )
        resp = MagicMock()
        _set_refresh_cookie(resp, "tok", True)
        resp.set_cookie.assert_called_once()
        call_kw = resp.set_cookie.call_args.kwargs
        assert call_kw["key"] == COOKIE_NAME
        assert call_kw["value"] == "tok"
        assert call_kw["max_age"] == REFRESH_TOKEN_REMEMBER_DAYS * 86400
        assert call_kw["httponly"] is True

    def test_set_refresh_cookie_remember_me_false(self):
        from app.auth.service import (
            _set_refresh_cookie,
            REFRESH_TOKEN_EXPIRE_DAYS,
        )
        resp = MagicMock()
        _set_refresh_cookie(resp, "tok", False)
        call_kw = resp.set_cookie.call_args.kwargs
        assert call_kw["max_age"] == REFRESH_TOKEN_EXPIRE_DAYS * 86400

    def test_clear_refresh_cookie(self):
        from app.auth.service import _clear_refresh_cookie, COOKIE_NAME
        resp = MagicMock()
        _clear_refresh_cookie(resp)
        resp.delete_cookie.assert_called_once_with(key=COOKIE_NAME, path="/")


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.register
# ═════════════════════════════════════════════════════════════════════════════

class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, service):
        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        row = _make_row(id=1, full_name="Jane Doe", email="jane@example.com", created_at=created_at)
        conn = _make_conn(fetchrow_return=[None, row])  # first=existing check, second=insert
        with _patch_conn(conn):
            resp = await service.register(_register_body())
        assert resp.id == 1
        assert resp.fullName == "Jane Doe"
        assert resp.email == "jane@example.com"
        assert "2024" in resp.createdAt

    @pytest.mark.asyncio
    async def test_register_email_taken(self, service):
        existing = _make_row(id=99)
        conn = _make_conn(fetchrow_return=existing)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.register(_register_body())
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"]["code"] == "EMAIL_TAKEN"


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.login
# ═════════════════════════════════════════════════════════════════════════════

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, service):
        pw_hash = _pw_hash("password123")
        row = _make_row(
            id=1,
            full_name="Jane",
            email="jane@example.com",
            password_hash=pw_hash,
            is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        response = MagicMock(spec=Response)
        with _patch_conn(conn):
            result = await service.login(_login_body(), response)
        assert result.tokenType == "bearer"
        assert result.accessToken
        assert result.user["email"] == "jane@example.com"
        response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, service):
        conn = _make_conn(fetchrow_return=None)
        response = MagicMock(spec=Response)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.login(_login_body(), response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, service):
        pw_hash = _pw_hash("correct_password")
        row = _make_row(
            id=1,
            full_name="Jane",
            email="jane@example.com",
            password_hash=pw_hash,
            is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        response = MagicMock(spec=Response)
        body = _login_body(password="wrong_password")
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.login(body, response)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_account(self, service):
        pw_hash = _pw_hash("password123")
        row = _make_row(
            id=1,
            full_name="Jane",
            email="jane@example.com",
            password_hash=pw_hash,
            is_active=False,
        )
        conn = _make_conn(fetchrow_return=row)
        response = MagicMock(spec=Response)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.login(_login_body(), response)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "ACCOUNT_INACTIVE"

    @pytest.mark.asyncio
    async def test_login_remember_me_true(self, service):
        from app.auth.service import REFRESH_TOKEN_REMEMBER_DAYS
        pw_hash = _pw_hash("password123")
        row = _make_row(
            id=1,
            full_name="Jane",
            email="jane@example.com",
            password_hash=pw_hash,
            is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        response = MagicMock(spec=Response)
        body = _login_body(rememberMe=True)
        with _patch_conn(conn):
            await service.login(body, response)
        call_kw = response.set_cookie.call_args.kwargs
        assert call_kw["max_age"] == REFRESH_TOKEN_REMEMBER_DAYS * 86400


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.forgot_password / forgotPassword
# ═════════════════════════════════════════════════════════════════════════════

class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_returns_generic_when_email_found(self, service):
        row = _make_row(id=5)
        conn = _make_conn(fetchrow_return=row)
        body = ForgotPasswordRequest(email="jane@example.com")
        with _patch_conn(conn):
            result = await service.forgot_password(body)
        assert "email exists" in result.message or "sent" in result.message

    @pytest.mark.asyncio
    async def test_returns_generic_when_email_not_found(self, service):
        conn = _make_conn(fetchrow_return=None)
        body = ForgotPasswordRequest(email="unknown@example.com")
        with _patch_conn(conn):
            result = await service.forgot_password(body)
        assert result.message  # same generic message, does not raise

    @pytest.mark.asyncio
    async def test_forgotPassword_alias(self, service):
        conn = _make_conn(fetchrow_return=None)
        body = ForgotPasswordRequest(email="x@example.com")
        with _patch_conn(conn):
            result = await service.forgotPassword(body)
        assert result.message


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.reset_password / resetPassword
# ═════════════════════════════════════════════════════════════════════════════

class TestResetPassword:
    def _body(self, token="good-token"):
        return ResetPasswordRequest(
            token=token,
            password="newpassword",
            confirmPassword="newpassword",
        )

    @pytest.mark.asyncio
    async def test_reset_success(self, service):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        row = _make_row(id=10, user_id=1, expires_at=future, used_at=None)
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn):
            result = await service.reset_password(self._body())
        assert "reset" in result.message.lower()

    @pytest.mark.asyncio
    async def test_reset_token_not_found(self, service):
        conn = _make_conn(fetchrow_return=None)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.reset_password(self._body())
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_RESET_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_token_already_used(self, service):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        row = _make_row(id=10, user_id=1, expires_at=future, used_at=datetime.now(timezone.utc))
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.reset_password(self._body())
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "RESET_TOKEN_USED"

    @pytest.mark.asyncio
    async def test_reset_token_expired(self, service):
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        row = _make_row(id=10, user_id=1, expires_at=past, used_at=None)
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.reset_password(self._body())
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "RESET_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_resetPassword_alias(self, service):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        row = _make_row(id=10, user_id=1, expires_at=future, used_at=None)
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn):
            result = await service.resetPassword(self._body())
        assert result.message


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.me
# ═════════════════════════════════════════════════════════════════════════════

class TestMe:
    def _creds(self, token):
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    @pytest.mark.asyncio
    async def test_me_success(self, service):
        from app.auth.service import _generate_access_token
        token = _generate_access_token(7, "me@example.com")
        created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
        row = _make_row(id=7, full_name="Me User", email="me@example.com", is_active=True, created_at=created_at)
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn):
            result = await service.me(self._creds(token))
        assert result.id == 7
        assert result.email == "me@example.com"

    @pytest.mark.asyncio
    async def test_me_no_credentials(self, service):
        with pytest.raises(HTTPException) as exc_info:
            await service.me(None)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, service):
        with pytest.raises(HTTPException) as exc_info:
            await service.me(self._creds("not.a.jwt"))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_me_expired_token(self, service):
        from app.auth.service import SECRET_KEY, ALGORITHM
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "1", "email": "x@x.com", "exp": past, "iat": past}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            await service.me(self._creds(token))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_me_user_not_found_in_db(self, service):
        from app.auth.service import _generate_access_token
        token = _generate_access_token(999, "ghost@example.com")
        conn = _make_conn(fetchrow_return=None)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.me(self._creds(token))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_me_user_inactive(self, service):
        from app.auth.service import _generate_access_token
        token = _generate_access_token(2, "inactive@example.com")
        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        row = _make_row(id=2, full_name="In Active", email="inactive@example.com", is_active=False, created_at=created_at)
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.me(self._creds(token))
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "USER_NOT_FOUND"


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.logout
# ═════════════════════════════════════════════════════════════════════════════

class TestLogout:
    def _make_request(self, cookie_value=None):
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/logout",
            "headers": [],
            "query_string": b"",
        }
        if cookie_value:
            cookie_header = f"refresh_token={cookie_value}".encode()
            scope["headers"] = [(b"cookie", cookie_header)]
        return Request(scope)

    @pytest.mark.asyncio
    async def test_logout_with_cookie(self, service):
        request = self._make_request("some-refresh-token")
        response = MagicMock(spec=Response)
        conn = _make_conn()
        with _patch_conn(conn):
            result = await service.logout(request, response, None)
        assert "logged out" in result.message.lower()
        response.delete_cookie.assert_called_once()
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_without_cookie(self, service):
        request = self._make_request(cookie_value=None)
        response = MagicMock(spec=Response)
        # No DB call expected when no cookie
        result = await service.logout(request, response, None)
        assert result.message
        response.delete_cookie.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# AuthService.refresh
# ═════════════════════════════════════════════════════════════════════════════

class TestRefresh:
    def _make_request(self, cookie_value=None):
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/refresh",
            "headers": [],
            "query_string": b"",
        }
        if cookie_value:
            cookie_header = f"refresh_token={cookie_value}".encode()
            scope["headers"] = [(b"cookie", cookie_header)]
        return Request(scope)

    @pytest.mark.asyncio
    async def test_refresh_no_cookie(self, service):
        request = self._make_request()
        response = MagicMock(spec=Response)
        with pytest.raises(HTTPException) as exc_info:
            await service.refresh(request, response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_token_not_found(self, service):
        request = self._make_request("nonexistent-token")
        response = MagicMock(spec=Response)
        conn = _make_conn(fetchrow_return=None)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.refresh(request, response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_token_revoked(self, service):
        request = self._make_request("revoked-token")
        response = MagicMock(spec=Response)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        row = _make_row(
            id=1, user_id=2, expires_at=future,
            revoked_at=datetime.now(timezone.utc),
            remember_me=False,
            email="u@x.com", full_name="U", is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.refresh(request, response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "REFRESH_TOKEN_REUSE"

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, service):
        request = self._make_request("expired-token")
        response = MagicMock(spec=Response)
        past = datetime.now(timezone.utc) - timedelta(days=1)
        row = _make_row(
            id=1, user_id=2, expires_at=past,
            revoked_at=None,
            remember_me=False,
            email="u@x.com", full_name="U", is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.refresh(request, response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "REFRESH_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_refresh_account_inactive(self, service):
        request = self._make_request("valid-token")
        response = MagicMock(spec=Response)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        row = _make_row(
            id=1, user_id=2, expires_at=future,
            revoked_at=None,
            remember_me=False,
            email="u@x.com", full_name="U", is_active=False,
        )
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn), pytest.raises(HTTPException) as exc_info:
            await service.refresh(request, response)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "ACCOUNT_INACTIVE"

    @pytest.mark.asyncio
    async def test_refresh_success(self, service):
        request = self._make_request("valid-token")
        response = MagicMock(spec=Response)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        row = _make_row(
            id=1, user_id=2, expires_at=future,
            revoked_at=None,
            remember_me=False,
            email="u@x.com", full_name="User", is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn):
            result = await service.refresh(request, response)
        assert result.tokenType == "bearer"
        assert result.accessToken
        assert result.user["email"] == "u@x.com"
        response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_success_remember_me(self, service):
        from app.auth.service import REFRESH_TOKEN_REMEMBER_DAYS
        request = self._make_request("valid-token")
        response = MagicMock(spec=Response)
        future = datetime.now(timezone.utc) + timedelta(days=30)
        row = _make_row(
            id=1, user_id=2, expires_at=future,
            revoked_at=None,
            remember_me=True,
            email="u@x.com", full_name="User", is_active=True,
        )
        conn = _make_conn(fetchrow_return=row)
        with _patch_conn(conn):
            await service.refresh(request, response)
        call_kw = response.set_cookie.call_args.kwargs
        assert call_kw["max_age"] == REFRESH_TOKEN_REMEMBER_DAYS * 86400


# ═════════════════════════════════════════════════════════════════════════════
# Router integration (via TestClient) — mocks the AuthService methods
# ═════════════════════════════════════════════════════════════════════════════

class TestRouter:
    """Smoke-test each route end-to-end with a mocked AuthService."""

    def _mock_service(self, client_fixture, **method_overrides):
        """Patch get_auth_service to return a MagicMock with given async returns."""
        svc = MagicMock()
        for name, ret in method_overrides.items():
            setattr(svc, name, AsyncMock(return_value=ret))
        return patch("app.auth.router.get_auth_service", return_value=svc), svc

    def test_register_201(self, client):
        from app.auth.schemas import RegisterResponse
        resp_obj = RegisterResponse(
            id=1, fullName="J", email="j@e.com", createdAt="2024-01-01T00:00:00"
        )
        patcher, _ = self._mock_service(client, register=resp_obj)
        with patcher:
            r = client.post(
                "/auth/register",
                json={
                    "fullName": "J",
                    "email": "j@e.com",
                    "password": "password123",
                    "confirmPassword": "password123",
                    "acceptTerms": True,
                },
            )
        assert r.status_code == 201

    def test_login_200(self, client):
        from app.auth.schemas import LoginResponse
        resp_obj = LoginResponse(
            accessToken="tok", tokenType="bearer", user={"id": 1, "fullName": "J", "email": "j@e.com"}
        )
        patcher, _ = self._mock_service(client, login=resp_obj)
        with patcher:
            r = client.post(
                "/auth/login",
                json={"email": "j@e.com", "password": "password123"},
            )
        assert r.status_code == 200
        assert r.json()["accessToken"] == "tok"

    def test_forgot_password_202(self, client):
        from app.auth.schemas import ForgotPasswordResponse
        resp_obj = ForgotPasswordResponse(message="If an account with that email exists, a password reset link has been sent.")
        patcher, _ = self._mock_service(client, forgotPassword=resp_obj)
        with patcher:
            r = client.post("/auth/forgot-password", json={"email": "j@e.com"})
        assert r.status_code == 202

    def test_reset_password_200(self, client):
        from app.auth.schemas import ResetPasswordResponse
        resp_obj = ResetPasswordResponse(message="Your password has been reset successfully.")
        patcher, _ = self._mock_service(client, resetPassword=resp_obj)
        with patcher:
            r = client.post(
                "/auth/reset-password",
                json={"token": "t", "password": "newpassword1", "confirmPassword": "newpassword1"},
            )
        assert r.status_code == 200

    def test_me_200(self, client):
        from app.auth.schemas import MeResponse
        from app.auth.service import _generate_access_token
        token = _generate_access_token(1, "j@e.com")
        resp_obj = MeResponse(id=1, fullName="J", email="j@e.com", createdAt="2024-01-01T00:00:00")
        patcher, _ = self._mock_service(client, me=resp_obj)
        with patcher:
            r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_logout_200(self, client):
        from app.auth.schemas import LogoutResponse
        resp_obj = LogoutResponse(message="Logged out successfully.")
        patcher, _ = self._mock_service(client, logout=resp_obj)
        with patcher:
            r = client.post("/auth/logout")
        assert r.status_code == 200

    def test_refresh_200(self, client):
        from app.auth.schemas import RefreshResponse
        resp_obj = RefreshResponse(
            accessToken="new-tok", tokenType="bearer", user={"id": 1, "fullName": "J", "email": "j@e.com"}
        )
        patcher, _ = self._mock_service(client, refresh=resp_obj)
        with patcher:
            r = client.post("/auth/refresh")
        assert r.status_code == 200
        assert r.json()["accessToken"] == "new-tok"


# ═════════════════════════════════════════════════════════════════════════════
# Schema tests
# ═════════════════════════════════════════════════════════════════════════════

class TestSchemas:
    def test_register_request_alias(self):
        body = RegisterRequest(
            fullName="Alice",
            email="alice@example.com",
            password="password123",
            confirmPassword="password123",
            acceptTerms=True,
        )
        assert body.full_name == "Alice"

    def test_login_request_defaults_remember_me_false(self):
        body = LoginRequest(email="a@b.com", password="secret123")
        assert body.remember_me is False

    def test_register_response_alias(self):
        from app.auth.schemas import RegisterResponse
        r = RegisterResponse(id=1, fullName="A", email="a@b.com", createdAt="2024-01-01T00:00:00")
        assert r.full_name == "A"
        assert r.fullName == "A"

    def test_login_response_alias(self):
        from app.auth.schemas import LoginResponse
        r = LoginResponse(accessToken="t", tokenType="bearer", user={})
        assert r.access_token == "t"
        assert r.token_type == "bearer"

    def test_me_response_fields(self):
        from app.auth.schemas import MeResponse
        r = MeResponse(id=5, fullName="B", email="b@c.com", createdAt="2024-01-01T00:00:00")
        assert r.id == 5
        assert r.email == "b@c.com"

    def test_forgot_password_response(self):
        from app.auth.schemas import ForgotPasswordResponse
        r = ForgotPasswordResponse(message="check email")
        assert r.message == "check email"

    def test_reset_password_response(self):
        from app.auth.schemas import ResetPasswordResponse
        r = ResetPasswordResponse(message="done")
        assert r.message == "done"

    def test_logout_response(self):
        from app.auth.schemas import LogoutResponse
        r = LogoutResponse(message="bye")
        assert r.message == "bye"

    def test_refresh_response_alias(self):
        from app.auth.schemas import RefreshResponse
        r = RefreshResponse(accessToken="rt", tokenType="bearer", user={})
        assert r.access_token == "rt"
