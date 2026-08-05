from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    fullName: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirmPassword: str
    acceptTerms: bool


class RegisterResponse(BaseModel):
    id: int
    fullName: str
    email: str
    createdAt: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = False


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str
    user: Dict[str, Any]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)
    confirmPassword: str


class ResetPasswordResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    id: int
    fullName: str
    email: str
    createdAt: str


class LogoutRequest(BaseModel):
    pass


class LogoutResponse(BaseModel):
    message: str


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str
    user: Dict[str, Any]
