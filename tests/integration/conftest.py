import pytest_asyncio

from src.auth.service import create_access_token
from tests.conftest import seed_tenant_and_user


@pytest_asyncio.fixture
async def seeded_data(session):
    """Seed tenant + user and return them."""
    return await seed_tenant_and_user(session)


@pytest_asyncio.fixture
async def auth_headers(seeded_data) -> dict[str, str]:
    """Create JWT auth headers for the test user."""
    _, user = seeded_data
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}
