from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str


class RegisterResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str


class ResetPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


class MeResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict


class ErrorResponse(BaseModel):
    error: ErrorDetail
