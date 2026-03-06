import json
import secrets
import time
from typing import Optional

import bcrypt
from jwt import PyJWT
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dto import AuthTokenResponse, RefreshTokenResponse, UserInfo
from src.common.email import send_verification_code
from src.common.erri import bad_request, conflict, not_found, unauthorized
from src.conf.config import settings
from src.invitation.model import InvitationCode
from src.tenant.model import Tenant
from src.user.model import User, UserRole

_jwt = PyJWT()

# --- Password ---


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- Token ---


def create_access_token(user: User) -> str:
    now = int(time.time())
    payload = {
        "sub": user.username,
        "uid": user.id,
        "tid": user.tenant_id,
        "rol": user.role,
        "iat": now,
        "exp": now + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    return _jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


async def _store_refresh_token(redis: Redis, token: str, user_id: int, username: str) -> None:
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    pipe = redis.pipeline()
    pipe.hset(f"rt:{token}", mapping={"user_id": str(user_id), "username": username})
    pipe.expire(f"rt:{token}", ttl)
    pipe.sadd(f"rt_user:{user_id}", token)
    pipe.expire(f"rt_user:{user_id}", ttl)
    await pipe.execute()


async def _build_auth_response(redis: Redis, user: User) -> AuthTokenResponse:
    access_token = create_access_token(user)
    refresh_token = _generate_refresh_token()
    await _store_refresh_token(redis, refresh_token, user.id, user.username)
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(id=user.id, username=user.username, email=user.email, role=user.role, tenant_id=user.tenant_id),
    )


# --- Verification code ---


def _generate_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


async def _store_verification_code(
    redis: Redis, email: str, purpose: str, code: str, extra: Optional[dict] = None
) -> None:
    key = f"vc:{email}:{purpose}"
    data = {"code": code}
    if extra:
        data["extra"] = json.dumps(extra)
    await redis.hset(key, mapping=data)
    await redis.expire(key, 300)


async def _validate_verification_code(redis: Redis, email: str, purpose: str, code: str) -> Optional[dict]:
    key = f"vc:{email}:{purpose}"
    data = await redis.hgetall(key)
    if not data or data.get("code") != code:
        return None
    await redis.delete(key)
    return data


# --- Register ---


async def register(
    db: AsyncSession,
    redis: Redis,
    email: str,
    username: str,
    password: str,
    tenant_name: str,
    invitation_code: Optional[str],
) -> None:
    inv_id: Optional[int] = None

    # Check invitation code (only when required)
    if settings.REQUIRE_INVITATION_CODE:
        if not invitation_code:
            raise bad_request("Invitation code is required")
        stmt = select(InvitationCode).where(
            InvitationCode.code == invitation_code,
            InvitationCode.is_active.is_(True),
        )
        inv = (await db.execute(stmt)).scalar_one_or_none()
        if not inv:
            raise bad_request("Invalid invitation code")
        if inv.max_uses > 0 and inv.used_count >= inv.max_uses:
            raise bad_request("Invitation code has reached max uses")
        if inv.expires_at and inv.expires_at.timestamp() < time.time():
            raise bad_request("Invitation code has expired")
        inv_id = inv.id

    # Check duplicates
    existing = (
        await db.execute(
            select(User).where(or_(User.email == email, User.username == username), User.is_deleted.is_(False))
        )
    ).scalar_one_or_none()
    if existing:
        field = "email" if existing.email == email else "username"
        raise conflict(f"{field} already exists")

    existing_tenant = (
        await db.execute(select(Tenant).where(Tenant.name == tenant_name, Tenant.is_deleted.is_(False)))
    ).scalar_one_or_none()
    if existing_tenant:
        raise conflict("Tenant name already exists")

    # Store registration info + send code
    code = _generate_code()
    await _store_verification_code(
        redis,
        email,
        "register",
        code,
        extra={
            "username": username,
            "hashed_password": hash_password(password),
            "tenant_name": tenant_name,
            "invitation_code_id": inv_id,
        },
    )
    if not send_verification_code(email, code, "register"):
        logger.warning(f"Failed to send registration email to {email}")


async def verify_register(db: AsyncSession, redis: Redis, email: str, code: str) -> AuthTokenResponse:
    data = await _validate_verification_code(redis, email, "register", code)
    if not data:
        raise bad_request("Invalid or expired verification code")

    extra = json.loads(data["extra"])

    # Create tenant
    tenant = Tenant(name=extra["tenant_name"])
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=email,
        username=extra["username"],
        hashed_password=extra["hashed_password"],
        role=UserRole.OWNER,
        invitation_code_id=extra.get("invitation_code_id"),
    )
    db.add(user)

    # Update invitation code usage
    if extra.get("invitation_code_id"):
        stmt = select(InvitationCode).where(InvitationCode.id == extra["invitation_code_id"])
        inv = (await db.execute(stmt)).scalar_one()
        inv.used_count += 1

    await db.commit()
    await db.refresh(user)

    return await _build_auth_response(redis, user)


# --- Login ---


_DUMMY_HASH = hash_password("dummy-password-for-timing")


async def login(db: AsyncSession, redis: Redis, identifier: str, password: str) -> AuthTokenResponse:
    stmt = select(User).where(
        or_(User.email == identifier, User.username == identifier),
        User.is_deleted.is_(False),
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        verify_password(password, _DUMMY_HASH)
        raise unauthorized("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise unauthorized("Invalid credentials")

    return await _build_auth_response(redis, user)


# --- Token refresh ---


async def refresh_token(db: AsyncSession, redis: Redis, token: str) -> RefreshTokenResponse:
    key = f"rt:{token}"
    data = await redis.hgetall(key)
    if not data:
        raise unauthorized("Invalid refresh token")

    user_id = int(data["user_id"])

    # Fetch user from DB for correct tid/rol in new access token
    stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise unauthorized("User not found")

    # Rotation: delete old, create new
    pipe = redis.pipeline()
    pipe.delete(key)
    pipe.srem(f"rt_user:{user_id}", token)
    await pipe.execute()

    new_token = _generate_refresh_token()
    await _store_refresh_token(redis, new_token, user.id, user.username)
    access_token = create_access_token(user)

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# --- Logout ---


async def logout(redis: Redis, token: str) -> None:
    data = await redis.hgetall(f"rt:{token}")
    if data:
        user_id = data["user_id"]
        pipe = redis.pipeline()
        pipe.delete(f"rt:{token}")
        pipe.srem(f"rt_user:{user_id}", token)
        await pipe.execute()


# --- Password forgot/reset ---


async def forgot_password(db: AsyncSession, redis: Redis, email: str) -> None:
    stmt = select(User).where(User.email == email, User.is_deleted.is_(False))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        return  # Silent - don't reveal if email exists

    code = _generate_code()
    await _store_verification_code(redis, email, "reset_password", code)
    if not send_verification_code(email, code, "reset_password"):
        logger.warning(f"Failed to send password reset email to {email}")


async def reset_password(db: AsyncSession, redis: Redis, email: str, code: str, new_password: str) -> None:
    data = await _validate_verification_code(redis, email, "reset_password", code)
    if not data:
        raise bad_request("Invalid or expired verification code")

    stmt = select(User).where(User.email == email, User.is_deleted.is_(False))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise not_found("User not found")

    user.hashed_password = hash_password(new_password)
    await db.commit()

    # Revoke all refresh tokens
    tokens = await redis.smembers(f"rt_user:{user.id}")
    if tokens:
        pipe = redis.pipeline()
        for t in tokens:
            pipe.delete(f"rt:{t}")
        pipe.delete(f"rt_user:{user.id}")
        await pipe.execute()
