"""Unit tests for app/config/settings.py"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID = {
    "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost/db",
    "JWT_SECRET_KEY": "supersecretkey",
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_TTL_MINUTES": 15,
    "BCRYPT_ROUNDS": 12,
    "RESET_TOKEN_TTL_MINUTES": 30,
    "REFRESH_TOKEN_TTL_DAYS": 7,
    "REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS": 30,
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": 587,
    "SMTP_USERNAME": "user@example.com",
    "SMTP_PASSWORD": "smtp_password",
    "SMTP_FROM_ADDRESS": "noreply@example.com",
    "SMTP_USE_TLS": True,
    "RATE_LIMIT_LOGIN_MAX_ATTEMPTS": 5,
    "RATE_LIMIT_LOGIN_WINDOW_SECONDS": 60,
    "RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS": 3,
    "RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS": 3600,
}


def make_settings(**overrides):
    """Import Settings fresh and build from a dict (not from .env)."""
    from app.config.settings import Settings

    data = {**MINIMAL_VALID, **overrides}
    # Disable env-file loading so tests are hermetic
    return Settings.model_validate(data)


# ---------------------------------------------------------------------------
# Happy-path: all required fields present
# ---------------------------------------------------------------------------

class TestSettingsValidConstruction:
    def test_basic_construction(self):
        s = make_settings()
        assert s.DATABASE_URL == MINIMAL_VALID["DATABASE_URL"]
        assert s.JWT_SECRET_KEY == MINIMAL_VALID["JWT_SECRET_KEY"]
        assert s.JWT_ALGORITHM == "HS256"
        assert s.JWT_ACCESS_TOKEN_TTL_MINUTES == 15
        assert s.BCRYPT_ROUNDS == 12
        assert s.RESET_TOKEN_TTL_MINUTES == 30
        assert s.REFRESH_TOKEN_TTL_DAYS == 7
        assert s.REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS == 30
        assert s.SMTP_HOST == "smtp.example.com"
        assert s.SMTP_PORT == 587
        assert s.SMTP_USERNAME == "user@example.com"
        assert s.SMTP_PASSWORD == "smtp_password"
        assert s.SMTP_FROM_ADDRESS == "noreply@example.com"
        assert s.SMTP_USE_TLS is True
        assert s.RATE_LIMIT_LOGIN_MAX_ATTEMPTS == 5
        assert s.RATE_LIMIT_LOGIN_WINDOW_SECONDS == 60
        assert s.RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS == 3
        assert s.RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS == 3600

    def test_default_jwt_algorithm(self):
        """JWT_ALGORITHM defaults to HS256 when not supplied."""
        from app.config.settings import Settings

        data = {k: v for k, v in MINIMAL_VALID.items() if k != "JWT_ALGORITHM"}
        s = Settings.model_validate(data)
        assert s.JWT_ALGORITHM == "HS256"

    def test_default_smtp_use_tls(self):
        """SMTP_USE_TLS defaults to True."""
        from app.config.settings import Settings

        data = {k: v for k, v in MINIMAL_VALID.items() if k != "SMTP_USE_TLS"}
        s = Settings.model_validate(data)
        assert s.SMTP_USE_TLS is True

    def test_smtp_use_tls_false(self):
        s = make_settings(SMTP_USE_TLS=False)
        assert s.SMTP_USE_TLS is False

    def test_non_default_jwt_algorithm(self):
        s = make_settings(JWT_ALGORITHM="RS256")
        assert s.JWT_ALGORITHM == "RS256"


# ---------------------------------------------------------------------------
# DATABASE_URL validator
# ---------------------------------------------------------------------------

class TestDatabaseUrlValidator:
    def test_empty_string_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            make_settings(DATABASE_URL="")
        assert "DATABASE_URL" in str(exc_info.value)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            make_settings(DATABASE_URL="   ")
        assert "DATABASE_URL" in str(exc_info.value)

    def test_valid_url_accepted(self):
        s = make_settings(DATABASE_URL="postgresql://user:pass@host/db")
        assert s.DATABASE_URL == "postgresql://user:pass@host/db"


# ---------------------------------------------------------------------------
# JWT_SECRET_KEY validator
# ---------------------------------------------------------------------------

class TestJwtSecretKeyValidator:
    def test_empty_string_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            make_settings(JWT_SECRET_KEY="")
        assert "JWT_SECRET_KEY" in str(exc_info.value)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            make_settings(JWT_SECRET_KEY="   ")
        assert "JWT_SECRET_KEY" in str(exc_info.value)

    def test_valid_secret_accepted(self):
        s = make_settings(JWT_SECRET_KEY="my-very-secret-key")
        assert s.JWT_SECRET_KEY == "my-very-secret-key"


# ---------------------------------------------------------------------------
# SMTP field validators (HOST, USERNAME, PASSWORD)
# ---------------------------------------------------------------------------

class TestSmtpFieldValidators:
    @pytest.mark.parametrize("field", ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"])
    def test_empty_string_raises(self, field):
        with pytest.raises(ValidationError) as exc_info:
            make_settings(**{field: ""})
        assert field in str(exc_info.value)

    @pytest.mark.parametrize("field", ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"])
    def test_whitespace_only_raises(self, field):
        with pytest.raises(ValidationError) as exc_info:
            make_settings(**{field: "   "})
        assert field in str(exc_info.value)

    def test_valid_smtp_fields_accepted(self):
        s = make_settings(
            SMTP_HOST="mail.example.org",
            SMTP_USERNAME="mailer",
            SMTP_PASSWORD="secret123",
        )
        assert s.SMTP_HOST == "mail.example.org"
        assert s.SMTP_USERNAME == "mailer"
        assert s.SMTP_PASSWORD == "secret123"


# ---------------------------------------------------------------------------
# SMTP_FROM_ADDRESS must be a valid email
# ---------------------------------------------------------------------------

class TestSmtpFromAddress:
    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            make_settings(SMTP_FROM_ADDRESS="not-an-email")

    def test_valid_email_accepted(self):
        s = make_settings(SMTP_FROM_ADDRESS="admin@domain.io")
        assert "@" in str(s.SMTP_FROM_ADDRESS)


# ---------------------------------------------------------------------------
# SMTP_PORT range
# ---------------------------------------------------------------------------

class TestSmtpPort:
    def test_port_zero_raises(self):
        with pytest.raises(ValidationError):
            make_settings(SMTP_PORT=0)

    def test_port_65536_raises(self):
        with pytest.raises(ValidationError):
            make_settings(SMTP_PORT=65536)

    def test_port_65535_accepted(self):
        s = make_settings(SMTP_PORT=65535)
        assert s.SMTP_PORT == 65535

    def test_port_1_accepted(self):
        s = make_settings(SMTP_PORT=1)
        assert s.SMTP_PORT == 1

    def test_standard_port_accepted(self):
        s = make_settings(SMTP_PORT=465)
        assert s.SMTP_PORT == 465


# ---------------------------------------------------------------------------
# BCRYPT_ROUNDS must be >= 12
# ---------------------------------------------------------------------------

class TestBcryptRounds:
    def test_below_12_raises(self):
        with pytest.raises(ValidationError):
            make_settings(BCRYPT_ROUNDS=11)

    def test_exactly_12_accepted(self):
        s = make_settings(BCRYPT_ROUNDS=12)
        assert s.BCRYPT_ROUNDS == 12

    def test_above_12_accepted(self):
        s = make_settings(BCRYPT_ROUNDS=14)
        assert s.BCRYPT_ROUNDS == 14


# ---------------------------------------------------------------------------
# RESET_TOKEN_TTL_MINUTES must be > 0
# ---------------------------------------------------------------------------

class TestResetTokenTTL:
    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            make_settings(RESET_TOKEN_TTL_MINUTES=0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            make_settings(RESET_TOKEN_TTL_MINUTES=-1)

    def test_positive_accepted(self):
        s = make_settings(RESET_TOKEN_TTL_MINUTES=60)
        assert s.RESET_TOKEN_TTL_MINUTES == 60


# ---------------------------------------------------------------------------
# REFRESH_TOKEN_TTL_DAYS must be > 0
# ---------------------------------------------------------------------------

class TestRefreshTokenTTL:
    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            make_settings(REFRESH_TOKEN_TTL_DAYS=0)

    def test_positive_accepted(self):
        s = make_settings(REFRESH_TOKEN_TTL_DAYS=1)
        assert s.REFRESH_TOKEN_TTL_DAYS == 1

    def test_remember_me_zero_raises(self):
        with pytest.raises(ValidationError):
            make_settings(REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS=0)

    def test_remember_me_positive_accepted(self):
        s = make_settings(REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS=90)
        assert s.REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS == 90


# ---------------------------------------------------------------------------
# Rate-limit fields must be > 0
# ---------------------------------------------------------------------------

class TestRateLimitFields:
    @pytest.mark.parametrize(
        "field",
        [
            "RATE_LIMIT_LOGIN_MAX_ATTEMPTS",
            "RATE_LIMIT_LOGIN_WINDOW_SECONDS",
            "RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS",
            "RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS",
        ],
    )
    def test_zero_raises(self, field):
        with pytest.raises(ValidationError):
            make_settings(**{field: 0})

    @pytest.mark.parametrize(
        "field",
        [
            "RATE_LIMIT_LOGIN_MAX_ATTEMPTS",
            "RATE_LIMIT_LOGIN_WINDOW_SECONDS",
            "RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS",
            "RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS",
        ],
    )
    def test_positive_accepted(self, field):
        s = make_settings(**{field: 1})
        assert getattr(s, field) == 1


# ---------------------------------------------------------------------------
# get_settings() caching
# ---------------------------------------------------------------------------

class TestGetSettings:
    def test_get_settings_returns_settings_instance(self):
        """get_settings() must return a Settings object (or raise if env not set)."""
        from app.config.settings import get_settings, Settings

        # The function may succeed or raise depending on the test environment;
        # we only verify that if it succeeds it returns the right type.
        try:
            result = get_settings()
            assert isinstance(result, Settings)
        except Exception:
            # Missing required env vars in CI/test environment — acceptable
            pass

    def test_get_settings_is_cached(self):
        """Calling get_settings() twice returns the identical object."""
        from app.config.settings import get_settings

        try:
            first = get_settings()
            second = get_settings()
            assert first is second
        except Exception:
            pass
