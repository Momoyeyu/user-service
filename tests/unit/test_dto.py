import pytest
from pydantic import ValidationError

from src.auth.dto import LoginRequest, RegisterRequest
from src.tenant.dto import TenantInfo, UpdateTenantRequest
from src.user.dto import ChangePasswordRequest, UpdateUserRequest, UserProfile


class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(identifier="alice", password="secret123")
        assert req.identifier == "alice"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            LoginRequest()


class TestRegisterRequest:
    def test_valid(self):
        req = RegisterRequest(
            email="alice@example.com",
            username="alice",
            password="Secret123",
            tenant_name="Alice Corp",
            invitation_code="ABC123",
        )
        assert req.email == "alice@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                username="alice",
                password="Secret123",
                tenant_name="Alice Corp",
                invitation_code="ABC123",
            )

    def test_weak_password_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="alice@example.com",
                username="alice",
                password="weak",
                tenant_name="Alice Corp",
                invitation_code="ABC123",
            )


class TestUserProfile:
    def test_valid(self):
        from datetime import datetime

        profile = UserProfile(
            id=1,
            email="alice@example.com",
            username="alice",
            role="owner",
            tenant_id=1,
            created_at=datetime.now(),
        )
        assert profile.id == 1


class TestUpdateUserRequest:
    def test_all_optional(self):
        req = UpdateUserRequest()
        assert req.email is None
        assert req.username is None


class TestChangePasswordRequest:
    def test_valid(self):
        req = ChangePasswordRequest(old_password="old", new_password="NewPass123")
        assert req.old_password == "old"

    def test_weak_password_rejected(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password="old", new_password="weak")


class TestTenantInfo:
    def test_valid(self):
        from datetime import datetime

        info = TenantInfo(id=1, name="Corp", status="active", created_at=datetime.now())
        assert info.name == "Corp"


class TestUpdateTenantRequest:
    def test_all_optional(self):
        req = UpdateTenantRequest()
        assert req.name is None
