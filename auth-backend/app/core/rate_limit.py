from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

# ---------------------------------------------------------------------------
# Shared limiter instance — keyed by client IP address (NFR-08)
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Per-endpoint limit strings (read from settings so they are env-driven)
# ---------------------------------------------------------------------------


def login_limit() -> str:
    """Return the rate-limit rule string for POST /auth/login."""
    return settings.LOGIN_RATE_LIMIT


def forgot_password_limit() -> str:
    """Return the rate-limit rule string for POST /auth/forgot-password."""
    return settings.FORGOT_PASSWORD_RATE_LIMIT
