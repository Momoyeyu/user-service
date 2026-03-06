from pydantic import BaseModel


class InternalUserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str
    tenant_id: int

    @classmethod
    def from_model(cls, user) -> "InternalUserInfo":
        return cls(id=user.id, username=user.username, email=user.email, role=user.role, tenant_id=user.tenant_id)


class BatchGetUsersRequest(BaseModel):
    user_ids: list[int]


class BatchGetUsersResponse(BaseModel):
    users: list[InternalUserInfo]
