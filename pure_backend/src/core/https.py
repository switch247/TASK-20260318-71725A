from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.core.config import get_settings


class HttpsEnforcementMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, trusted_proxies: list[str] | None = None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        runtime_settings = get_settings()
        self.trusted_proxy_headers = runtime_settings.trusted_proxy_headers
        self.trusted_proxies = (
            trusted_proxies if trusted_proxies is not None else runtime_settings.trusted_proxies
        )

    def _is_trusted_proxy(self, request: Request) -> bool:
        client = request.client
        if client is None:
            return False
        return client.host in self.trusted_proxies

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path.startswith("/api"):
            forwarded_proto = request.headers.get("x-forwarded-proto", "")
            forwarded_https = forwarded_proto.lower() == "https"
            trusted_forwarded_https = (
                self.trusted_proxy_headers
                and forwarded_https
                and self._is_trusted_proxy(request)
            )
            if request.url.scheme != "https" and not trusted_forwarded_https:
                return JSONResponse(
                    status_code=400,
                    content={
                        "code": 400,
                        "message": "HTTPS is required",
                        "details": {},
                    },
                )
        return await call_next(request)
