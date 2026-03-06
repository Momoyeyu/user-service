from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, NoReturn

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from jwt import PyJWT, PyJWTError
from starlette.routing import Match

from src.common import resp
from src.common.erri import unauthorized
from src.conf.config import settings

_jwt = PyJWT()

# --- JWT Claims ---


@dataclass(frozen=True)
class JWTClaims:
    sub: str
    uid: int
    tid: int
    rol: str
    exp: int
    iat: int

    @property
    def username(self) -> str:
        return self.sub

    @property
    def user_id(self) -> int:
        return self.uid

    @property
    def tenant_id(self) -> int:
        return self.tid

    @property
    def user_role(self) -> str:
        return self.rol


# --- Token verification ---


def verify_token(token: str) -> JWTClaims:
    """验证 JWT token 并返回 Claims。"""
    try:
        payload = _jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return JWTClaims(**{k: payload[k] for k in ("sub", "uid", "tid", "rol", "exp", "iat")})
    except PyJWTError:
        raise unauthorized("Invalid token") from None


# --- FastAPI dependency ---


def get_claims(request: Request) -> JWTClaims:
    """从 request.state 中提取中间件已验证的 JWT Claims。"""
    claims = getattr(request.state, "claims", None)
    if not claims:
        raise unauthorized("Unauthorized")
    return claims


# --- @exempt decorator ---

_EXEMPT_ATTR = "__jwt_exempt__"


def exempt[TFunc: Callable[..., Any]](fn: TFunc) -> TFunc:
    """标记免鉴权端点。"""
    setattr(fn, _EXEMPT_ATTR, True)
    return fn


# --- Middleware setup ---

EXEMPT_PATHS: set[str] = {"/", "/health", "/docs", "/redoc", "/openapi.json"}
_ROUTES_FROZEN_ATTR = "__jwt_routes_frozen__"
_SETUP_ATTR = "__jwt_middleware_installed__"


def _build_exempt_paths(app: FastAPI) -> set[str]:
    """收集所有被 @exempt 标记的端点路径。"""
    paths: set[str] = set()
    for route in list(app.router.routes):
        if isinstance(route, APIRoute) and getattr(route.endpoint, _EXEMPT_ATTR, False):
            paths.add(route.path)
    return paths


def _freeze_route_registration(app: FastAPI) -> None:
    """冻结路由注册，防止中间件安装后新增路由绕过鉴权。"""
    if getattr(app, _ROUTES_FROZEN_ATTR, False):
        return
    setattr(app, _ROUTES_FROZEN_ATTR, True)

    def _blocked(*_: object, **__: object) -> NoReturn:
        raise RuntimeError("Routes are frozen. Register all routes before setup_auth_middleware.")

    app.include_router = _blocked  # type: ignore[assignment]
    app.add_api_route = _blocked  # type: ignore[assignment]
    app.add_route = _blocked  # type: ignore[assignment]
    app.mount = _blocked  # type: ignore[assignment]
    app.router.include_router = _blocked  # type: ignore[assignment]
    app.router.add_api_route = _blocked  # type: ignore[assignment]


def _is_exempt_endpoint(app: FastAPI, request: Request) -> bool:
    """检查请求端点是否免鉴权。"""
    if request.url.path in EXEMPT_PATHS:
        return True

    for route in app.router.routes:
        if not isinstance(route, APIRoute):
            continue
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route.endpoint, _EXEMPT_ATTR, False)

    return False


def setup_auth_middleware(app: FastAPI) -> None:
    """安装全局 JWT 鉴权中间件。"""
    if getattr(app, _SETUP_ATTR, False):
        return

    EXEMPT_PATHS.update(_build_exempt_paths(app))
    _freeze_route_registration(app)
    setattr(app, _SETUP_ATTR, True)

    @app.middleware("http")
    async def jwt_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if _is_exempt_endpoint(app, request):
            return await call_next(request)

        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content=resp.error(resp.Code.UNAUTHORIZED, "Unauthorized").model_dump(),
            )

        token = auth.split(" ", 1)[1]
        try:
            claims = verify_token(token)
        except Exception as e:
            detail = getattr(e, "detail", "Invalid token")
            return JSONResponse(
                status_code=401,
                content=resp.error(resp.Code.UNAUTHORIZED, detail).model_dump(),
            )

        request.state.claims = claims
        return await call_next(request)
