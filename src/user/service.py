from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service as auth_service
from src.common.erri import bad_request, conflict, not_found
from src.user.model import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise not_found("User not found")
    return user


async def update_user(
    db: AsyncSession, user_id: int, email: Optional[str] = None, username: Optional[str] = None
) -> User:
    user = await get_user_by_id(db, user_id)
    if email is not None and email != user.email:
        existing = (
            await db.execute(select(User).where(User.email == email, User.is_deleted.is_(False)))
        ).scalar_one_or_none()
        if existing:
            raise conflict("Email already exists")
        user.email = email
    if username is not None and username != user.username:
        existing = (
            await db.execute(select(User).where(User.username == username, User.is_deleted.is_(False)))
        ).scalar_one_or_none()
        if existing:
            raise conflict("Username already exists")
        user.username = username
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(db: AsyncSession, user_id: int, old_password: str, new_password: str) -> None:
    user = await get_user_by_id(db, user_id)
    if not auth_service.verify_password(old_password, user.hashed_password):
        raise bad_request("Current password is incorrect")
    user.hashed_password = auth_service.hash_password(new_password)
    await db.commit()
