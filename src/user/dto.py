from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from src.auth.dto import Username, _check_password


class UserProfile(BaseModel):
    id: int
    email: str
    username: str
    role: str
    tenant_id: int
    created_at: datetime

    @classmethod
    def from_model(cls, user) -> "UserProfile":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            tenant_id=user.tenant_id,
            created_at=user.created_at,
        )


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[Username] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _check_password(v)
