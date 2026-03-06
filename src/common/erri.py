"""Business exceptions.

Each exception carries a business code (from resp.Code) and an HTTP status code.
Raise via factory functions; trap.py converts to {code, message, data} response.
"""

from __future__ import annotations

from src.common.resp import Code


class BusinessError(Exception):
    def __init__(self, *, code: int, status_code: int, detail: str):
        self.code = code
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def bad_request(detail: str) -> BusinessError:
    return BusinessError(code=Code.BAD_REQUEST, status_code=400, detail=detail)


def unauthorized(detail: str) -> BusinessError:
    return BusinessError(code=Code.UNAUTHORIZED, status_code=401, detail=detail)


def forbidden(detail: str) -> BusinessError:
    return BusinessError(code=Code.FORBIDDEN, status_code=403, detail=detail)


def not_found(detail: str) -> BusinessError:
    return BusinessError(code=Code.NOT_FOUND, status_code=404, detail=detail)


def conflict(detail: str) -> BusinessError:
    return BusinessError(code=Code.CONFLICT, status_code=409, detail=detail)


def internal(detail: str) -> BusinessError:
    return BusinessError(code=Code.INTERNAL_ERROR, status_code=500, detail=detail)
