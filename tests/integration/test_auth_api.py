import pytest
from httpx import AsyncClient

from tests.conftest import TEST_PASSWORD, seed_tenant_and_user


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, session):
        await seed_tenant_and_user(session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "testuser", "password": TEST_PASSWORD},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "access_token" in body["data"]
        assert "refresh_token" in body["data"]
        assert body["data"]["user"]["username"] == "testuser"

    async def test_login_wrong_password(self, client: AsyncClient, session):
        await seed_tenant_and_user(session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "testuser", "password": "wrong"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "nobody", "password": "pass"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestTokenRefresh:
    async def test_refresh_success(self, client: AsyncClient, session):
        await seed_tenant_and_user(session)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "testuser", "password": TEST_PASSWORD},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        refresh_resp = await client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        body = refresh_resp.json()
        assert body["data"]["refresh_token"] != refresh_token  # Rotated

    async def test_refresh_old_token_fails(self, client: AsyncClient, session):
        await seed_tenant_and_user(session)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "testuser", "password": TEST_PASSWORD},
        )
        old_token = login_resp.json()["data"]["refresh_token"]

        # First refresh: success
        await client.post("/api/v1/auth/token/refresh", json={"refresh_token": old_token})

        # Second refresh with old token: fail
        resp = await client.post("/api/v1/auth/token/refresh", json={"refresh_token": old_token})
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    async def test_logout(self, client: AsyncClient, session):
        await seed_tenant_and_user(session)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "testuser", "password": TEST_PASSWORD},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        logout_resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert logout_resp.status_code == 200

        # Refresh after logout should fail
        resp = await client.post("/api/v1/auth/token/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401
