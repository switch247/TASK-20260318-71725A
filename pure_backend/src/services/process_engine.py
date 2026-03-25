"""Evaluate workflow conditions and build task descriptors for process execution."""

import json
from datetime import datetime

from src.models.enums import TaskStatus
from src.models.process import ProcessTaskAssignment
from src.services.process_parser import ProcessParser


class ProcessEngine:
    def __init__(self) -> None:
        self.parser = ProcessParser()

    def build_initial_tasks(
        self,
        organization_id: str,
        process_instance_id: str,
        fallback_assignee_user_id: str,
        due_at: datetime,
        definition_json: str,
        payload_json: str,
    ) -> list[ProcessTaskAssignment]:
        payload = self.parser.parse_payload_json(payload_json)
        workflow_nodes = self.parser.parse_nodes(definition_json, fallback_assignee_user_id)

        tasks: list[ProcessTaskAssignment] = []
        for node in workflow_nodes:
            if self._evaluate_node_condition(definition_json, node.key, payload):
                tasks.append(
                    ProcessTaskAssignment(
                        organization_id=organization_id,
                        process_instance_id=process_instance_id,
                        assignee_user_id=node.assignee_user_id,
                        task_node_key=node.key,
                        task_status=TaskStatus.PENDING,
                        is_joint_sign=node.is_joint_sign,
                        is_parallel=node.is_parallel,
                        due_at=due_at,
                        comment=None,
                    )
                )

        if len(tasks) == 0:
            tasks.append(
                ProcessTaskAssignment(
                    organization_id=organization_id,
                    process_instance_id=process_instance_id,
                    assignee_user_id=fallback_assignee_user_id,
                    task_node_key="review-node-1",
                    task_status=TaskStatus.PENDING,
                    is_joint_sign=False,
                    is_parallel=False,
                    due_at=due_at,
                    comment=None,
                )
            )
        return tasks

    def _evaluate_node_condition(
        self,
        definition_json: str,
        node_key: str,
        payload: dict[str, object],
    ) -> bool:
        definition = json.loads(definition_json)
        nodes = definition.get("nodes", [])
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if str(node.get("key")) != node_key:
                continue

            condition = node.get("condition")
            if condition is None:
                return True
            if not isinstance(condition, dict):
                return False

            field_name = condition.get("field")
            operator = condition.get("operator", "eq")
            expected_value = condition.get("value")

            if not isinstance(field_name, str):
                return False

            actual_value = payload.get(field_name)
            if operator == "eq":
                return actual_value == expected_value
            if (
                operator == "gt"
                and isinstance(actual_value, (int, float))
                and isinstance(expected_value, (int, float))
            ):
                return actual_value > expected_value
            if (
                operator == "gte"
                and isinstance(actual_value, (int, float))
                and isinstance(expected_value, (int, float))
            ):
                return actual_value >= expected_value
            if (
                operator == "lt"
                and isinstance(actual_value, (int, float))
                and isinstance(expected_value, (int, float))
            ):
                return actual_value < expected_value
            if (
                operator == "lte"
                and isinstance(actual_value, (int, float))
                and isinstance(expected_value, (int, float))
            ):
                return actual_value <= expected_value
            return False
        return False
