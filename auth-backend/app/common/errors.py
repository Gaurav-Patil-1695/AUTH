from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


# Keep old name as alias for backward compatibility
AppException = AppError


class ValidationError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=422,
            details=details,
        )


class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Invalid email or password.") -> None:
        super().__init__(
            code=ErrorCode.INVALID_CREDENTIALS,
            message=message,
            status_code=401,
        )


class EmailTakenError(AppError):
    def __init__(
        self,
        message: str = "An account with this email already exists.",
    ) -> None:
        super().__init__(
            code=ErrorCode.EMAIL_TAKEN,
            message=message,
            status_code=409,
        )


class InvalidTokenError(AppError):
    def __init__(
        self, message: str = "This link is invalid or has expired."
    ) -> None:
        super().__init__(
            code=ErrorCode.INVALID_TOKEN,
            message=message,
            status_code=400,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401,
        )


class RateLimitedError(AppError):
    def __init__(
        self,
        message: str = "Too many attempts. Please try again later.",
    ) -> None:
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message=message,
            status_code=429,
        )


class InternalError(AppError):
    def __init__(
        self,
        message: str = "An unexpected error occurred. Please try again.",
    ) -> None:
        super().__init__(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            status_code=500,
        )
