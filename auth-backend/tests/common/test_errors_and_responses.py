import json
import pytest

from app.common.errors import (
    AppError,
    AppException,
    EmailTakenError,
    ErrorCode,
    InternalError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitedError,
    UnauthorizedError,
    ValidationError,
)
from app.common.responses import error_response, error_response_from_exception


# ---------------------------------------------------------------------------
# ErrorCode
# ---------------------------------------------------------------------------

class TestErrorCode:
    def test_all_members_are_strings(self):
        for member in ErrorCode:
            assert isinstance(member.value, str)

    def test_expected_members_exist(self):
        names = {m.name for m in ErrorCode}
        assert names == {
            "VALIDATION_ERROR",
            "INVALID_CREDENTIALS",
            "EMAIL_TAKEN",
            "INVALID_TOKEN",
            "UNAUTHORIZED",
            "RATE_LIMITED",
            "INTERNAL_ERROR",
        }

    def test_value_equals_name(self):
        for member in ErrorCode:
            assert member.value == member.name


# ---------------------------------------------------------------------------
# AppError
# ---------------------------------------------------------------------------

class TestAppError:
    def test_basic_construction(self):
        err = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Something went wrong",
            status_code=500,
        )
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert err.message == "Something went wrong"
        assert err.status_code == 500
        assert err.details is None

    def test_default_status_code_is_400(self):
        err = AppError(code=ErrorCode.VALIDATION_ERROR, message="bad")
        assert err.status_code == 400

    def test_details_stored(self):
        details = {"field": "email", "reason": "invalid"}
        err = AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad",
            details=details,
        )
        assert err.details == details

    def test_is_exception(self):
        err = AppError(code=ErrorCode.INTERNAL_ERROR, message="oops")
        assert isinstance(err, Exception)

    def test_str_is_message(self):
        err = AppError(code=ErrorCode.INTERNAL_ERROR, message="oops")
        assert str(err) == "oops"

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AppError) as exc_info:
            raise AppError(code=ErrorCode.UNAUTHORIZED, message="nope", status_code=401)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# AppException alias
# ---------------------------------------------------------------------------

class TestAppExceptionAlias:
    def test_alias_is_same_class(self):
        assert AppException is AppError

    def test_instance_check(self):
        err = AppError(code=ErrorCode.INTERNAL_ERROR, message="x")
        assert isinstance(err, AppException)


# ---------------------------------------------------------------------------
# ValidationError
# ---------------------------------------------------------------------------

class TestValidationError:
    def test_defaults(self):
        err = ValidationError(message="invalid input")
        assert err.code == ErrorCode.VALIDATION_ERROR
        assert err.status_code == 422
        assert err.message == "invalid input"
        assert err.details is None

    def test_with_details(self):
        details = [{"loc": ["body", "email"], "msg": "invalid"}]
        err = ValidationError(message="bad", details=details)
        assert err.details == details

    def test_is_app_error(self):
        assert isinstance(ValidationError("x"), AppError)


# ---------------------------------------------------------------------------
# InvalidCredentialsError
# ---------------------------------------------------------------------------

class TestInvalidCredentialsError:
    def test_defaults(self):
        err = InvalidCredentialsError()
        assert err.code == ErrorCode.INVALID_CREDENTIALS
        assert err.status_code == 401
        assert err.message == "Invalid email or password."

    def test_custom_message(self):
        err = InvalidCredentialsError(message="Wrong password.")
        assert err.message == "Wrong password."

    def test_is_app_error(self):
        assert isinstance(InvalidCredentialsError(), AppError)


# ---------------------------------------------------------------------------
# EmailTakenError
# ---------------------------------------------------------------------------

class TestEmailTakenError:
    def test_defaults(self):
        err = EmailTakenError()
        assert err.code == ErrorCode.EMAIL_TAKEN
        assert err.status_code == 409
        assert err.message == "An account with this email already exists."

    def test_custom_message(self):
        err = EmailTakenError(message="Email in use.")
        assert err.message == "Email in use."

    def test_is_app_error(self):
        assert isinstance(EmailTakenError(), AppError)


# ---------------------------------------------------------------------------
# InvalidTokenError
# ---------------------------------------------------------------------------

class TestInvalidTokenError:
    def test_defaults(self):
        err = InvalidTokenError()
        assert err.code == ErrorCode.INVALID_TOKEN
        assert err.status_code == 400
        assert err.message == "This link is invalid or has expired."

    def test_custom_message(self):
        err = InvalidTokenError(message="Token expired.")
        assert err.message == "Token expired."

    def test_is_app_error(self):
        assert isinstance(InvalidTokenError(), AppError)


# ---------------------------------------------------------------------------
# UnauthorizedError
# ---------------------------------------------------------------------------

class TestUnauthorizedError:
    def test_defaults(self):
        err = UnauthorizedError()
        assert err.code == ErrorCode.UNAUTHORIZED
        assert err.status_code == 401
        assert err.message == "Authentication required."

    def test_custom_message(self):
        err = UnauthorizedError(message="Please log in.")
        assert err.message == "Please log in."

    def test_is_app_error(self):
        assert isinstance(UnauthorizedError(), AppError)


# ---------------------------------------------------------------------------
# RateLimitedError
# ---------------------------------------------------------------------------

class TestRateLimitedError:
    def test_defaults(self):
        err = RateLimitedError()
        assert err.code == ErrorCode.RATE_LIMITED
        assert err.status_code == 429
        assert err.message == "Too many attempts. Please try again later."

    def test_custom_message(self):
        err = RateLimitedError(message="Slow down.")
        assert err.message == "Slow down."

    def test_is_app_error(self):
        assert isinstance(RateLimitedError(), AppError)


# ---------------------------------------------------------------------------
# InternalError
# ---------------------------------------------------------------------------

class TestInternalError:
    def test_defaults(self):
        err = InternalError()
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert err.status_code == 500
        assert err.message == "An unexpected error occurred. Please try again."

    def test_custom_message(self):
        err = InternalError(message="DB is down.")
        assert err.message == "DB is down."

    def test_is_app_error(self):
        assert isinstance(InternalError(), AppError)


# ---------------------------------------------------------------------------
# error_response
# ---------------------------------------------------------------------------

class TestErrorResponse:
    def _decode_body(self, response):
        """Decode JSONResponse body bytes to dict."""
        return json.loads(response.body)

    def test_status_code(self):
        resp = error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="oops",
            status_code=500,
        )
        assert resp.status_code == 500

    def test_default_status_code(self):
        resp = error_response(code=ErrorCode.VALIDATION_ERROR, message="bad")
        assert resp.status_code == 400

    def test_body_structure(self):
        resp = error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="no access",
            status_code=401,
        )
        body = self._decode_body(resp)
        assert "error" in body
        assert body["error"]["code"] == "UNAUTHORIZED"
        assert body["error"]["message"] == "no access"
        assert body["error"]["details"] is None

    def test_body_with_details(self):
        details = {"field": "email"}
        resp = error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad email",
            status_code=422,
            details=details,
        )
        body = self._decode_body(resp)
        assert body["error"]["details"] == details

    def test_code_value_is_string(self):
        resp = error_response(code=ErrorCode.EMAIL_TAKEN, message="taken")
        body = self._decode_body(resp)
        assert body["error"]["code"] == "EMAIL_TAKEN"


# ---------------------------------------------------------------------------
# error_response_from_exception
# ---------------------------------------------------------------------------

class TestErrorResponseFromException:
    def _decode_body(self, response):
        return json.loads(response.body)

    def test_validation_error(self):
        exc = ValidationError(message="bad value", details={"field": "name"})
        resp = error_response_from_exception(exc)
        assert resp.status_code == 422
        body = self._decode_body(resp)
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "bad value"
        assert body["error"]["details"] == {"field": "name"}

    def test_invalid_credentials_error(self):
        exc = InvalidCredentialsError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 401
        body = self._decode_body(resp)
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    def test_email_taken_error(self):
        exc = EmailTakenError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 409
        body = self._decode_body(resp)
        assert body["error"]["code"] == "EMAIL_TAKEN"

    def test_invalid_token_error(self):
        exc = InvalidTokenError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 400
        body = self._decode_body(resp)
        assert body["error"]["code"] == "INVALID_TOKEN"

    def test_unauthorized_error(self):
        exc = UnauthorizedError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 401
        body = self._decode_body(resp)
        assert body["error"]["code"] == "UNAUTHORIZED"

    def test_rate_limited_error(self):
        exc = RateLimitedError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 429
        body = self._decode_body(resp)
        assert body["error"]["code"] == "RATE_LIMITED"

    def test_internal_error(self):
        exc = InternalError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 500
        body = self._decode_body(resp)
        assert body["error"]["code"] == "INTERNAL_ERROR"

    def test_generic_app_error(self):
        exc = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="generic",
            status_code=503,
            details="extra info",
        )
        resp = error_response_from_exception(exc)
        assert resp.status_code == 503
        body = self._decode_body(resp)
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "generic"
        assert body["error"]["details"] == "extra info"

    def test_details_none_when_not_provided(self):
        exc = UnauthorizedError()
        resp = error_response_from_exception(exc)
        body = self._decode_body(resp)
        assert body["error"]["details"] is None
