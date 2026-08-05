from fastapi import Response

from app.auth.schemas import LoginRequest, LoginResponse
from app.core.config import settings
from app.core.database import get_db_connection
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
)
import asyncpg


async def login(body: LoginRequest, response: Response) -> LoginResponse:
    async with get_db_connection() as conn:
        user = await _get_user_by_email(conn, body.email)

        if user is None or not verify_password(body.password, user["password_hash"]):
            raise UnauthorizedException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        if not user["is_active"]:
            raise UnauthorizedException(
                code="ACCOUNT_INACTIVE",
                message="Invalid email or password.",
            )

        access_token = create_access_token(
            subject=str(user["id"]),
            email=user["email"],
            full_name=user["full_name"],
        )

        raw_refresh_token, refresh_token_hash = create_refresh_token()
        remember_me = body.remember_me if body.remember_me is not None else False

        await _store_refresh_token(
            conn,
            user_id=user["id"],
            token_hash=refresh_token_hash,
            remember_me=remember_me,
        )

    max_age = settings.REFRESH_TOKEN_REMEMBER_ME_EXPIRE_SECONDS if remember_me else settings.REFRESH_TOKEN_EXPIRE_SECONDS

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=max_age,
        path="/",
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(user["id"]),
            "full_name": user["full_name"],
            "email": user["email"],
        },
    )


async def _get_user_by_email(conn: asyncpg.Connection, email: str):
    row = await conn.fetchrow(
        """
        SELECT id, full_name, email, password_hash, is_active
        FROM users
        WHERE email = $1
        """,
        email.lower(),
    )
    return row


async def _store_refresh_token(
    conn: asyncpg.Connection,
    user_id: int,
    token_hash: str,
    remember_me: bool,
) -> None:
    import datetime

    if remember_me:
        expires_delta = datetime.timedelta(seconds=settings.REFRESH_TOKEN_REMEMBER_ME_EXPIRE_SECONDS)
    else:
        expires_delta = datetime.timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS)

    expires_at = datetime.datetime.utcnow() + expires_delta

    await conn.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at, remember_me)
        VALUES ($1, $2, $3, $4)
        """,
        user_id,
        token_hash,
        expires_at,
        remember_me,
    )
