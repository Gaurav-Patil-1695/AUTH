import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy import select
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
from app.models import PasswordReset, RefreshToken, User


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


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        result = await self.db.execute(select(User).where(User.email == payload.email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": {},
                },
            )

        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": {},
                },
            )

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=_hash_password(payload.password),
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def login(self, payload: LoginRequest, response: Response) -> LoginResponse:
        result = await self.db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()

        if user is None or not _verify_password(payload.password, user.password_hash):
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
                    "message": "Your account is inactive.",
                    "details": {},
                },
            )

        access_token = _create_access_token(user.id)
        raw_refresh = _create_refresh_token()
        remember_me = payload.remember_me if payload.remember_me is not None else False
        refresh_expires = timedelta(
            days=settings.REFRESH_TOKEN_REMEMBER_DAYS if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh),
            expires_at=datetime.now(timezone.utc) + refresh_expires,
            remember_me=remember_me,
        )
        self.db.add(refresh_token_record)
        await self.db.commit()

        max_age = int(refresh_expires.total_seconds())
        response.set_cookie(
            key="refresh_token",
            value=raw_refresh,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=max_age,
            path="/",
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def forgotPassword(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        result = await self.db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()

        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(32)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)

            reset_record = PasswordReset(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            self.db.add(reset_record)
            await self.db.commit()

            # In a production system the reset link would be emailed here.
            # Email delivery is outside the scope of this implementation.

        return ForgotPasswordResponse(
            message="If that email address is in our system, we have sent a password reset link."
        )

    async def resetPassword(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _hash_token(payload.token)

        result = await self.db.execute(
            select(PasswordReset).where(
                PasswordReset.token_hash == token_hash,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > datetime.now(timezone.utc),
            )
        )
        reset_record = result.scalar_one_or_none()

        if reset_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_OR_EXPIRED_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                },
            )

        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": {},
                },
            )

        user_result = await self.db.execute(select(User).where(User.id == reset_record.user_id))
        user = user_result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_OR_EXPIRED_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                },
            )

        user.password_hash = _hash_password(payload.password)
        reset_record.used_at = datetime.now(timezone.utc)

        # Revoke all existing refresh tokens for this user
        rt_result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        for rt in rt_result.scalars().all():
            rt.revoked_at = datetime.now(timezone.utc)

        await self.db.commit()

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def logout(self, current_user: User, response: Response) -> LogoutResponse:
        rt_result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == current_user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        for rt in rt_result.scalars().all():
            rt.revoked_at = datetime.now(timezone.utc)

        await self.db.commit()

        response.delete_cookie(key="refresh_token", path="/")

        return LogoutResponse(message="Successfully logged out.")

    async def refresh(self, response: Response) -> RefreshResponse:
        from fastapi import Request as FastAPIRequest

        # The raw cookie value must be extracted via the Request object;
        # this method is called from the router which passes Response only.
        # Per the router signature, refresh receives `response: Response`.
        # The cookie is read inside the dependency; here we raise an error
        # since the router is expected to pass the raw token via a different
        # mechanism. To keep the interface consistent with the router as
        # already defined (only `response` is passed), we raise 401 if no
        # cookie is accessible. In practice the router should extract the
        # cookie and call a variant; for now we document this limitation.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_REFRESH_TOKEN",
                "message": "No refresh token provided.",
                "details": {},
            },
        )

    async def refresh_with_token(self, raw_token: str, response: Response) -> RefreshResponse:
        token_hash = _hash_token(raw_token)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        rt = result.scalar_one_or_none()

        if rt is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )

        user_result = await self.db.execute(select(User).where(User.id == rt.user_id))
        user = user_result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )

        # Rotate: revoke old, issue new
        rt.revoked_at = datetime.now(timezone.utc)

        new_raw = _create_refresh_token()
        remember_me = rt.remember_me
        refresh_expires = timedelta(
            days=settings.REFRESH_TOKEN_REMEMBER_DAYS if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(new_raw),
            expires_at=datetime.now(timezone.utc) + refresh_expires,
            remember_me=remember_me,
        )
        self.db.add(new_rt)
        await self.db.commit()

        max_age = int(refresh_expires.total_seconds())
        response.set_cookie(
            key="refresh_token",
            value=new_raw,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=max_age,
            path="/",
        )

        access_token = _create_access_token(user.id)
        return RefreshResponse(access_token=access_token, token_type="bearer")
