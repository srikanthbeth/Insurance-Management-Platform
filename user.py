from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from models.user import UserRole


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )