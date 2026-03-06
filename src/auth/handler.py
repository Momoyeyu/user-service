from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service
from src.auth.dto import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyRegisterRequest,
)
from src.common.resp import ok
from src.conf.db import get_db
from src.conf.redis import get_redis
from src.middleware.auth import exempt

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", summary="发起注册", operation_id="register")
@exempt
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    await service.register(db, redis, req.email, req.username, req.password, req.tenant_name, req.invitation_code)
    return ok(message="验证码已发送")


@router.post("/register/verify", summary="验证码确认注册", operation_id="verifyRegister")
@exempt
async def verify_register(
    req: VerifyRegisterRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    result = await service.verify_register(db, redis, req.email, req.code)
    return ok(data=result.model_dump())


@router.post("/login", summary="用户登录", operation_id="login")
@exempt
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    result = await service.login(db, redis, req.identifier, req.password)
    return ok(data=result.model_dump())


@router.post("/token/refresh", summary="刷新 token", operation_id="refreshToken")
@exempt
async def refresh_token(
    req: RefreshTokenRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    result = await service.refresh_token(db, redis, req.refresh_token)
    return ok(data=result.model_dump())


@router.post("/logout", summary="用户登出", operation_id="logout")
@exempt
async def logout(req: LogoutRequest, redis: Redis = Depends(get_redis)):
    await service.logout(redis, req.refresh_token)
    return ok(message="已登出")


@router.post("/password/forgot", summary="忘记密码", operation_id="forgotPassword")
@exempt
async def forgot_password(
    req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    await service.forgot_password(db, redis, req.email)
    return ok(message="重置邮件已发送")


@router.post("/password/reset", summary="重置密码", operation_id="resetPassword")
@exempt
async def reset_password(
    req: ResetPasswordRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    await service.reset_password(db, redis, req.email, req.code, req.new_password)
    return ok(message="密码已重置")
