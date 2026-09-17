"""Tests for app.auth.validators"""
from __future__ import annotations

import pytest

from app.auth.validators import (
    MSG_CONFIRM_PASSWORD_MISMATCH,
    MSG_CONFIRM_PASSWORD_REQUIRED,
    MSG_EMAIL_ALREADY_REGISTERED,
    MSG_EMAIL_INVALID,
    MSG_EMAIL_MAX_LENGTH,
    MSG_EMAIL_REQUIRED,
    MSG_FULL_NAME_MAX_LENGTH,
    MSG_FULL_NAME_REQUIRED,
    MSG_LOGIN_INVALID,
    MSG_PASSWORD_LOWERCASE,
    MSG_PASSWORD_MIN_LENGTH,
    MSG_PASSWORD_NUMBER,
    MSG_PASSWORD_REQUIRED,
    MSG_PASSWORD_UPPERCASE,
    MSG_TERMS_REQUIRED,
    MSG_TOKEN_INVALID,
    MSG_TOKEN_REQUIRED,
    collect_registration_errors,
    collect_reset_password_errors,
    validate_confirm_password,
    validate_email,
    validate_full_name,
    validate_password,
    validate_reset_token,
    validate_terms_accepted,
)


# ---------------------------------------------------------------------------
# validate_full_name
# ---------------------------------------------------------------------------

class TestValidateFullName:
    def test_valid_name(self):
        assert validate_full_name("Alice Smith") is None

    def test_none_returns_required(self):
        assert validate_full_name(None) == MSG_FULL_NAME_REQUIRED

    def test_empty_string_returns_required(self):
        assert validate_full_name("") == MSG_FULL_NAME_REQUIRED

    def test_whitespace_only_returns_required(self):
        assert validate_full_name("   ") == MSG_FULL_NAME_REQUIRED

    def test_exactly_100_chars_is_valid(self):
        assert validate_full_name("A" * 100) is None

    def test_101_chars_returns_max_length(self):
        assert validate_full_name("A" * 101) == MSG_FULL_NAME_MAX_LENGTH

    def test_single_character(self):
        assert validate_full_name("X") is None


# ---------------------------------------------------------------------------
# validate_email
# ---------------------------------------------------------------------------

class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("user@example.com") is None

    def test_none_returns_required(self):
        assert validate_email(None) == MSG_EMAIL_REQUIRED

    def test_empty_string_returns_required(self):
        assert validate_email("") == MSG_EMAIL_REQUIRED

    def test_whitespace_only_returns_required(self):
        assert validate_email("   ") == MSG_EMAIL_REQUIRED

    def test_255_chars_returns_max_length(self):
        # build an email that is 255 chars long
        local = "a" * 243
        email = f"{local}@example.com"  # 243 + 12 = 255
        assert validate_email(email) == MSG_EMAIL_MAX_LENGTH

    def test_exactly_254_chars_is_valid(self):
        local = "a" * 242
        email = f"{local}@example.com"  # 242 + 12 = 254
        assert validate_email(email) is None

    def test_missing_at_symbol(self):
        assert validate_email("userexample.com") == MSG_EMAIL_INVALID

    def test_missing_domain(self):
        assert validate_email("user@") == MSG_EMAIL_INVALID

    def test_missing_local(self):
        assert validate_email("@example.com") == MSG_EMAIL_INVALID

    def test_subdomain_email(self):
        assert validate_email("user@mail.example.co.uk") is None

    def test_plus_sign_in_local(self):
        assert validate_email("user+tag@example.com") is None


# ---------------------------------------------------------------------------
# validate_password
# ---------------------------------------------------------------------------

class TestValidatePassword:
    def test_valid_password(self):
        assert validate_password("SecurePass1") == []

    def test_none_returns_required_only(self):
        errors = validate_password(None)
        assert errors == [MSG_PASSWORD_REQUIRED]

    def test_empty_string_returns_required_only(self):
        errors = validate_password("")
        assert errors == [MSG_PASSWORD_REQUIRED]

    def test_too_short(self):
        errors = validate_password("Sh1")
        assert MSG_PASSWORD_MIN_LENGTH in errors

    def test_exactly_8_chars(self):
        errors = validate_password("Secure1a")
        assert MSG_PASSWORD_MIN_LENGTH not in errors

    def test_missing_uppercase(self):
        errors = validate_password("securepass1")
        assert MSG_PASSWORD_UPPERCASE in errors

    def test_missing_lowercase(self):
        errors = validate_password("SECUREPASS1")
        assert MSG_PASSWORD_LOWERCASE in errors

    def test_missing_number(self):
        errors = validate_password("SecurePass")
        assert MSG_PASSWORD_NUMBER in errors

    def test_multiple_errors_all_present(self):
        # lowercase only, too short
        errors = validate_password("ab")
        assert MSG_PASSWORD_MIN_LENGTH in errors
        assert MSG_PASSWORD_UPPERCASE in errors
        assert MSG_PASSWORD_NUMBER in errors

    def test_order_min_length_before_uppercase(self):
        # When too short AND no uppercase, min_length should appear before uppercase
        errors = validate_password("ab")
        assert errors.index(MSG_PASSWORD_MIN_LENGTH) < errors.index(MSG_PASSWORD_UPPERCASE)

    def test_special_character_not_required(self):
        # Special chars not required; valid without them
        assert validate_password("SecurePass1") == []


# ---------------------------------------------------------------------------
# validate_confirm_password
# ---------------------------------------------------------------------------

class TestValidateConfirmPassword:
    def test_matching_passwords(self):
        assert validate_confirm_password("Pass1word", "Pass1word") is None

    def test_none_confirm(self):
        assert validate_confirm_password(None, "Pass1word") == MSG_CONFIRM_PASSWORD_REQUIRED

    def test_empty_confirm(self):
        assert validate_confirm_password("", "Pass1word") == MSG_CONFIRM_PASSWORD_REQUIRED

    def test_mismatch(self):
        assert validate_confirm_password("Pass1word", "DifferentPass1") == MSG_CONFIRM_PASSWORD_MISMATCH

    def test_mismatch_when_password_is_none(self):
        # confirm provided but password is None -> mismatch
        assert validate_confirm_password("somevalue", None) == MSG_CONFIRM_PASSWORD_MISMATCH


# ---------------------------------------------------------------------------
# validate_reset_token
# ---------------------------------------------------------------------------

class TestValidateResetToken:
    def test_valid_token(self):
        assert validate_reset_token("abc123") is None

    def test_none_token(self):
        assert validate_reset_token(None) == MSG_TOKEN_REQUIRED

    def test_empty_token(self):
        assert validate_reset_token("") == MSG_TOKEN_REQUIRED

    def test_whitespace_token(self):
        assert validate_reset_token("   ") == MSG_TOKEN_REQUIRED


# ---------------------------------------------------------------------------
# validate_terms_accepted
# ---------------------------------------------------------------------------

class TestValidateTermsAccepted:
    def test_true_passes(self):
        assert validate_terms_accepted(True) is None

    def test_false_fails(self):
        assert validate_terms_accepted(False) == MSG_TERMS_REQUIRED

    def test_none_fails(self):
        assert validate_terms_accepted(None) == MSG_TERMS_REQUIRED


# ---------------------------------------------------------------------------
# collect_registration_errors
# ---------------------------------------------------------------------------

class TestCollectRegistrationErrors:
    def _valid_kwargs(self):
        return dict(
            full_name="Alice Smith",
            email="alice@example.com",
            password="SecurePass1",
            confirm_password="SecurePass1",
            terms_accepted=True,
        )

    def test_all_valid_returns_empty(self):
        assert collect_registration_errors(**self._valid_kwargs()) == {}

    def test_missing_full_name(self):
        kwargs = self._valid_kwargs()
        kwargs["full_name"] = None
        errors = collect_registration_errors(**kwargs)
        assert "full_name" in errors
        assert errors["full_name"] == [MSG_FULL_NAME_REQUIRED]

    def test_missing_email(self):
        kwargs = self._valid_kwargs()
        kwargs["email"] = ""
        errors = collect_registration_errors(**kwargs)
        assert "email" in errors

    def test_invalid_email(self):
        kwargs = self._valid_kwargs()
        kwargs["email"] = "not-an-email"
        errors = collect_registration_errors(**kwargs)
        assert "email" in errors
        assert errors["email"] == [MSG_EMAIL_INVALID]

    def test_weak_password(self):
        kwargs = self._valid_kwargs()
        kwargs["password"] = "short"
        kwargs["confirm_password"] = "short"
        errors = collect_registration_errors(**kwargs)
        assert "password" in errors
        assert MSG_PASSWORD_MIN_LENGTH in errors["password"]

    def test_password_mismatch(self):
        kwargs = self._valid_kwargs()
        kwargs["confirm_password"] = "DifferentPass1"
        errors = collect_registration_errors(**kwargs)
        assert "confirm_password" in errors
        assert errors["confirm_password"] == [MSG_CONFIRM_PASSWORD_MISMATCH]

    def test_terms_not_accepted(self):
        kwargs = self._valid_kwargs()
        kwargs["terms_accepted"] = False
        errors = collect_registration_errors(**kwargs)
        assert "terms_accepted" in errors
        assert errors["terms_accepted"] == [MSG_TERMS_REQUIRED]

    def test_multiple_fields_invalid(self):
        errors = collect_registration_errors(
            full_name=None,
            email=None,
            password=None,
            confirm_password=None,
            terms_accepted=False,
        )
        assert "full_name" in errors
        assert "email" in errors
        assert "password" in errors
        assert "terms_accepted" in errors


# ---------------------------------------------------------------------------
# collect_reset_password_errors
# ---------------------------------------------------------------------------

class TestCollectResetPasswordErrors:
    def _valid_kwargs(self):
        return dict(
            token="valid-reset-token",
            password="SecurePass1",
            confirm_password="SecurePass1",
        )

    def test_all_valid_returns_empty(self):
        assert collect_reset_password_errors(**self._valid_kwargs()) == {}

    def test_missing_token(self):
        kwargs = self._valid_kwargs()
        kwargs["token"] = None
        errors = collect_reset_password_errors(**kwargs)
        assert "token" in errors
        assert errors["token"] == [MSG_TOKEN_REQUIRED]

    def test_whitespace_token(self):
        kwargs = self._valid_kwargs()
        kwargs["token"] = "   "
        errors = collect_reset_password_errors(**kwargs)
        assert "token" in errors

    def test_weak_password(self):
        kwargs = self._valid_kwargs()
        kwargs["password"] = "weak"
        kwargs["confirm_password"] = "weak"
        errors = collect_reset_password_errors(**kwargs)
        assert "password" in errors

    def test_password_mismatch(self):
        kwargs = self._valid_kwargs()
        kwargs["confirm_password"] = "Different1"
        errors = collect_reset_password_errors(**kwargs)
        assert "confirm_password" in errors

    def test_all_invalid(self):
        errors = collect_reset_password_errors(
            token=None,
            password=None,
            confirm_password=None,
        )
        assert "token" in errors
        assert "password" in errors
        # confirm_password missing check still triggered
        assert "confirm_password" in errors


# ---------------------------------------------------------------------------
# Constant sanity checks
# ---------------------------------------------------------------------------

class TestMessageConstants:
    def test_email_already_registered_defined(self):
        assert MSG_EMAIL_ALREADY_REGISTERED

    def test_login_invalid_defined(self):
        assert MSG_LOGIN_INVALID

    def test_token_invalid_defined(self):
        assert MSG_TOKEN_INVALID
