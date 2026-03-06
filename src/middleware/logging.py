import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from loguru import logger

EXCLUDED_PATHS = {"/docs", "/redoc", "/openapi.json"}
EXCLUDED_PREFIXES = ("/.well-known/",)


def setup_logging_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = request.url.path
        if path in EXCLUDED_PATHS or path.startswith(EXCLUDED_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "{method} {path} -> {status} ({duration:.1f}ms)",
            method=request.method,
            path=path,
            status=response.status_code,
            duration=duration_ms,
        )
        return response
