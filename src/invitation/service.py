from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.erri import not_found
from src.user.model import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise not_found("User not found")
    return user


async def batch_get_users(db: AsyncSession, user_ids: list[int]) -> list[User]:
    stmt = select(User).where(User.id.in_(user_ids), User.is_deleted.is_(False))
    result = await db.execute(stmt)
    return list(result.scalars().all())
