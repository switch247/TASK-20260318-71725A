import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.v1.router import api_router
from src.core.config import get_settings
from src.core.errors import AppError
from src.core.https import HttpsEnforcementMiddleware
from src.core.logging import configure_logging
from src.db.base import Base
from src.db.session import SessionLocal, engine
from src.services.seed_service import seed_role_permissions

settings = get_settings()
configure_logging(settings.app_debug)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

if settings.enforce_https:
    app.add_middleware(HttpsEnforcementMiddleware)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_role_permissions(session)
    finally:
        session.close()


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
    logger.exception("Unhandled exception", extra={"error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "Internal server error", "details": {}},
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
