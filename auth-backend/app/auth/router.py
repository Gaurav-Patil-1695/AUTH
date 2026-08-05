from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshResponse,
)
from app.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await service.register(body)


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await service.login(body, response)


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=202)
async def forgotPassword(
    body: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordResponse:
    return await service.forgotPassword(body)


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=200)
async def resetPassword(
    body: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResetPasswordResponse:
    return await service.resetPassword(body)


@router.get("/me", response_model=MeResponse, status_code=200)
async def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    return await service.me(credentials)


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    return await service.logout(request, response, credentials)


@router.post("/refresh", response_model=RefreshResponse, status_code=200)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    return await service.refresh(request, response)
