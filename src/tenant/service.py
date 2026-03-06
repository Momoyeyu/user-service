from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.erri import forbidden, not_found
from src.tenant.model import Tenant
from src.user.model import UserRole


async def get_tenant_by_id(db: AsyncSession, tenant_id: int) -> Tenant:
    stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.is_deleted.is_(False))
    tenant = (await db.execute(stmt)).scalar_one_or_none()
    if not tenant:
        raise not_found("Tenant not found")
    return tenant


async def update_tenant(db: AsyncSession, tenant_id: int, role: str, name: Optional[str] = None) -> Tenant:
    if role != UserRole.OWNER:
        raise forbidden("Only owner can update tenant")
    tenant = await get_tenant_by_id(db, tenant_id)
    if name is not None:
        tenant.name = name
    await db.commit()
    await db.refresh(tenant)
    return tenant
