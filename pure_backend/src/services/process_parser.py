"""Parse and validate process definition and payload structures."""

import json

from src.core.errors import ValidationError
from src.core.workflow import WorkflowNode, parse_workflow_nodes


class ProcessParser:
    def parse_definition_json(self, definition_json: str) -> dict[str, object]:
        try:
            data = json.loads(definition_json)
        except json.JSONDecodeError as exc:
            raise ValidationError("Invalid workflow definition JSON") from exc
        if not isinstance(data, dict):
            raise ValidationError("Workflow definition must be a JSON object")
        return data

    def parse_payload_json(self, payload_json: str) -> dict[str, object]:
        try:
            data = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise ValidationError("Payload must be valid JSON") from exc
        if not isinstance(data, dict):
            raise ValidationError("Payload must be a JSON object")
        return data

    def parse_nodes(
        self, definition_json: str, fallback_assignee_user_id: str
    ) -> list[WorkflowNode]:
        return parse_workflow_nodes(definition_json, fallback_assignee_user_id)
