"""Unit tests for app.core.rate_limit."""
from slowapi import Limiter

from app.core.rate_limit import forgot_password_limit, limiter, login_limit


class TestLimiterInstance:
    def test_limiter_is_limiter_instance(self):
        assert isinstance(limiter, Limiter)


class TestLoginLimit:
    def test_returns_string(self):
        result = login_limit()
        assert isinstance(result, str)

    def test_non_empty(self):
        assert login_limit() != ""

    def test_matches_settings(self):
        from app.config.settings import settings

        assert login_limit() == settings.LOGIN_RATE_LIMIT


class TestForgotPasswordLimit:
    def test_returns_string(self):
        result = forgot_password_limit()
        assert isinstance(result, str)

    def test_non_empty(self):
        assert forgot_password_limit() != ""

    def test_matches_settings(self):
        from app.config.settings import settings

        assert forgot_password_limit() == settings.FORGOT_PASSWORD_RATE_LIMIT
