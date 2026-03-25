from pydantic import BaseModel, Field


class CreateOrganizationRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)


class JoinOrganizationRequest(BaseModel):
    organization_code: str = Field(min_length=2, max_length=64)


class OrganizationResponse(BaseModel):
    id: str
    code: str
    name: str
