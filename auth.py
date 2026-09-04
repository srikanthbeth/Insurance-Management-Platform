from pydantic import BaseModel, EmailStr, Field

from models.user import UserRole
from schemas.user import UserResponse


class RegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=72,
    )

    role: UserRole = UserRole.CUSTOMER


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=72,
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=72,
    )

    new_password: str = Field(
        min_length=8,
        max_length=72,
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

    


class UserStatusUpdate(BaseModel):
    is_active: bool