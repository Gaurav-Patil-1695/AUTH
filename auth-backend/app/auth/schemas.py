from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    terms: bool


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
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
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


class MeResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool


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
    refresh_token: str
    token_type: str


# ---------------------------------------------------------------------------
# Error envelope (shared)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
