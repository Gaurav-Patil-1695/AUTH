from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.auth.service import AuthService
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="register",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    service = AuthService(db)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    operation_id="login",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    service = AuthService(db)
    return await service.login(payload, response)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="forgotPassword",
)
async def forgotPassword(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    service = AuthService(db)
    return await service.forgotPassword(payload)


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    operation_id="resetPassword",
)
async def resetPassword(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ResetPasswordResponse:
    service = AuthService(db)
    return await service.resetPassword(payload)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="me",
)
async def me(
    current_user=Depends(get_current_user),
) -> MeResponse:
    return MeResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    operation_id="logout",
)
async def logout(
    response: Response,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutResponse:
    service = AuthService(db)
    return await service.logout(current_user, response)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    operation_id="refresh",
)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    service = AuthService(db)
    return await service.refresh(response)
