"""Define user response contracts with optional masking-aware fields."""

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    username: str
    display_name: str
    email: str | None
    role_name: str | None = None
