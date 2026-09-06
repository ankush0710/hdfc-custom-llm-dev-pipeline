from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignup(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    # Role is strictly server-assigned to VIEWER. Any client-sent role is ignored.
    role: Optional[str] = None



class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    session_expires_at: Optional[datetime] = None
    session_duration_minutes: Optional[int] = None


class RoleUpdate(BaseModel):
    role: str


class UserStatusUpdate(BaseModel):
    is_active: bool

