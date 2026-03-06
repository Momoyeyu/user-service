from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.resp import ok
from src.conf.db import get_db
from src.middleware.auth import JWTClaims, get_claims
from src.tenant import service
from src.tenant.dto import TenantInfo, UpdateTenantRequest

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.get("/current", summary="获取当前租户信息", operation_id="getCurrentTenant")
async def get_current_tenant(claims: JWTClaims = Depends(get_claims), db: AsyncSession = Depends(get_db)):
    tenant = await service.get_tenant_by_id(db, claims.tenant_id)
    return ok(data=TenantInfo.from_model(tenant).model_dump(mode="json"))


@router.put("/current", summary="更新租户信息", operation_id="updateCurrentTenant")
async def update_current_tenant(
    req: UpdateTenantRequest, claims: JWTClaims = Depends(get_claims), db: AsyncSession = Depends(get_db)
):
    tenant = await service.update_tenant(db, claims.tenant_id, claims.user_role, name=req.name)
    return ok(data=TenantInfo.from_model(tenant).model_dump(mode="json"))
