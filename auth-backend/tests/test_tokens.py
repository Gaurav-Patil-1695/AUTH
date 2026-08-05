"""Tests for app.auth.tokens"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from jose import jwt

from app.auth import tokens as token_module
from app.auth.tokens import (
    ALGORITHM,
    ACCESS_TOKEN_TTL,
    REFRESH_TOKEN_TTL_EXTENDED,
    REFRESH_TOKEN_TTL_STANDARD,
    RESET_TOKEN_TTL,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_access_token,
    hash_token,
    is_refresh_token_valid,
    is_reset_token_valid,
    rotate_refresh_token,
)
from app.config.settings import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _fixed_utcnow():
    return NOW


# ---------------------------------------------------------------------------
# hash_token
# ---------------------------------------------------------------------------

class TestHashToken:
    def test_returns_sha256_hex(self):
        raw = "hello"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert hash_token(raw) == expected

    def test_deterministic(self):
        assert hash_token("token") == hash_token("token")

    def test_different_inputs_different_hashes(self):
        assert hash_token("abc") != hash_token("xyz")

    def test_returns_64_char_hex(self):
        assert len(hash_token("test")) == 64


# ---------------------------------------------------------------------------
# create_access_token / decode_access_token
# ---------------------------------------------------------------------------

class TestAccessToken:
    def test_create_returns_two_tuple(self):
        result = create_access_token(42)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_token_is_string(self):
        token, _ = create_access_token(42)
        assert isinstance(token, str) and len(token) > 0

    def test_expires_at_is_utc_datetime(self):
        _, expires_at = create_access_token(42)
        assert isinstance(expires_at, datetime)
        assert expires_at.tzinfo is not None

    def test_expires_at_is_approximately_correct(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            _, expires_at = create_access_token(1)
        expected = NOW + ACCESS_TOKEN_TTL
        assert expires_at == expected

    def test_decode_returns_correct_user_id(self):
        token, _ = create_access_token(99)
        assert decode_access_token(token) == 99

    def test_decode_invalid_token_returns_none(self):
        assert decode_access_token("not.a.jwt") is None

    def test_decode_empty_string_returns_none(self):
        assert decode_access_token("") is None

    def test_decode_wrong_type_claim_returns_none(self):
        # Manually create a token with type != "access"
        payload = {
            "sub": "1",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
            "type": "refresh",
        }
        bad_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        assert decode_access_token(bad_token) is None

    def test_decode_token_without_sub_returns_none(self):
        payload = {
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        assert decode_access_token(token) is None

    def test_decode_expired_token_returns_none(self):
        with patch.object(token_module, "_utcnow", lambda: NOW - timedelta(hours=2)):
            token, _ = create_access_token(7)
        # Now time has moved forward past expiry; jose will reject it
        assert decode_access_token(token) is None

    def test_decode_wrong_secret_returns_none(self):
        payload = {
            "sub": "1",
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
            "type": "access",
        }
        token = jwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)
        assert decode_access_token(token) is None


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------

class TestCreateRefreshToken:
    def test_returns_three_tuple(self):
        result = create_refresh_token()
        assert len(result) == 3

    def test_raw_token_is_string(self):
        raw, _, _ = create_refresh_token()
        assert isinstance(raw, str) and len(raw) > 0

    def test_token_hash_matches_hash_of_raw(self):
        raw, token_hash, _ = create_refresh_token()
        assert token_hash == hash_token(raw)

    def test_expires_at_standard_ttl(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            _, _, expires_at = create_refresh_token(remember_me=False)
        assert expires_at == NOW + REFRESH_TOKEN_TTL_STANDARD

    def test_expires_at_extended_ttl(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            _, _, expires_at = create_refresh_token(remember_me=True)
        assert expires_at == NOW + REFRESH_TOKEN_TTL_EXTENDED

    def test_extended_ttl_longer_than_standard(self):
        assert REFRESH_TOKEN_TTL_EXTENDED > REFRESH_TOKEN_TTL_STANDARD

    def test_tokens_are_unique(self):
        raw1, _, _ = create_refresh_token()
        raw2, _, _ = create_refresh_token()
        assert raw1 != raw2


# ---------------------------------------------------------------------------
# create_reset_token
# ---------------------------------------------------------------------------

class TestCreateResetToken:
    def test_returns_three_tuple(self):
        assert len(create_reset_token()) == 3

    def test_raw_token_is_string(self):
        raw, _, _ = create_reset_token()
        assert isinstance(raw, str) and len(raw) > 0

    def test_token_hash_matches_hash_of_raw(self):
        raw, token_hash, _ = create_reset_token()
        assert token_hash == hash_token(raw)

    def test_expires_at_correct(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            _, _, expires_at = create_reset_token()
        assert expires_at == NOW + RESET_TOKEN_TTL

    def test_tokens_are_unique(self):
        raw1, _, _ = create_reset_token()
        raw2, _, _ = create_reset_token()
        assert raw1 != raw2


# ---------------------------------------------------------------------------
# rotate_refresh_token
# ---------------------------------------------------------------------------

class TestRotateRefreshToken:
    def test_returns_same_structure_as_create(self):
        result = rotate_refresh_token()
        assert len(result) == 3

    def test_remember_me_propagated(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            _, _, expires_standard = rotate_refresh_token(remember_me=False)
            _, _, expires_extended = rotate_refresh_token(remember_me=True)
        assert expires_extended > expires_standard

    def test_hash_matches_raw(self):
        raw, token_hash, _ = rotate_refresh_token()
        assert hash_token(raw) == token_hash


# ---------------------------------------------------------------------------
# is_refresh_token_valid
# ---------------------------------------------------------------------------

class TestIsRefreshTokenValid:
    def _make_row(self, *, revoked_at=None, expires_at=None):
        if expires_at is None:
            expires_at = NOW + timedelta(hours=1)
        return {"revoked_at": revoked_at, "expires_at": expires_at}

    def test_valid_token(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_refresh_token_valid(self._make_row()) is True

    def test_revoked_token_is_invalid(self):
        row = self._make_row(revoked_at=NOW - timedelta(minutes=5))
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_refresh_token_valid(row) is False

    def test_expired_token_is_invalid(self):
        row = self._make_row(expires_at=NOW - timedelta(seconds=1))
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_refresh_token_valid(row) is False

    def test_expires_at_naive_treated_as_utc(self):
        naive_expires = (NOW + timedelta(hours=1)).replace(tzinfo=None)
        row = {"revoked_at": None, "expires_at": naive_expires}
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_refresh_token_valid(row) is True

    def test_expires_at_exactly_now_is_invalid(self):
        row = self._make_row(expires_at=NOW)
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_refresh_token_valid(row) is False


# ---------------------------------------------------------------------------
# is_reset_token_valid
# ---------------------------------------------------------------------------

class TestIsResetTokenValid:
    def _make_row(self, *, used_at=None, expires_at=None):
        if expires_at is None:
            expires_at = NOW + timedelta(hours=1)
        return {"used_at": used_at, "expires_at": expires_at}

    def test_valid_token(self):
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_reset_token_valid(self._make_row()) is True

    def test_used_token_is_invalid(self):
        row = self._make_row(used_at=NOW - timedelta(minutes=1))
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_reset_token_valid(row) is False

    def test_expired_token_is_invalid(self):
        row = self._make_row(expires_at=NOW - timedelta(seconds=1))
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_reset_token_valid(row) is False

    def test_naive_expires_at_treated_as_utc(self):
        naive_expires = (NOW + timedelta(hours=1)).replace(tzinfo=None)
        row = {"used_at": None, "expires_at": naive_expires}
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_reset_token_valid(row) is True

    def test_expires_at_exactly_now_is_invalid(self):
        row = self._make_row(expires_at=NOW)
        with patch.object(token_module, "_utcnow", _fixed_utcnow):
            assert is_reset_token_valid(row) is False
