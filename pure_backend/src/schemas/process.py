from datetime import datetime

from pydantic import BaseModel, Field


class CreateProcessDefinitionRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    workflow_type: str
    definition_json: str


class SubmitProcessRequest(BaseModel):
    process_definition_id: str
    business_number: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=8, max_length=128)
    payload_json: str


class DecideTaskRequest(BaseModel):
    task_id: str
    decision: str = Field(pattern="^(approve|reject)$")
    comment: str | None = Field(default=None, max_length=2000)


class ProcessInstanceResponse(BaseModel):
    id: str
    status: str
    business_number: str
    submitted_at: datetime
    due_at: datetime


class ReminderDispatchResponse(BaseModel):
    reminded_count: int
    process_instance_ids: list[str]
