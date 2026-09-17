"""Unit tests for the logout-related functionality in auth service and router."""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers / constants mirrored from the service module
# ---------------------------------------------------------------------------
COOKIE_NAME = "refresh_token"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_service():
    """Return a real AuthService instance (DB calls will be patched per-test)."""
    from app.auth.service import AuthService
    return AuthService()


@pytest.fixture()
def mock_response():
    """A real FastAPI/Starlette Response object so cookie helpers work."""
    return Response()


def _make_request(cookies: dict | None = None) -> Request:
    """Build a minimal Request-like object with the given cookies."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/logout",
        "query_string": b"",
        "headers": [],
    }
    request = Request(scope)
    # Inject cookies directly into the internal state
    request._cookies = cookies or {}
    return request


# ---------------------------------------------------------------------------
# Tests for AuthService.logout
# ---------------------------------------------------------------------------

class TestAuthServiceLogout:
    """Tests for AuthService.logout()"""

    @pytest.mark.asyncio
    async def test_logout_with_valid_refresh_cookie_revokes_token(self, auth_service, mock_response):
        """When a refresh_token cookie is present, the DB row should be revoked."""
        raw_token = "some-raw-refresh-token"
        request = _make_request(cookies={COOKIE_NAME: raw_token})

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await auth_service.logout(request, mock_response, credentials=None)

        # The DB execute should have been called with the hashed token
        mock_conn.execute.assert_awaited_once()
        call_args = mock_conn.execute.call_args
        # Second positional arg is the token hash
        assert call_args[0][1] == _hash_token(raw_token)

        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_without_refresh_cookie_skips_db_and_succeeds(self, auth_service, mock_response):
        """When no refresh_token cookie is present, no DB call is made."""
        request = _make_request(cookies={})

        with patch("app.auth.service.get_connection") as mock_get_conn:
            result = await auth_service.logout(request, mock_response, credentials=None)

        # get_connection should NOT have been called
        mock_get_conn.assert_not_called()
        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_clears_refresh_cookie(self, auth_service, mock_response):
        """logout() must clear the refresh_token cookie from the response."""
        raw_token = "token-to-clear"
        request = _make_request(cookies={COOKIE_NAME: raw_token})

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            await auth_service.logout(request, mock_response, credentials=None)

        # The cookie should have a delete directive (max-age=0 or set-cookie header)
        set_cookie_header = mock_response.headers.get("set-cookie", "")
        assert COOKIE_NAME in set_cookie_header

    @pytest.mark.asyncio
    async def test_logout_clears_cookie_even_without_refresh_cookie(self, auth_service, mock_response):
        """logout() clears the cookie unconditionally, even if no cookie was sent."""
        request = _make_request(cookies={})

        with patch("app.auth.service.get_connection"):
            await auth_service.logout(request, mock_response, credentials=None)

        set_cookie_header = mock_response.headers.get("set-cookie", "")
        assert COOKIE_NAME in set_cookie_header

    @pytest.mark.asyncio
    async def test_logout_returns_logout_response_schema(self, auth_service, mock_response):
        """Return type must be LogoutResponse with the expected message."""
        from app.auth.schemas import LogoutResponse

        request = _make_request(cookies={})
        with patch("app.auth.service.get_connection"):
            result = await auth_service.logout(request, mock_response, credentials=None)

        assert isinstance(result, LogoutResponse)
        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_with_credentials_param_does_not_crash(self, auth_service, mock_response):
        """Passing a credentials object should not change logout behaviour."""
        request = _make_request(cookies={})
        creds = MagicMock(spec=HTTPAuthorizationCredentials)
        creds.credentials = "some-access-token"

        with patch("app.auth.service.get_connection"):
            result = await auth_service.logout(request, mock_response, credentials=creds)

        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_uses_correct_sql_pattern(self, auth_service, mock_response):
        """The UPDATE statement must only revoke tokens that are not already revoked."""
        raw_token = "check-sql-token"
        request = _make_request(cookies={COOKIE_NAME: raw_token})

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            await auth_service.logout(request, mock_response, credentials=None)

        sql = mock_conn.execute.call_args[0][0]
        assert "revoked_at" in sql.lower()
        assert "token_hash" in sql.lower()


# ---------------------------------------------------------------------------
# Tests for helper functions used by logout
# ---------------------------------------------------------------------------

class TestClearRefreshCookie:
    """Tests for the _clear_refresh_cookie helper."""

    def test_clear_refresh_cookie_deletes_cookie(self):
        from app.auth.service import _clear_refresh_cookie

        response = Response()
        _clear_refresh_cookie(response)

        set_cookie_header = response.headers.get("set-cookie", "")
        assert COOKIE_NAME in set_cookie_header

    def test_clear_refresh_cookie_idempotent(self):
        """Calling twice should not raise."""
        from app.auth.service import _clear_refresh_cookie

        response = Response()
        _clear_refresh_cookie(response)
        _clear_refresh_cookie(response)
        # No exception means success


# ---------------------------------------------------------------------------
# Tests for the router endpoint via TestClient
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_client():
    """Create a TestClient for the FastAPI app built from the router."""
    from fastapi import FastAPI
    from app.auth.router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


class TestLogoutRouterEndpoint:
    """Integration-level tests that call the /auth/logout HTTP endpoint."""

    def test_logout_returns_200(self, app_client):
        """POST /auth/logout should return HTTP 200."""
        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            response = app_client.post("/auth/logout")

        assert response.status_code == 200

    def test_logout_returns_logged_out_message(self, app_client):
        """Response body should contain the success message."""
        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            response = app_client.post("/auth/logout")

        data = response.json()
        assert data["message"] == "Logged out successfully."

    def test_logout_with_refresh_cookie_calls_db(self, app_client):
        """When a refresh_token cookie is provided, the DB revoke query executes."""
        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            app_client.cookies.set(COOKIE_NAME, "some-refresh-token")
            response = app_client.post("/auth/logout")
            app_client.cookies.clear()

        assert response.status_code == 200
        mock_conn.execute.assert_awaited_once()

    def test_logout_without_bearer_token_still_succeeds(self, app_client):
        """No Authorization header required for logout."""
        with patch("app.auth.service.get_connection"):
            response = app_client.post("/auth/logout")

        assert response.status_code == 200

    def test_logout_with_bearer_token_still_succeeds(self, app_client):
        """Optional Bearer token should not break logout."""
        with patch("app.auth.service.get_connection"):
            response = app_client.post(
                "/auth/logout",
                headers={"Authorization": "Bearer some.access.token"},
            )

        assert response.status_code == 200

    def test_logout_clears_cookie_in_response(self, app_client):
        """The response should include a Set-Cookie header clearing the refresh cookie."""
        with patch("app.auth.service.get_connection") as mock_get_conn:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock(return_value=False)

            app_client.cookies.set(COOKIE_NAME, "tok")
            response = app_client.post("/auth/logout")
            app_client.cookies.clear()

        set_cookie = response.headers.get("set-cookie", "")
        assert COOKIE_NAME in set_cookie


# ---------------------------------------------------------------------------
# Tests for LogoutResponse schema
# ---------------------------------------------------------------------------

class TestLogoutResponseSchema:
    def test_logout_response_message_field(self):
        from app.auth.schemas import LogoutResponse

        resp = LogoutResponse(message="Logged out successfully.")
        assert resp.message == "Logged out successfully."

    def test_logout_response_serialization(self):
        from app.auth.schemas import LogoutResponse

        resp = LogoutResponse(message="Logged out successfully.")
        data = resp.model_dump()
        assert data == {"message": "Logged out successfully."}

    def test_logout_response_requires_message(self):
        from app.auth.schemas import LogoutResponse
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LogoutResponse()  # type: ignore[call-arg]
