from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: Optional[bool] = Field(None, description="Extend refresh token lifetime")


class UserInfo(BaseModel):
    id: str
    full_name: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserInfo


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
