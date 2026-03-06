import pytest
from httpx import AsyncClient

from tests.conftest import TEST_PASSWORD


@pytest.mark.asyncio
class TestGetMe:
    async def test_success(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["username"] == "testuser"
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["role"] == "owner"

    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateMe:
    async def test_update_username(self, client: AsyncClient, auth_headers):
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"username": "newname"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["username"] == "newname"

    async def test_update_email(self, client: AsyncClient, auth_headers):
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"email": "new@example.com"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "new@example.com"


@pytest.mark.asyncio
class TestChangePassword:
    async def test_success(self, client: AsyncClient, auth_headers):
        response = await client.put(
            "/api/v1/users/me/password",
            headers=auth_headers,
            json={"old_password": TEST_PASSWORD, "new_password": "NewPass456"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "密码已修改"

    async def test_wrong_old_password(self, client: AsyncClient, auth_headers):
        response = await client.put(
            "/api/v1/users/me/password",
            headers=auth_headers,
            json={"old_password": "wrong", "new_password": "NewPass456"},
        )
        assert response.status_code == 400
