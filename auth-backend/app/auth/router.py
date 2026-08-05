from fastapi import APIRouter, Depends, Response, status

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    ErrorResponse,
)
from app.auth.service import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    status_code=status.HTTP_200_OK,
    operation_id="login",
)
async def login_endpoint(
    body: LoginRequest,
    response: Response,
) -> LoginResponse:
    return await login(body, response)
