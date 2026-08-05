import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Response
from jose import JWTError, jwt
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
from app.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset import PasswordReset
from app.auth.repository import AuthRepository


COOKIE_NAME = "refresh_token"


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400 if remember_me else None
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax", path="/")


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self._repo = repo

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        from fastapi import HTTPException, status

        existing = await self._repo.get_user_by_email(body.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {},
                    }
                },
            )

        password_hash = _hash_password(body.password)
        user = await self._repo.create_user(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
        )
        return RegisterResponse(
            id=str(user.id),
            fullName=user.full_name,
            email=user.email,
            createdAt=user.created_at.isoformat(),
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        from fastapi import HTTPException, status

        _INVALID = "Invalid email or password."

        user = await self._repo.get_user_by_email(body.email)
        if user is None or not _verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": _INVALID,
                        "details": {},
                    }
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": _INVALID,
                        "details": {},
                    }
                },
            )

        access_token = _create_access_token(user.id)
        raw_refresh = _create_refresh_token()
        remember_me: bool = body.rememberMe if body.rememberMe is not None else False
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self._repo.create_refresh_token(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh),
            expires_at=expires_at,
            remember_me=remember_me,
        )

        _set_refresh_cookie(response, raw_refresh, remember_me)

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
            user=MeResponse(
                id=str(user.id),
                fullName=user.full_name,
                email=user.email,
                createdAt=user.created_at.isoformat(),
            ),
        )

    async def forgot_password(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        _GENERIC = "If that email is registered you will receive a reset link shortly."

        user = await self._repo.get_user_by_email(body.email)
        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(32)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
            )
            await self._repo.create_password_reset(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            # Email sending is handled by the infrastructure layer (out of scope here)

        return ForgotPasswordResponse(message=_GENERIC)

    async def reset_password(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        from fastapi import HTTPException, status

        token_hash = _hash_token(body.token)
        reset_record = await self._repo.get_valid_password_reset(token_hash)
        if reset_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_OR_EXPIRED_TOKEN",
                        "message": "This reset link is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        new_hash = _hash_password(body.password)
        await self._repo.update_user_password(reset_record.user_id, new_hash)
        await self._repo.mark_password_reset_used(reset_record.id)
        await self._repo.revoke_all_refresh_tokens(reset_record.user_id)

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self, current_user: User) -> MeResponse:
        return MeResponse(
            id=str(current_user.id),
            fullName=current_user.full_name,
            email=current_user.email,
            createdAt=current_user.created_at.isoformat(),
        )

    async def logout(
        self,
        current_user: User,
        refresh_token: Optional[str],
        response: Response,
    ) -> LogoutResponse:
        if refresh_token is not None:
            token_hash = _hash_token(refresh_token)
            await self._repo.revoke_refresh_token_by_hash(token_hash)

        _clear_refresh_cookie(response)

        return LogoutResponse(message="Logged out successfully.")

    async def refresh(
        self,
        refresh_token: Optional[str],
        response: Response,
    ) -> RefreshResponse:
        from fastapi import HTTPException, status

        _INVALID = "Invalid or expired refresh token."

        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "MISSING_REFRESH_TOKEN",
                        "message": _INVALID,
                        "details": {},
                    }
                },
            )

        token_hash = _hash_token(refresh_token)
        stored = await self._repo.get_valid_refresh_token(token_hash)

        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": _INVALID,
                        "details": {},
                    }
                },
            )

        # Rotate: revoke old, issue new
        await self._repo.revoke_refresh_token_by_hash(token_hash)

        user = await self._repo.get_user_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": _INVALID,
                        "details": {},
                    }
                },
            )

        access_token = _create_access_token(user.id)
        raw_refresh = _create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self._repo.create_refresh_token(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh),
            expires_at=expires_at,
            remember_me=stored.remember_me,
        )

        _set_refresh_cookie(response, raw_refresh, stored.remember_me)

        return RefreshResponse(
            accessToken=access_token,
            tokenType="bearer",
        )
