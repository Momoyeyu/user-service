import pytest

from src.common.erri import BusinessError
from src.user import service
from tests.conftest import TEST_PASSWORD, seed_tenant_and_user


@pytest.mark.asyncio
class TestGetUserById:
    async def test_found(self, session):
        tenant, user = await seed_tenant_and_user(session)
        result = await service.get_user_by_id(session, user.id)
        assert result.username == "testuser"

    async def test_not_found(self, session):
        with pytest.raises(BusinessError) as exc:
            await service.get_user_by_id(session, 99999)
        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestUpdateUser:
    async def test_update_email(self, session):
        tenant, user = await seed_tenant_and_user(session)
        updated = await service.update_user(session, user.id, email="new@example.com")
        assert updated.email == "new@example.com"

    async def test_update_username(self, session):
        tenant, user = await seed_tenant_and_user(session)
        updated = await service.update_user(session, user.id, username="newname")
        assert updated.username == "newname"


@pytest.mark.asyncio
class TestChangePassword:
    async def test_success(self, session):
        tenant, user = await seed_tenant_and_user(session)
        await service.change_password(session, user.id, TEST_PASSWORD, "NewPass456")
        # Verify new password works
        from tests.conftest import _fast_verify

        await session.refresh(user)
        assert _fast_verify("NewPass456", user.hashed_password)

    async def test_wrong_old_password(self, session):
        tenant, user = await seed_tenant_and_user(session)
        with pytest.raises(BusinessError) as exc:
            await service.change_password(session, user.id, "wrongpass", "NewPass456")
        assert exc.value.status_code == 400
