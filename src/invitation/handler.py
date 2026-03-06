from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.erri import bad_request, unauthorized
from src.common.resp import ok
from src.conf.config import settings
from src.conf.db import get_db
from src.invitation import service
from src.invitation.dto import BatchGetUsersRequest, InternalUserInfo
from src.middleware.auth import exempt

router = APIRouter(prefix="/api/v1/internal", tags=["internal"])


def verify_api_key(x_api_key: str = Header()) -> None:
    if x_api_key != settings.INTERNAL_API_KEY:
        raise unauthorized("Invalid API key")


@router.get("/users/{user_id}", summary="内部查询单个用户", operation_id="getInternalUser")
@exempt
async def get_internal_user(user_id: int, _: None = Depends(verify_api_key), db: AsyncSession = Depends(get_db)):
    user = await service.get_user_by_id(db, user_id)
    return ok(data=InternalUserInfo.from_model(user).model_dump())


@router.post("/users/batch", summary="内部批量查询用户", operation_id="batchGetInternalUsers")
@exempt
async def batch_get_users(
    req: BatchGetUsersRequest, _: None = Depends(verify_api_key), db: AsyncSession = Depends(get_db)
):
    if len(req.user_ids) > 100:
        raise bad_request("Max 100 user IDs per request")
    users = await service.batch_get_users(db, req.user_ids)
    return ok(data={"users": [InternalUserInfo.from_model(u).model_dump() for u in users]})
