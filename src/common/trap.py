"""Global exception handlers.

Path: raise erri.xxx() → trap catches → resp formats → JSONResponse out.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from src.common import resp
from src.common.erri import BusinessError


async def _handle_business_error(_request: Request, exc: BusinessError) -> JSONResponse:
    """BusinessError already carries code + status_code. Just format and return."""
    return JSONResponse(
        status_code=exc.status_code,
        content=resp.error(exc.code, exc.detail).model_dump(),
    )


async def _handle_http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    """FastAPI/Starlette HTTP exceptions (e.g. 422 from path params)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=resp.error(resp.Code.INTERNAL_ERROR, exc.detail).model_dump(),
    )


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic request validation failures."""
    return JSONResponse(
        status_code=422,
        content=resp.error(resp.Code.BAD_REQUEST, "Validation failed", data=exc.errors()).model_dump(),
    )


async def _handle_generic_error(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log and return generic 500."""
    logger.exception("Unhandled exception: {}", exc)
    return JSONResponse(
        status_code=500,
        content=resp.error(resp.Code.INTERNAL_ERROR, "Internal server error").model_dump(),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BusinessError, _handle_business_error)
    app.add_exception_handler(HTTPException, _handle_http_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_generic_error)
