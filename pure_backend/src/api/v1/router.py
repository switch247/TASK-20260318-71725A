from fastapi import APIRouter

from src.api.v1.endpoints import (
    analytics,
    auth,
    governance,
    health,
    medical_ops,
    organizations,
    process,
    security,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(organizations.router, tags=["organizations"])
api_router.include_router(process.router, tags=["process"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(governance.router, tags=["governance"])
api_router.include_router(security.router, tags=["security"])
api_router.include_router(medical_ops.router, tags=["operations"])
