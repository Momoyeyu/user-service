from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.resp import ok
from src.conf.db import get_db
from src.middleware.auth import JWTClaims, get_claims
from src.user import service
from src.user.dto import ChangePasswordRequest, UpdateUserRequest, UserProfile

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", summary="获取当前用户信息", operation_id="getCurrentUser")
async def get_me(claims: JWTClaims = Depends(get_claims), db: AsyncSession = Depends(get_db)):
    user = await service.get_user_by_id(db, claims.user_id)
    return ok(data=UserProfile.from_model(user).model_dump(mode="json"))


@router.put("/me", summary="更新当前用户信息", operation_id="updateCurrentUser")
async def update_me(
    req: UpdateUserRequest, claims: JWTClaims = Depends(get_claims), db: AsyncSession = Depends(get_db)
):
    user = await service.update_user(db, claims.user_id, email=req.email, username=req.username)
    return ok(data=UserProfile.from_model(user).model_dump(mode="json"))


@router.put("/me/password", summary="修改密码", operation_id="changePassword")
async def change_password(
    req: ChangePasswordRequest, claims: JWTClaims = Depends(get_claims), db: AsyncSession = Depends(get_db)
):
    await service.change_password(db, claims.user_id, req.old_password, req.new_password)
    return ok(message="密码已修改")
