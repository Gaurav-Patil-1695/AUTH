from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Password policy constants (mirrors capabilities.yaml)
# ---------------------------------------------------------------------------

PASSWORD_MIN_LENGTH: int = 8
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_LOWERCASE: bool = True
PASSWORD_REQUIRE_NUMBER: bool = True
PASSWORD_REQUIRE_SPECIAL: bool = False  # require_special_character=false

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_NUMBER_RE = re.compile(r"[0-9]")
# RFC-5322 simplified pattern — same rule used by the frontend
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


# ---------------------------------------------------------------------------
# Validation messages — copied VERBATIM from validation-rules.md
# ---------------------------------------------------------------------------

MSG_FULL_NAME_REQUIRED: str = "Full name is required."
MSG_FULL_NAME_MAX_LENGTH: str = "Full name must not exceed 100 characters."

MSG_EMAIL_REQUIRED: str = "Email address is required."
MSG_EMAIL_INVALID: str = "Enter a valid email address."
MSG_EMAIL_MAX_LENGTH: str = "Email must not exceed 254 characters."
MSG_EMAIL_ALREADY_REGISTERED: str = "An account with this email already exists."

MSG_PASSWORD_REQUIRED: str = "Password is required."
MSG_PASSWORD_MIN_LENGTH: str = "Password must be at least 8 characters."
MSG_PASSWORD_UPPERCASE: str = "Password must contain at least one uppercase letter."
MSG_PASSWORD_LOWERCASE: str = "Password must contain at least one lowercase letter."
MSG_PASSWORD_NUMBER: str = "Password must contain at least one number."

MSG_CONFIRM_PASSWORD_REQUIRED: str = "Please confirm your password."
MSG_CONFIRM_PASSWORD_MISMATCH: str = "Passwords do not match."

MSG_LOGIN_INVALID: str = "Invalid email or password."

MSG_TOKEN_REQUIRED: str = "Reset token is required."
MSG_TOKEN_INVALID: str = "This password reset link is invalid or has expired."

MSG_TERMS_REQUIRED: str = "You must accept the terms and conditions."


# ---------------------------------------------------------------------------
# Field-level validators
# (Each function returns None on success or the exact error message string.)
# ---------------------------------------------------------------------------

def validate_full_name(full_name: str | None) -> str | None:
    """Validate the full_name field; return error message or None."""
    if not full_name or not full_name.strip():
        return MSG_FULL_NAME_REQUIRED
    if len(full_name) > 100:
        return MSG_FULL_NAME_MAX_LENGTH
    return None


def validate_email(email: str | None) -> str | None:
    """Validate the email field; return error message or None."""
    if not email or not email.strip():
        return MSG_EMAIL_REQUIRED
    if len(email) > 254:
        return MSG_EMAIL_MAX_LENGTH
    if not _EMAIL_RE.match(email):
        return MSG_EMAIL_INVALID
    return None


def validate_password(password: str | None) -> list[str]:
    """Validate a new password against the policy.

    Returns a list of error messages in the order specified by
    validation-rules.md (empty list == valid).
    """
    errors: list[str] = []

    if not password:
        errors.append(MSG_PASSWORD_REQUIRED)
        return errors  # remaining checks are meaningless without a value

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(MSG_PASSWORD_MIN_LENGTH)

    if PASSWORD_REQUIRE_UPPERCASE and not _UPPERCASE_RE.search(password):
        errors.append(MSG_PASSWORD_UPPERCASE)

    if PASSWORD_REQUIRE_LOWERCASE and not _LOWERCASE_RE.search(password):
        errors.append(MSG_PASSWORD_LOWERCASE)

    if PASSWORD_REQUIRE_NUMBER and not _NUMBER_RE.search(password):
        errors.append(MSG_PASSWORD_NUMBER)

    return errors


def validate_confirm_password(
    confirm_password: str | None, password: str | None
) -> str | None:
    """Validate the confirm_password field; return error message or None."""
    if not confirm_password:
        return MSG_CONFIRM_PASSWORD_REQUIRED
    if confirm_password != password:
        return MSG_CONFIRM_PASSWORD_MISMATCH
    return None


def validate_reset_token(token: str | None) -> str | None:
    """Validate the presence of a reset token; return error message or None."""
    if not token or not token.strip():
        return MSG_TOKEN_REQUIRED
    return None


def validate_terms_accepted(accepted: bool | None) -> str | None:
    """Validate that the terms-and-conditions checkbox was ticked."""
    if not accepted:
        return MSG_TERMS_REQUIRED
    return None


# ---------------------------------------------------------------------------
# Composite validators used by the service layer
# ---------------------------------------------------------------------------

def collect_registration_errors(
    *,
    full_name: str | None,
    email: str | None,
    password: str | None,
    confirm_password: str | None,
    terms_accepted: bool | None,
) -> dict[str, list[str]]:
    """Run all registration field validators and return a dict of field -> [messages].

    The dict is empty when all fields pass.
    Rule order within each field matches validation-rules.md.
    """
    errors: dict[str, list[str]] = {}

    full_name_error = validate_full_name(full_name)
    if full_name_error:
        errors["full_name"] = [full_name_error]

    email_error = validate_email(email)
    if email_error:
        errors["email"] = [email_error]

    password_errors = validate_password(password)
    if password_errors:
        errors["password"] = password_errors

    confirm_error = validate_confirm_password(confirm_password, password)
    if confirm_error:
        errors["confirm_password"] = [confirm_error]

    terms_error = validate_terms_accepted(terms_accepted)
    if terms_error:
        errors["terms_accepted"] = [terms_error]

    return errors


def collect_reset_password_errors(
    *,
    token: str | None,
    password: str | None,
    confirm_password: str | None,
) -> dict[str, list[str]]:
    """Run all reset-password field validators and return a dict of
    field -> [messages]."""
    errors: dict[str, list[str]] = {}

    token_error = validate_reset_token(token)
    if token_error:
        errors["token"] = [token_error]

    password_errors = validate_password(password)
    if password_errors:
        errors["password"] = password_errors

    confirm_error = validate_confirm_password(confirm_password, password)
    if confirm_error:
        errors["confirm_password"] = [confirm_error]

    return errors
