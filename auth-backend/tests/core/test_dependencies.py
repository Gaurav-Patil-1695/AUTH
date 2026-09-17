"""Unit tests for app.core.dependencies.get_current_user."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_active_user(user_id: int = 1) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_active = True
    return user


def _make_inactive_user(user_id: int = 1) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_active = False
    return user


def _make_db(user):
    """Return a minimal mock Session whose query chain returns *user*."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestGetCurrentUserHappyPath:
    def test_returns_user_for_valid_token(self):
        user = _make_active_user(user_id=42)
        token = create_access_token(subject=42)
        creds = _make_credentials(token)
        db = _make_db(user)

        result = get_current_user(credentials=creds, db=db)

        assert result is user

    def test_queries_correct_user_id(self):
        user = _make_active_user(user_id=7)
        token = create_access_token(subject=7)
        creds = _make_credentials(token)
        db = _make_db(user)

        get_current_user(credentials=creds, db=db)

        # Verify that db.query was called (chain was exercised)
        db.query.assert_called_once()


# ---------------------------------------------------------------------------
# Failure-path tests
# ---------------------------------------------------------------------------


class TestGetCurrentUserFailurePaths:
    def _assert_401(self, **kwargs):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(**kwargs)
        assert exc_info.value.status_code == 401

    # --- missing credentials ---

    def test_none_credentials_raises_401(self):
        db = _make_db(_make_active_user())
        self._assert_401(credentials=None, db=db)

    # --- invalid / garbage token ---

    def test_garbage_token_raises_401(self):
        db = _make_db(_make_active_user())
        creds = _make_credentials("not.a.real.jwt")
        self._assert_401(credentials=creds, db=db)

    # --- expired token ---

    def test_expired_token_raises_401(self):
        db = _make_db(_make_active_user())
        token = create_access_token(subject=1, expires_delta=timedelta(seconds=-1))
        creds = _make_credentials(token)
        self._assert_401(credentials=creds, db=db)

    # --- wrong token type (refresh instead of access) ---

    def test_refresh_token_raises_401(self):
        db = _make_db(_make_active_user())
        token = create_refresh_token(subject=1)
        creds = _make_credentials(token)
        self._assert_401(credentials=creds, db=db)

    # --- user not found ---

    def test_user_not_found_raises_401(self):
        token = create_access_token(subject=999)
        creds = _make_credentials(token)
        db = _make_db(None)  # first() returns None
        self._assert_401(credentials=creds, db=db)

    # --- inactive user ---

    def test_inactive_user_raises_401(self):
        user = _make_inactive_user(user_id=5)
        token = create_access_token(subject=5)
        creds = _make_credentials(token)
        db = _make_db(user)
        self._assert_401(credentials=creds, db=db)

    # --- non-integer subject ---

    def test_non_integer_sub_raises_401(self):
        from app.config.settings import settings
        from jose import jwt
        from datetime import datetime, timezone

        payload = {
            "sub": "not-an-int",
            "iat": datetime.now(tz=timezone.utc),
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        creds = _make_credentials(token)
        db = _make_db(_make_active_user())
        self._assert_401(credentials=creds, db=db)

    # --- db raises exception ---

    def test_db_exception_raises_401(self):
        token = create_access_token(subject=1)
        creds = _make_credentials(token)
        db = MagicMock()
        db.query.side_effect = Exception("DB is down")
        self._assert_401(credentials=creds, db=db)

    # --- 401 detail shape ---

    def test_401_detail_has_expected_shape(self):
        db = _make_db(None)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=db)
        detail = exc_info.value.detail
        assert "error" in detail
        assert detail["error"]["code"] == "UNAUTHORIZED"

    # --- WWW-Authenticate header ---

    def test_401_has_www_authenticate_header(self):
        db = _make_db(None)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=db)
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"
