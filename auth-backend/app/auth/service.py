import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials

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
from app.db import get_connection

SECRET_KEY: str = os.environ.get("JWT_SECRET", "change-me")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30")
)
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
COOKIE_NAME: str = "refresh_token"

_MSG_INVALID_RESET_TOKEN: str = (
    "This password reset link is invalid or has expired."
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _generate_refresh_token() -> str:
    return hashlib.sha256(os.urandom(64)).hexdigest()


def _set_refresh_cookie(
    response: Response, token: str, remember_me: bool
) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400
        if remember_me
        else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


class AuthService:
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        async with get_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", body.email
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": {
                            "code": "EMAIL_TAKEN",
                            "message": "An account with this email already exists.",
                            "details": {},
                        }
                    },
                )

            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            row = await conn.fetchrow(
                """
                INSERT INTO users (full_name, email, password_hash, is_active)
                VALUES ($1, $2, $3, TRUE)
                RETURNING id, full_name, email, created_at
                """,
                body.full_name,
                body.email,
                password_hash,
            )

        return RegisterResponse(
            id=row["id"],
            fullName=row["full_name"],
            email=row["email"],
            createdAt=row["created_at"].isoformat(),
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, full_name, email, password_hash, is_active"
                " FROM users WHERE email = $1",
                body.email,
            )

            invalid_exc = HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": {},
                    }
                },
            )

            if not row:
                raise invalid_exc

            if not bcrypt.checkpw(
                body.password.encode(), row["password_hash"].encode()
            ):
                raise invalid_exc

            if not row["is_active"]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": {
                            "code": "ACCOUNT_INACTIVE",
                            "message": "Your account is inactive.",
                            "details": {},
                        }
                    },
                )

            access_token = _generate_access_token(row["id"], row["email"])
            raw_refresh = _generate_refresh_token()
            token_hash = _hash_token(raw_refresh)
            remember_me: bool = (
                body.remember_me if body.remember_me is not None else False
            )
            expire_days = (
                REFRESH_TOKEN_REMEMBER_DAYS
                if remember_me
                else REFRESH_TOKEN_EXPIRE_DAYS
            )
            expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

            await conn.execute(
                """
                INSERT INTO refresh_tokens
                (user_id, token_hash, expires_at, remember_me)
                VALUES ($1, $2, $3, $4)
                """,
                row["id"],
                token_hash,
                expires_at,
                remember_me,
            )

        _set_refresh_cookie(response, raw_refresh, remember_me)

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
            user={
                "id": row["id"],
                "fullName": row["full_name"],
                "email": row["email"],
            },
        )

    async def forgot_password(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        generic = ForgotPasswordResponse(
            message=(
                "If an account with that email exists, a password reset link"
                " has been sent."
            )
        )

        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1 AND is_active = TRUE",
                body.email,
            )
            if not row:
                return generic

            raw_token = _generate_refresh_token()
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            await conn.execute(
                """
                INSERT INTO password_resets (user_id, token_hash, expires_at)
                VALUES ($1, $2, $3)
                """,
                row["id"],
                token_hash,
                expires_at,
            )

        # In production, send email here with raw_token.
        return generic

    # Keep old name as alias for compatibility with router calling forgotPassword
    async def forgotPassword(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        return await self.forgot_password(body)

    async def reset_password(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        token_hash = _hash_token(body.token)

        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, expires_at, used_at
                FROM password_resets
                WHERE token_hash = $1
                """,
                token_hash,
            )

            if not row:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "INVALID_RESET_TOKEN",
                            "message": _MSG_INVALID_RESET_TOKEN,
                            "details": {},
                        }
                    },
                )

            if row["used_at"] is not None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "RESET_TOKEN_USED",
                            "message": _MSG_INVALID_RESET_TOKEN,
                            "details": {},
                        }
                    },
                )

            if row["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(
                timezone.utc
            ):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "RESET_TOKEN_EXPIRED",
                            "message": _MSG_INVALID_RESET_TOKEN,
                            "details": {},
                        }
                    },
                )

            new_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = NOW()"
                " WHERE id = $2",
                new_hash,
                row["user_id"],
            )

            await conn.execute(
                "UPDATE password_resets SET used_at = NOW() WHERE id = $1",
                row["id"],
            )

            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW()"
                " WHERE user_id = $1 AND revoked_at IS NULL",
                row["user_id"],
            )

        return ResetPasswordResponse(
            message="Your password has been reset successfully."
        )

    # Keep old name as alias for compatibility with router calling resetPassword
    async def resetPassword(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        return await self.reset_password(body)

    async def me(
        self, credentials: HTTPAuthorizationCredentials | None
    ) -> MeResponse:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "MISSING_TOKEN",
                        "message": "Authentication required.",
                        "details": {},
                    }
                },
            )

        try:
            payload = jwt.decode(
                credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Your session has expired. Please log in again.",
                        "details": {},
                    }
                },
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Authentication required.",
                        "details": {},
                    }
                },
            )

        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Authentication required.",
                        "details": {},
                    }
                },
            )
        user_id = int(user_id_raw)

        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, full_name, email, is_active, created_at"
                " FROM users WHERE id = $1",
                user_id,
            )

        if not row or not row["is_active"]:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "Authentication required.",
                        "details": {},
                    }
                },
            )

        return MeResponse(
            id=row["id"],
            fullName=row["full_name"],
            email=row["email"],
            createdAt=row["created_at"].isoformat(),
        )

    async def logout(
        self,
        request: Request,
        response: Response,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> LogoutResponse:
        raw_refresh: str | None = request.cookies.get(COOKIE_NAME)

        if raw_refresh:
            token_hash = _hash_token(raw_refresh)
            async with get_connection() as conn:
                await conn.execute(
                    """
                    UPDATE refresh_tokens
                    SET revoked_at = NOW()
                    WHERE token_hash = $1 AND revoked_at IS NULL
                    """,
                    token_hash,
                )

        _clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")

    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        raw_refresh: str | None = request.cookies.get(COOKIE_NAME)

        if not raw_refresh:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "MISSING_REFRESH_TOKEN",
                        "message": "Your session has expired. Please log in again.",
                        "details": {},
                    }
                },
            )

        token_hash = _hash_token(raw_refresh)

        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked_at,
                       rt.remember_me,
                       u.email, u.full_name, u.is_active
                FROM refresh_tokens rt
                JOIN users u ON u.id = rt.user_id
                WHERE rt.token_hash = $1
                """,
                token_hash,
            )

            if not row:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": {
                            "code": "INVALID_REFRESH_TOKEN",
                            "message": "Your session has expired. Please log in again.",
                            "details": {},
                        }
                    },
                )

            if row["revoked_at"] is not None:
                # Possible token reuse — revoke all tokens for this user.
                await conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = NOW()"
                    " WHERE user_id = $1 AND revoked_at IS NULL",
                    row["user_id"],
                )
                _clear_refresh_cookie(response)
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": {
                            "code": "REFRESH_TOKEN_REUSE",
                            "message": "Your session has expired. Please log in again.",
                            "details": {},
                        }
                    },
                )

            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": {
                            "code": "REFRESH_TOKEN_EXPIRED",
                            "message": "Your session has expired. Please log in again.",
                            "details": {},
                        }
                    },
                )

            if not row["is_active"]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": {
                            "code": "ACCOUNT_INACTIVE",
                            "message": "Your account is inactive.",
                            "details": {},
                        }
                    },
                )

            # Revoke old refresh token.
            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = $1",
                row["id"],
            )

            # Issue new refresh token (rotation).
            new_raw_refresh = _generate_refresh_token()
            new_token_hash = _hash_token(new_raw_refresh)
            remember_me: bool = row["remember_me"]
            expire_days = (
                REFRESH_TOKEN_REMEMBER_DAYS
                if remember_me
                else REFRESH_TOKEN_EXPIRE_DAYS
            )
            new_expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

            await conn.execute(
                """
                INSERT INTO refresh_tokens
                (user_id, token_hash, expires_at, remember_me)
                VALUES ($1, $2, $3, $4)
                """,
                row["user_id"],
                new_token_hash,
                new_expires_at,
                remember_me,
            )

        access_token = _generate_access_token(row["user_id"], row["email"])
        _set_refresh_cookie(response, new_raw_refresh, remember_me)

        return RefreshResponse(
            accessToken=access_token,
            tokenType="bearer",
            user={
                "id": row["user_id"],
                "fullName": row["full_name"],
                "email": row["email"],
            },
        )
