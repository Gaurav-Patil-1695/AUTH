"""Unit tests for app.core.security."""
from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    compare_token,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("secret")
        assert isinstance(result, str)

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("secret")
        h2 = hash_password("secret")
        # bcrypt uses random salts — two hashes must differ
        assert h1 != h2

    def test_starts_with_bcrypt_prefix(self):
        result = hash_password("secret")
        assert result.startswith("$2b$") or result.startswith("$2a$")

    def test_empty_password(self):
        result = hash_password("")
        assert isinstance(result, str)
        assert len(result) > 0


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        pw = "correct-horse-battery"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("right")
        assert verify_password("wrong", hashed) is False

    def test_empty_plain_against_hash_of_empty(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_invalid_hash_returns_false(self):
        # Passing a garbage hash must not raise, should return False
        assert verify_password("password", "not-a-valid-hash") is False

    def test_empty_hash_returns_false(self):
        assert verify_password("password", "") is False


# ---------------------------------------------------------------------------
# Token hashing (SHA-256)
# ---------------------------------------------------------------------------


class TestHashToken:
    def test_returns_hex_string(self):
        result = hash_token("mytoken")
        assert isinstance(result, str)
        # SHA-256 hex digest is always 64 hex characters
        assert len(result) == 64

    def test_deterministic(self):
        assert hash_token("abc") == hash_token("abc")

    def test_different_tokens_produce_different_hashes(self):
        assert hash_token("tokenA") != hash_token("tokenB")

    def test_empty_token(self):
        result = hash_token("")
        assert len(result) == 64


class TestCompareToken:
    def test_matching_token_returns_true(self):
        raw = "supersecrettoken"
        stored = hash_token(raw)
        assert compare_token(raw, stored) is True

    def test_wrong_token_returns_false(self):
        stored = hash_token("correct")
        assert compare_token("wrong", stored) is False

    def test_empty_token_matches_its_own_hash(self):
        stored = hash_token("")
        assert compare_token("", stored) is True

    def test_case_sensitive(self):
        stored = hash_token("Token")
        assert compare_token("token", stored) is False


# ---------------------------------------------------------------------------
# JWT access token
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(subject=42)
        assert isinstance(token, str)

    def test_token_is_decodable(self):
        token = create_access_token(subject=1)
        payload = decode_access_token(token)
        assert payload["sub"] == "1"

    def test_subject_stored_as_string(self):
        token = create_access_token(subject=99)
        payload = decode_access_token(token)
        assert payload["sub"] == "99"

    def test_string_subject(self):
        token = create_access_token(subject="user-uuid")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-uuid"

    def test_type_claim_is_access(self):
        token = create_access_token(subject=1)
        payload = decode_access_token(token)
        assert payload["type"] == "access"

    def test_additional_claims_merged(self):
        token = create_access_token(subject=1, additional_claims={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_custom_expires_delta(self):
        token = create_access_token(subject=1, expires_delta=timedelta(hours=2))
        payload = decode_access_token(token)
        # exp should exist and the token should be valid
        assert "exp" in payload

    def test_expired_token_raises(self):
        token = create_access_token(subject=1, expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_iat_claim_present(self):
        token = create_access_token(subject=1)
        payload = decode_access_token(token)
        assert "iat" in payload


class TestDecodeAccessToken:
    def test_tampered_token_raises(self):
        token = create_access_token(subject=1)
        tampered = token[:-4] + "XXXX"
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_garbage_token_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.jwt")

    def test_refresh_token_rejected_by_decode_access(self):
        # A refresh token must not be accepted as an access token
        refresh = create_refresh_token(subject=1)
        with pytest.raises(JWTError):
            decode_access_token(refresh)


# ---------------------------------------------------------------------------
# JWT refresh token
# ---------------------------------------------------------------------------


class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token(subject=1)
        assert isinstance(token, str)

    def test_type_claim_is_refresh(self):
        token = create_refresh_token(subject=1)
        payload = decode_refresh_token(token)
        assert payload["type"] == "refresh"

    def test_remember_me_false_by_default(self):
        token = create_refresh_token(subject=1)
        payload = decode_refresh_token(token)
        assert payload["remember_me"] is False

    def test_remember_me_true_propagated(self):
        token = create_refresh_token(subject=1, remember_me=True)
        payload = decode_refresh_token(token)
        assert payload["remember_me"] is True

    def test_subject_stored_as_string(self):
        token = create_refresh_token(subject=7)
        payload = decode_refresh_token(token)
        assert payload["sub"] == "7"

    def test_custom_expires_delta(self):
        token = create_refresh_token(subject=1, expires_delta=timedelta(days=30))
        payload = decode_refresh_token(token)
        assert "exp" in payload

    def test_expired_token_raises(self):
        token = create_refresh_token(subject=1, expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_refresh_token(token)

    def test_remember_me_longer_expiry_than_default(self):
        """remember_me=True should produce a later expiry than the default."""
        from app.config.settings import settings

        default_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        remember_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER)
        # Only assert when the two settings actually differ
        if remember_delta > default_delta:
            t_default = create_refresh_token(subject=1, remember_me=False)
            t_remember = create_refresh_token(subject=1, remember_me=True)
            p_default = decode_refresh_token(t_default)
            p_remember = decode_refresh_token(t_remember)
            assert p_remember["exp"] > p_default["exp"]


class TestDecodeRefreshToken:
    def test_tampered_token_raises(self):
        token = create_refresh_token(subject=1)
        tampered = token[:-4] + "XXXX"
        with pytest.raises(JWTError):
            decode_refresh_token(tampered)

    def test_garbage_token_raises(self):
        with pytest.raises(JWTError):
            decode_refresh_token("not.a.jwt")

    def test_access_token_rejected_by_decode_refresh(self):
        access = create_access_token(subject=1)
        with pytest.raises(JWTError):
            decode_refresh_token(access)
