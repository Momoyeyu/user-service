from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.auth.dto import TenantName


class TenantInfo(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime

    @classmethod
    def from_model(cls, tenant) -> "TenantInfo":
        return cls(id=tenant.id, name=tenant.name, status=tenant.status, created_at=tenant.created_at)


class UpdateTenantRequest(BaseModel):
    name: Optional[TenantName] = None
