from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.auth.handler import router as auth_router
from src.common.trap import setup_exception_handlers
from src.conf.logging import setup_logging
from src.conf.openapi import OPENAPI_CONFIG, TAGS_METADATA, oauth2_router, setup_openapi
from src.invitation.handler import router as internal_router
from src.middleware.auth import setup_auth_middleware
from src.middleware.logging import setup_logging_middleware
from src.tenant.handler import router as tenant_router
from src.user.handler import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from src.conf.db import check_db, close_db

    await check_db()
    logger.info("Application started")
    yield
    logger.info("Application shutdown")
    await close_db()


setup_logging()

app = FastAPI(
    **OPENAPI_CONFIG,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

# Register routes BEFORE middleware (middleware freezes route registration)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(tenant_router)
app.include_router(internal_router)
app.include_router(oauth2_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Setup middleware and exception handlers AFTER routes
setup_exception_handlers(app)
setup_auth_middleware(app)
setup_logging_middleware(app)

# Swagger OAuth2 integration
setup_openapi(app)
