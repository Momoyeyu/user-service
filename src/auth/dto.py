import re
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, StringConstraints, field_validator

Username = Annotated[str, StringConstraints(min_length=2, max_length=100)]
TenantName = Annotated[str, StringConstraints(min_length=1, max_length=100)]

_PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


def _check_password(v: str) -> str:
    if not _PASSWORD_RE.match(v):
        raise ValueError("Password must be at least 8 characters with uppercase, lowercase and numbers")
    return v


class RegisterRequest(BaseModel):
    email: EmailStr
    username: Username
    password: str
    tenant_name: TenantName
    invitation_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _check_password(v)


class VerifyRegisterRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _check_password(v)


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str
    tenant_id: int


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserInfo


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
