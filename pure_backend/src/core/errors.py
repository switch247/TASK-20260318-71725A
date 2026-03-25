"""Define application-level exception types and HTTP code mapping."""

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: int
    message: str
    details: dict[str, str] | dict[str, object] | None = None


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(code=401, message=message, details=None)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(code=403, message=message, details=None)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(code=404, message=message, details=None)


class ValidationError(AppError):
    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(code=400, message=message, details=details)


class ConflictError(AppError):
    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(code=409, message=message, details=details)
