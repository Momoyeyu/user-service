from src.common.erri import BusinessError, bad_request, conflict, forbidden, internal, not_found, unauthorized
from src.common.resp import Code


class TestBusinessError:
    def test_is_exception(self):
        err = BusinessError(code=Code.BAD_REQUEST, status_code=400, detail="test")
        assert isinstance(err, Exception)

    def test_attributes(self):
        err = BusinessError(code=9999, status_code=418, detail="I'm a teapot")
        assert err.code == 9999
        assert err.status_code == 418
        assert err.detail == "I'm a teapot"
        assert str(err) == "I'm a teapot"


class TestErrorFactories:
    def test_bad_request(self):
        err = bad_request("invalid input")
        assert err.code == Code.BAD_REQUEST
        assert err.status_code == 400
        assert err.detail == "invalid input"

    def test_unauthorized(self):
        err = unauthorized("no token")
        assert err.code == Code.UNAUTHORIZED
        assert err.status_code == 401

    def test_forbidden(self):
        err = forbidden("no access")
        assert err.code == Code.FORBIDDEN
        assert err.status_code == 403

    def test_not_found(self):
        err = not_found("missing")
        assert err.code == Code.NOT_FOUND
        assert err.status_code == 404

    def test_conflict(self):
        err = conflict("duplicate")
        assert err.code == Code.CONFLICT
        assert err.status_code == 409

    def test_internal(self):
        err = internal("server error")
        assert err.code == Code.INTERNAL_ERROR
        assert err.status_code == 500
