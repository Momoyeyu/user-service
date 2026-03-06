from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Code:
    """Business error codes. HTTP status codes are preserved separately.

    - 0: Success
    - 1xxx: Authentication/Authorization
    - 2xxx: Validation/Input
    - 3xxx: Resource errors
    - 5xxx: Internal/System
    """

    OK = 0
    UNAUTHORIZED = 1001
    FORBIDDEN = 1002
    BAD_REQUEST = 2001
    NOT_FOUND = 3001
    CONFLICT = 3002
    INTERNAL_ERROR = 5001


class Response(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


def ok(data: Any = None, message: str = "ok") -> Response:
    return Response(code=Code.OK, message=message, data=data)


def error(code: int, message: str, data: Any = None) -> Response:
    return Response(code=code, message=message, data=data)
