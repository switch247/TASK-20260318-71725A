from pydantic import BaseModel, Field


class CreateAttachmentRequest(BaseModel):
    process_instance_id: str | None = None
    business_number: str | None = None
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=3, max_length=128)
    file_size_bytes: int = Field(gt=0)
    file_content_base64: str


class AuditEventRequest(BaseModel):
    event_type: str = Field(min_length=2, max_length=100)
    event_payload_json: str
