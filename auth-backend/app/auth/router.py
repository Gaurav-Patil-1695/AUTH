from fastapi import APIRouter

from app.auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutResponse,
    RefreshResponse,
)
from app.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest) -> RegisterResponse:
    return await service.register(payload)


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(payload: LoginRequest) -> LoginResponse:
    return await service.login(payload)


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=202)
async def forgotPassword(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    return await service.forgotPassword(payload)


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=200)
async def resetPassword(payload: ResetPasswordRequest) -> ResetPasswordResponse:
    return await service.resetPassword(payload)


@router.get("/me", response_model=MeResponse, status_code=200)
async def me() -> MeResponse:
    return await service.me()


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout() -> LogoutResponse:
    return await service.logout()


@router.post("/refresh", response_model=RefreshResponse, status_code=200)
async def refresh() -> RefreshResponse:
    return await service.refresh()
