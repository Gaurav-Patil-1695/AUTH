from __future__ import annotations

from functools import lru_cache

from pydantic import AnyUrl, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = Field(..., description="PostgreSQL DSN used by SQLAlchemy")

    # ------------------------------------------------------------------ #
    # JWT
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str = Field(..., description="Secret key for signing JWTs")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = Field(
        ..., description="Access token lifetime in minutes"
    )

    # ------------------------------------------------------------------ #
    # Bcrypt
    # ------------------------------------------------------------------ #
    BCRYPT_ROUNDS: int = Field(
        ..., ge=12, description="bcrypt cost factor; must be >= 12"
    )

    # ------------------------------------------------------------------ #
    # Password-reset token
    # ------------------------------------------------------------------ #
    RESET_TOKEN_TTL_MINUTES: int = Field(
        ..., gt=0, description="Password-reset token lifetime in minutes"
    )

    # ------------------------------------------------------------------ #
    # Refresh token
    # ------------------------------------------------------------------ #
    REFRESH_TOKEN_TTL_DAYS: int = Field(
        ..., gt=0, description="Default refresh token lifetime in days"
    )
    REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS: int = Field(
        ..., gt=0, description="Remember-me refresh token lifetime in days"
    )

    # ------------------------------------------------------------------ #
    # SMTP
    # ------------------------------------------------------------------ #
    SMTP_HOST: str = Field(..., description="SMTP server hostname")
    SMTP_PORT: int = Field(..., gt=0, lt=65536, description="SMTP server port")
    SMTP_USERNAME: str = Field(..., description="SMTP authentication username")
    SMTP_PASSWORD: str = Field(..., description="SMTP authentication password")
    SMTP_FROM_ADDRESS: EmailStr = Field(
        ..., description="Envelope From address for outgoing mail"
    )
    SMTP_USE_TLS: bool = Field(default=True, description="Use STARTTLS for SMTP")

    # ------------------------------------------------------------------ #
    # Rate limits
    # ------------------------------------------------------------------ #
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = Field(
        ..., gt=0, description="Max login attempts per window"
    )
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = Field(
        ..., gt=0, description="Login rate-limit window in seconds"
    )
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = Field(
        ..., gt=0, description="Max forgot-password requests per window"
    )
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = Field(
        ..., gt=0, description="Forgot-password rate-limit window in seconds"
    )

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def database_url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL must not be empty")
        return v

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def jwt_secret_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("JWT_SECRET_KEY must not be empty")
        return v

    @field_validator("SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_HOST", mode="before")
    @classmethod
    def smtp_fields_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("SMTP configuration fields must not be empty")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance; fails fast if any required var is absent."""
    return Settings()


settings: Settings = get_settings()
