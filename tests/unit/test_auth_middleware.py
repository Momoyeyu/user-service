import time
from unittest.mock import MagicMock

import pytest
from jwt import PyJWT

from src.conf.config import settings
from src.middleware.auth import JWTClaims, get_claims, verify_token

_jwt = PyJWT()


def _make_token(overrides: dict = None, expired: bool = False) -> str:
    now = int(time.time())
    payload = {
        "sub": "alice",
        "uid": 1,
        "tid": 10,
        "rol": "owner",
        "iat": now,
        "exp": now - 10 if expired else now + 3600,
    }
    if overrides:
        payload.update(overrides)
    return _jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class TestJWTClaims:
    def test_properties(self):
        claims = JWTClaims(sub="alice", uid=1, tid=10, rol="owner", exp=0, iat=0)
        assert claims.username == "alice"
        assert claims.user_id == 1
        assert claims.tenant_id == 10
        assert claims.user_role == "owner"

    def test_frozen(self):
        claims = JWTClaims(sub="alice", uid=1, tid=10, rol="owner", exp=0, iat=0)
        with pytest.raises(AttributeError):
            claims.sub = "bob"  # type: ignore


class TestVerifyToken:
    def test_valid_token(self):
        token = _make_token()
        claims = verify_token(token)
        assert claims.username == "alice"
        assert claims.user_id == 1
        assert claims.tenant_id == 10
        assert claims.user_role == "owner"

    def test_expired_token(self):
        token = _make_token(expired=True)
        with pytest.raises(Exception) as exc:
            verify_token(token)
        assert exc.value.status_code == 401

    def test_invalid_token(self):
        with pytest.raises(Exception) as exc:
            verify_token("not.a.valid.token")
        assert exc.value.status_code == 401

    def test_wrong_secret(self):
        token = _jwt.encode(
            {"sub": "alice", "uid": 1, "tid": 10, "rol": "owner", "iat": 0, "exp": int(time.time()) + 3600},
            "wrong-secret-that-is-at-least-32-bytes-long",
            algorithm="HS256",
        )
        with pytest.raises(Exception) as exc:
            verify_token(token)
        assert exc.value.status_code == 401


class TestGetClaims:
    def test_has_claims(self):
        request = MagicMock()
        request.state.claims = JWTClaims(sub="alice", uid=1, tid=10, rol="owner", exp=0, iat=0)
        result = get_claims(request)
        assert result.username == "alice"

    def test_no_claims(self):
        request = MagicMock()
        request.state = MagicMock(spec=[])  # no claims attribute
        with pytest.raises(Exception) as exc:
            get_claims(request)
        assert exc.value.status_code == 401
