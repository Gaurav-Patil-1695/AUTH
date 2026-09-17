from typing import Any

from fastapi.responses import JSONResponse

from app.common.errors import AppException, ErrorCode


def error_response(
    code: ErrorCode,
    message: str,
    status_code: int = 400,
    details: Any | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "error": {
            "code": code.value,
            "message": message,
            "details": details,
        }
    }
    return JSONResponse(status_code=status_code, content=content)


def error_response_from_exception(exc: AppException) -> JSONResponse:
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
