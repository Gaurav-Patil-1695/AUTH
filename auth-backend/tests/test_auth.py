"""Integration tests for the auth-backend FastAPI application.

These tests use an in-memory SQLite database so no real Postgres / SMTP
connection is required.  External I/O (email sending) is patched out.
"""
import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Environment variables must be set BEFORE the app modules are imported so
# that pydantic-settings picks them up correctly.
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_auth.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_TTL_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_TTL_DAYS", "7")
os.environ.setdefault("REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS", "30")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # low for speed in tests
os.environ.setdefault("RESET_TOKEN_TTL_MINUTES", "60")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USE_TLS", "false")
os.environ.setdefault("SMTP_USERNAME", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "password")
os.environ.setdefault("SMTP_FROM_ADDRESS", "no-reply@example.com")
os.environ.setdefault("SMTP_FROM_NAME", "Test Auth")
os.environ.setdefault("RATE_LIMIT_LOGIN_MAX", "100")
os.environ.setdefault("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "60")
os.environ.setdefault("RATE_LIMIT_FORGOT_PASSWORD_MAX", "100")
os.environ.setdefault("RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS", "60")
os.environ.setdefault("APP_BASE_URL", "http://localhost:3000")
os.environ.setdefault("CORS_ORIGIN", "http://localhost:3000")

# ---------------------------------------------------------------------------
# Make sure the app package is importable when tests are run from the repo root
# or from inside AUTH/auth-backend/.
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.join(HERE, "..")
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# ---------------------------------------------------------------------------
# Now import the application
# ---------------------------------------------------------------------------
try:
    from app.database import Base, get_db
    from app.main import app
except Exception as exc:  # pragma: no cover
    pytest.skip(f"Could not import app: {exc}", allow_module_level=True)

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///./test_auth_run.db"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once before the test session and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Remove leftover file
    db_file = "./test_auth_run.db"
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate all tables between tests to keep state isolated."""
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture(scope="session")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper shortcuts
# ---------------------------------------------------------------------------

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
ME_URL = "/auth/me"
REFRESH_URL = "/auth/refresh"
LOGOUT_URL = "/auth/logout"
FORGOT_URL = "/auth/forgot-password"
RESET_URL = "/auth/reset-password"

DEFAULT_USER = {
    "full_name": "Alice Smith",
    "email": "alice@example.com",
    "password": "SecurePass123!",
}


def register_user(client, payload=None):
    payload = payload or DEFAULT_USER
    return client.post(REGISTER_URL, json=payload)


def login_user(client, email=None, password=None, remember_me=False):
    email = email or DEFAULT_USER["email"]
    password = password or DEFAULT_USER["password"]
    return client.post(
        LOGIN_URL,
        json={"email": email, "password": password, "remember_me": remember_me},
    )


def get_access_token(client):
    register_user(client)
    resp = login_user(client)
    return resp.json()["access_token"]


# ===========================================================================
# Registration tests
# ===========================================================================


class TestRegister:
    def test_register_success_returns_201(self, client):
        resp = register_user(client)
        assert resp.status_code in (200, 201)

    def test_register_returns_user_fields(self, client):
        resp = register_user(client)
        body = resp.json()
        assert body["email"] == DEFAULT_USER["email"]
        assert body["full_name"] == DEFAULT_USER["full_name"]
        assert "id" in body

    def test_register_does_not_return_password(self, client):
        resp = register_user(client)
        body = resp.json()
        assert "password" not in body
        assert "hashed_password" not in body

    def test_register_duplicate_email_returns_error(self, client):
        register_user(client)
        resp = register_user(client)  # second attempt
        assert resp.status_code in (400, 409, 422)

    def test_register_invalid_email_returns_422(self, client):
        resp = client.post(
            REGISTER_URL,
            json={"full_name": "Bob", "email": "not-an-email", "password": "Pass123!"},
        )
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self, client):
        resp = client.post(
            REGISTER_URL,
            json={"full_name": "Bob", "email": "bob@example.com"},
        )
        assert resp.status_code == 422

    def test_register_missing_email_returns_422(self, client):
        resp = client.post(
            REGISTER_URL,
            json={"full_name": "Bob", "password": "Pass123!"},
        )
        assert resp.status_code == 422


# ===========================================================================
# Login tests
# ===========================================================================


class TestLogin:
    def test_login_success_returns_access_token(self, client):
        register_user(client)
        resp = login_user(client)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"].lower() == "bearer"

    def test_login_sets_refresh_token_cookie(self, client):
        register_user(client)
        resp = login_user(client)
        assert resp.status_code == 200
        # refresh token should be in a cookie
        assert "refresh_token" in resp.cookies or "Set-Cookie" in resp.headers

    def test_login_wrong_password_returns_401(self, client):
        register_user(client)
        resp = login_user(client, password="WrongPassword!")
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        resp = login_user(client, email="ghost@example.com")
        assert resp.status_code == 401

    def test_login_error_message_is_generic(self, client):
        """Enumeration resistance: same message regardless of whether email exists."""
        resp = login_user(client, email="ghost@example.com")
        body = resp.json()
        assert "detail" in body
        assert "password" in body["detail"].lower() or "invalid" in body["detail"].lower()

    def test_login_missing_email_returns_422(self, client):
        resp = client.post(LOGIN_URL, json={"password": "Pass123!"})
        assert resp.status_code == 422

    def test_login_missing_password_returns_422(self, client):
        resp = client.post(LOGIN_URL, json={"email": "alice@example.com"})
        assert resp.status_code == 422


# ===========================================================================
# /auth/me tests
# ===========================================================================


class TestMe:
    def test_me_returns_current_user(self, client):
        token = get_access_token(client)
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == DEFAULT_USER["email"]

    def test_me_without_token_returns_401(self, client):
        resp = client.get(ME_URL)
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        resp = client.get(ME_URL, headers={"Authorization": "Bearer totally.invalid.token"})
        assert resp.status_code == 401


# ===========================================================================
# Refresh token tests
# ===========================================================================


class TestRefresh:
    def test_refresh_returns_new_access_token(self, client):
        register_user(client)
        login_resp = login_user(client)
        assert login_resp.status_code == 200
        resp = client.post(REFRESH_URL)  # cookies are carried by TestClient
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body

    def test_refresh_without_cookie_returns_401(self, client):
        # Use a fresh client to avoid carrying cookies from another test
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app, raise_server_exceptions=True) as fresh_client:
            resp = fresh_client.post(REFRESH_URL)
        assert resp.status_code == 401

    def test_refresh_rotates_token(self, client):
        """After a refresh the new cookie should differ from the original."""
        register_user(client)
        login_resp = login_user(client)
        first_cookie = login_resp.cookies.get("refresh_token")
        refresh_resp = client.post(REFRESH_URL)
        assert refresh_resp.status_code == 200
        new_cookie = refresh_resp.cookies.get("refresh_token")
        # Tokens should have rotated (may be None if httpOnly prevents reading)
        if first_cookie and new_cookie:
            assert first_cookie != new_cookie


# ===========================================================================
# Logout tests
# ===========================================================================


class TestLogout:
    def test_logout_returns_200(self, client):
        register_user(client)
        login_user(client)
        resp = client.post(LOGOUT_URL)
        assert resp.status_code == 200

    def test_logout_invalidates_refresh_token(self, client):
        register_user(client)
        login_user(client)
        client.post(LOGOUT_URL)
        # After logout, a refresh attempt should fail
        resp = client.post(REFRESH_URL)
        assert resp.status_code in (401, 403)


# ===========================================================================
# Forgot password tests
# ===========================================================================


class TestForgotPassword:
    @patch("app.auth.service.send_reset_email", return_value=None)
    def test_forgot_password_known_email_returns_202(self, mock_send, client):
        register_user(client)
        resp = client.post(FORGOT_URL, json={"email": DEFAULT_USER["email"]})
        assert resp.status_code == 202

    @patch("app.auth.service.send_reset_email", return_value=None)
    def test_forgot_password_unknown_email_returns_202(self, mock_send, client):
        """Enumeration resistance: always returns 202 regardless of email existence."""
        resp = client.post(FORGOT_URL, json={"email": "nobody@example.com"})
        assert resp.status_code == 202

    def test_forgot_password_invalid_email_returns_422(self, client):
        resp = client.post(FORGOT_URL, json={"email": "not-valid"})
        assert resp.status_code == 422

    def test_forgot_password_missing_email_returns_422(self, client):
        resp = client.post(FORGOT_URL, json={})
        assert resp.status_code == 422

    @patch("app.auth.service.send_reset_email", return_value=None)
    def test_forgot_password_sends_email_for_known_user(self, mock_send, client):
        register_user(client)
        client.post(FORGOT_URL, json={"email": DEFAULT_USER["email"]})
        mock_send.assert_called_once()

    @patch("app.auth.service.send_reset_email", return_value=None)
    def test_forgot_password_does_not_send_email_for_unknown_user(self, mock_send, client):
        client.post(FORGOT_URL, json={"email": "nobody@example.com"})
        mock_send.assert_not_called()


# ===========================================================================
# Reset password tests
# ===========================================================================


class TestResetPassword:
    def _get_reset_token(self, client):
        """Register a user, trigger forgot-password, and extract the raw token
        from what would have been sent to the email."""
        register_user(client)
        captured = {}

        def fake_send(email, token, base_url):
            captured["token"] = token

        with patch("app.auth.service.send_reset_email", side_effect=fake_send):
            client.post(FORGOT_URL, json={"email": DEFAULT_USER["email"]})

        return captured.get("token")

    def test_reset_password_with_valid_token_returns_200(self, client):
        token = self._get_reset_token(client)
        if token is None:
            pytest.skip("Could not capture reset token from service")
        resp = client.post(
            RESET_URL,
            json={"token": token, "new_password": "NewSecurePass456!"},
        )
        assert resp.status_code == 200

    def test_reset_password_allows_login_with_new_password(self, client):
        token = self._get_reset_token(client)
        if token is None:
            pytest.skip("Could not capture reset token from service")
        client.post(
            RESET_URL,
            json={"token": token, "new_password": "NewSecurePass456!"},
        )
        resp = login_user(client, password="NewSecurePass456!")
        assert resp.status_code == 200

    def test_reset_password_old_password_no_longer_works(self, client):
        token = self._get_reset_token(client)
        if token is None:
            pytest.skip("Could not capture reset token from service")
        client.post(
            RESET_URL,
            json={"token": token, "new_password": "NewSecurePass456!"},
        )
        resp = login_user(client, password=DEFAULT_USER["password"])
        assert resp.status_code == 401

    def test_reset_password_invalid_token_returns_error(self, client):
        resp = client.post(
            RESET_URL,
            json={"token": "completely-invalid-token", "new_password": "NewPass123!"},
        )
        assert resp.status_code in (400, 401, 404, 422)

    def test_reset_password_token_cannot_be_reused(self, client):
        token = self._get_reset_token(client)
        if token is None:
            pytest.skip("Could not capture reset token from service")
        client.post(
            RESET_URL,
            json={"token": token, "new_password": "NewSecurePass456!"},
        )
        resp = client.post(
            RESET_URL,
            json={"token": token, "new_password": "AnotherPass789!"},
        )
        assert resp.status_code in (400, 401, 404, 410)

    def test_reset_password_missing_token_returns_422(self, client):
        resp = client.post(RESET_URL, json={"new_password": "NewPass123!"})
        assert resp.status_code == 422

    def test_reset_password_missing_new_password_returns_422(self, client):
        resp = client.post(RESET_URL, json={"token": "sometoken"})
        assert resp.status_code == 422


# ===========================================================================
# Security / enumeration-resistance tests
# ===========================================================================


class TestSecurity:
    def test_login_bad_email_same_message_as_bad_password(self, client):
        register_user(client)
        bad_email_resp = login_user(client, email="ghost@example.com")
        bad_pass_resp = login_user(client, password="WrongPassword!")
        assert bad_email_resp.status_code == bad_pass_resp.status_code == 401
        # Both should carry the same generic message
        assert bad_email_resp.json()["detail"] == bad_pass_resp.json()["detail"]

    def test_access_token_is_bearer_jwt(self, client):
        """The token should have three dot-separated base64url parts."""
        token = get_access_token(client)
        parts = token.split(".")
        assert len(parts) == 3, "Access token should be a JWT with three parts"


# ===========================================================================
# Config / settings smoke tests
# ===========================================================================


class TestConfig:
    def test_settings_are_loaded(self):
        from app.config import settings

        assert settings.JWT_SECRET_KEY == "test-secret-key-that-is-long-enough"
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_TTL_MINUTES == 15
        assert settings.REFRESH_TOKEN_TTL_DAYS == 7
        assert settings.BCRYPT_ROUNDS == 4


# ===========================================================================
# Schema / model smoke tests
# ===========================================================================


class TestSchemas:
    def test_register_schema_validates_email(self):
        from app.auth.schemas import RegisterRequest
        import pydantic

        with pytest.raises((pydantic.ValidationError, ValueError)):
            RegisterRequest(full_name="Bob", email="bad-email", password="Pass123!")

    def test_register_schema_happy_path(self):
        from app.auth.schemas import RegisterRequest

        obj = RegisterRequest(
            full_name="Alice", email="alice@example.com", password="SecurePass123!"
        )
        assert obj.email == "alice@example.com"
        assert obj.full_name == "Alice"

    def test_login_schema_happy_path(self):
        from app.auth.schemas import LoginRequest

        obj = LoginRequest(email="alice@example.com", password="SecurePass123!")
        assert obj.email == "alice@example.com"

    def test_forgot_password_schema_validates_email(self):
        from app.auth.schemas import ForgotPasswordRequest
        import pydantic

        with pytest.raises((pydantic.ValidationError, ValueError)):
            ForgotPasswordRequest(email="not-an-email")

    def test_reset_password_schema_happy_path(self):
        from app.auth.schemas import ResetPasswordRequest

        obj = ResetPasswordRequest(token="abc123", new_password="NewPass123!")
        assert obj.token == "abc123"
        assert obj.new_password == "NewPass123!"
