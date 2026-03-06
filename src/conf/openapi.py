from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service as auth_service
from src.common.erri import BusinessError
from src.conf.config import settings as _settings
from src.conf.db import get_db
from src.conf.redis import get_redis
from src.middleware.auth import _EXEMPT_ATTR, exempt

OPENAPI_CONFIG = {
    "title": _settings.APP_NAME,
    "description": "统一用户认证与管理服务",
    "version": "0.1.0",
}

TAGS_METADATA = [
    {"name": "auth", "description": "认证相关接口（注册、登录、token 刷新等）"},
    {"name": "users", "description": "用户信息管理"},
    {"name": "tenants", "description": "租户管理"},
    {"name": "internal", "description": "内部服务间调用接口（API Key 鉴权）"},
]

# OAuth2-compatible token endpoint for Swagger UI
oauth2_router = APIRouter(tags=["oauth2"])


@exempt
@oauth2_router.post("/oauth2/token", include_in_schema=False)
async def swagger_oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """OAuth2-compatible login endpoint for Swagger UI."""
    try:
        result = await auth_service.login(db, redis, form_data.username, form_data.password)
        return {"access_token": result.access_token, "token_type": "bearer"}
    except BusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None


def setup_openapi(app: FastAPI) -> None:
    """Configure custom OpenAPI schema with OAuth2 for Swagger UI."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add OAuth2 Password Flow security scheme
        openapi_schema.setdefault("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/oauth2/token",
                        "scopes": {},
                    }
                },
            }
        }

        # Add security requirement to non-exempt routes
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            if getattr(route.endpoint, _EXEMPT_ATTR, False):
                continue
            path = openapi_schema["paths"].get(route.path, {})
            for method in route.methods or []:
                method_lower = method.lower()
                if method_lower in path:
                    path[method_lower]["security"] = [{"OAuth2PasswordBearer": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
