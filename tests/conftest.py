import hashlib
import os
from collections.abc import AsyncGenerator

# Override settings before any src imports to avoid .env pollution in tests
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-at-least-32-bytes-long-for-hs256")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.conf.db import Base, get_db
from src.conf.redis import get_redis
from src.main import app

# --- Fast password hashing for tests (replaces bcrypt ~200ms → <1ms) ---

_FAST_PREFIX = "$fast$"


def _fast_hash(password: str) -> str:
    return _FAST_PREFIX + hashlib.sha256(password.encode()).hexdigest()


def _fast_verify(plain: str, hashed: str) -> bool:
    if hashed.startswith(_FAST_PREFIX):
        return _fast_hash(plain) == hashed
    return False


# Patch auth service before any test imports
from src.auth import service as auth_service  # noqa: E402

auth_service.hash_password = _fast_hash
auth_service.verify_password = _fast_verify

# --- Test password ---
TEST_PASSWORD = "TestPass123"
TEST_PASSWORD_HASH = _fast_hash(TEST_PASSWORD)

# --- Database fixtures ---


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(test_session_factory) -> AsyncGenerator[AsyncSession]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def redis():
    import fakeredis.aioredis

    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest_asyncio.fixture
async def client(session, redis) -> AsyncGenerator[AsyncClient]:
    async def override_get_db():
        yield session

    async def override_get_redis():
        return redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def db_cleanup(test_engine, test_session_factory, redis):
    """Clean up DB and Redis between tests, re-seed default data."""
    await redis.flushall()
    yield
    # Truncate all tables after each test
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    await redis.flushall()


# --- Seed helpers ---


async def seed_tenant_and_user(session: AsyncSession):
    """Create a default tenant + test user. Returns (tenant, user)."""
    from src.invitation.model import InvitationCode
    from src.tenant.model import Tenant
    from src.user.model import User

    tenant = Tenant(name="test_tenant")
    session.add(tenant)
    await session.flush()

    inv = InvitationCode(code="TESTCODE", max_uses=0, used_count=0, is_active=True)
    session.add(inv)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email="test@example.com",
        username="testuser",
        hashed_password=TEST_PASSWORD_HASH,
        role="owner",
        invitation_code_id=inv.id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(tenant)
    await session.refresh(user)
    return tenant, user
