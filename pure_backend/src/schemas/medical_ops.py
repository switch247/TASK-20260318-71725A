from datetime import datetime

from pydantic import BaseModel, Field


class AdvancedSearchRequest(BaseModel):
    resource: str = Field(pattern="^(appointments|patients|doctors|expenses)$")
    keyword: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=255)
    min_amount: float | None = None
    max_amount: float | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
