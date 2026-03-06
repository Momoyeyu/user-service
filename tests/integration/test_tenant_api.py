import pytest
from httpx import AsyncClient

from src.auth.service import create_access_token
from tests.conftest import TEST_PASSWORD_HASH, seed_tenant_and_user


@pytest.mark.asyncio
class TestGetCurrentTenant:
    async def test_success(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/tenants/current", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "test_tenant"
        assert body["data"]["status"] == "active"

    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/tenants/current")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateCurrentTenant:
    async def test_owner_can_update(self, client: AsyncClient, auth_headers):
        response = await client.put(
            "/api/v1/tenants/current",
            headers=auth_headers,
            json={"name": "Updated Corp"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Corp"

    async def test_member_cannot_update(self, client: AsyncClient, session):
        from src.user.model import User

        tenant, _ = await seed_tenant_and_user(session)

        # Create a member user
        member = User(
            tenant_id=tenant.id,
            email="member@example.com",
            username="member",
            hashed_password=TEST_PASSWORD_HASH,
            role="member",
        )
        session.add(member)
        await session.commit()
        await session.refresh(member)

        token = create_access_token(member)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put(
            "/api/v1/tenants/current",
            headers=headers,
            json={"name": "Hacked"},
        )
        assert response.status_code == 403
