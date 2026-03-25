from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class HttpsEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path.startswith("/api"):
            forwarded_proto = request.headers.get("x-forwarded-proto", "")
            if request.url.scheme != "https" and forwarded_proto.lower() != "https":
                return JSONResponse(
                    status_code=400,
                    content={
                        "code": 400,
                        "message": "HTTPS is required",
                        "details": {},
                    },
                )
        return await call_next(request)
