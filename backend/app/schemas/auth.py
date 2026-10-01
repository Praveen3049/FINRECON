from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: str = Field(..., description="User corporate email address")
    password: str = Field(..., min_length=1, description="Account password")
    role: Optional[str] = Field(None, description="Enforced user role (USER, AUDITOR, MANAGER)")


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: str = Field(..., description="User corporate or personal email address")
    password: str = Field(..., min_length=6, description="Account password (min 6 characters)")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    status: str = "success"
    message: str = "Session successfully terminated"
