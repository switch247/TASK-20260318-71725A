from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    code: int
    message: str
    details: dict[str, object]
