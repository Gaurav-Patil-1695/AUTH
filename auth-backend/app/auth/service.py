from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.core.config import settings
from app.models.user import User
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


REFRESH_TOKEN_COOKIE = "refresh_token"


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400 if remember_me else None
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/")


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_reset_repo: PasswordResetRepository,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._password_reset_repo = password_reset_repo

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = await self._user_repo.get_by_email(body.email)
        if user is None or not _verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                },
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Account is inactive.",
                    "details": {},
                },
            )

        access_token = _create_access_token(user.id)
        raw_refresh = _create_refresh_token()
        remember_me: bool = body.remember_me if body.remember_me is not None else False
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self._refresh_token_repo.create(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh),
            expires_at=expires_at,
            remember_me=remember_me,
        )

        _set_refresh_cookie(response, raw_refresh, remember_me)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        existing = await self._user_repo.get_by_email(body.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": {},
                },
            )

        password_hash = _hash_password(body.password)
        user = await self._user_repo.create(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
        )

        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        user = await self._user_repo.get_by_email(body.email)
        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(64)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.PASSWORD_RESET_EXPIRE_HOURS
            )
            await self._password_reset_repo.create(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            # In a real system, an email with raw_token would be sent here.

        return ForgotPasswordResponse(
            message="If that email is registered, you will receive a password reset link shortly."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _hash_token(body.token)
        record = await self._password_reset_repo.get_valid_by_hash(token_hash)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_OR_EXPIRED_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                },
            )

        new_hash = _hash_password(body.password)
        await self._user_repo.update_password(record.user_id, new_hash)
        await self._password_reset_repo.mark_used(record.id)
        await self._refresh_token_repo.revoke_all_for_user(record.user_id)

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self, current_user: User) -> MeResponse:
        return MeResponse(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )

    async def logout(
        self,
        request: Request,
        response: Response,
        current_user: User,
    ) -> LogoutResponse:
        raw_refresh = request.cookies.get(REFRESH_TOKEN_COOKIE)
        if raw_refresh:
            token_hash = _hash_token(raw_refresh)
            await self._refresh_token_repo.revoke_by_hash(token_hash)
        _clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")

    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        raw_refresh = request.cookies.get(REFRESH_TOKEN_COOKIE)
        if not raw_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "MISSING_REFRESH_TOKEN",
                    "message": "Refresh token is missing.",
                    "details": {},
                },
            )

        token_hash = _hash_token(raw_refresh)
        record = await self._refresh_token_repo.get_valid_by_hash(token_hash)
        if record is None:
            _clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )

        user = await self._user_repo.get_by_id(record.user_id)
        if user is None or not user.is_active:
            _clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )

        # Rotate refresh token
        await self._refresh_token_repo.revoke_by_hash(token_hash)
        new_raw_refresh = _create_refresh_token()
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self._refresh_token_repo.create(
            user_id=user.id,
            token_hash=_hash_token(new_raw_refresh),
            expires_at=new_expires_at,
            remember_me=record.remember_me,
        )

        _set_refresh_cookie(response, new_raw_refresh, record.remember_me)
        access_token = _create_access_token(user.id)

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
        )
