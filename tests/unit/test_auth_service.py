from tests.conftest import _fast_hash, _fast_verify


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = _fast_hash("mypassword")
        assert _fast_verify("mypassword", hashed)
        assert not _fast_verify("wrong", hashed)

    def test_hash_is_deterministic(self):
        assert _fast_hash("test") == _fast_hash("test")

    def test_different_passwords_different_hashes(self):
        assert _fast_hash("a") != _fast_hash("b")


class TestAccessToken:
    def test_create_and_decode(self):
        from unittest.mock import MagicMock

        from src.auth.service import create_access_token
        from src.middleware.auth import verify_token

        user = MagicMock()
        user.id = 42
        user.username = "alice"
        user.tenant_id = 10
        user.role = "owner"

        token = create_access_token(user)
        claims = verify_token(token)

        assert claims.user_id == 42
        assert claims.username == "alice"
        assert claims.tenant_id == 10
        assert claims.user_role == "owner"
