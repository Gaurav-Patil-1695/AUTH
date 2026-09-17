from typing import Any

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, alias="fullName")
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., alias="confirmPassword")
    accept_terms: bool = Field(..., alias="acceptTerms")

    model_config = {"populate_by_name": True}


class RegisterResponse(BaseModel):
    id: int
    full_name: str = Field(..., alias="fullName")
    email: str
    created_at: str = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool | None = Field(False, alias="rememberMe")

    model_config = {"populate_by_name": True}


class LoginResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")
    user: dict[str, Any]

    model_config = {"populate_by_name": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., alias="confirmPassword")

    model_config = {"populate_by_name": True}


class ResetPasswordResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    id: int
    full_name: str = Field(..., alias="fullName")
    email: str
    created_at: str = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class LogoutRequest(BaseModel):
    pass


class LogoutResponse(BaseModel):
    message: str


class RefreshResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")
    user: dict[str, Any]

    model_config = {"populate_by_name": True}
