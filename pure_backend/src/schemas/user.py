from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    username: str
    display_name: str
    email: str | None
