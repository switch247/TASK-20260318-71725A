"""Bootstrap FastAPI application with lifespan startup initialization and global handlers."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.router import api_router
from src.core.config import get_settings
from src.core.errors import AppError
from src.core.https import HttpsEnforcementMiddleware
from src.core.logging import configure_logging
from src.core.metrics import increment
import src.db.session as db_session
from src.services.seed_service import seed_role_permissions

settings = get_settings()
configure_logging(settings.app_debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    db_session.ensure_engine()
    session = db_session.SessionLocal()
    try:
        seed_role_permissions(session)
    finally:
        session.close()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

if settings.enforce_https:
    app.add_middleware(HttpsEnforcementMiddleware)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        increment("requests_total")
        response = await call_next(request)
        if response.status_code >= 400:
            increment("requests_failed_total")
        return response


app.add_middleware(MetricsMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    payload = {
        "code": exc.code,
        "message": exc.message,
        "details": exc.details or {},
    }
    return JSONResponse(status_code=exc.code, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", extra={"error_type": exc.__class__.__name__})
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "Internal server error", "details": {}},
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)

