import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.errors import ForbiddenError, NotFoundError, ValidationError
from src.core.workflow import parse_workflow_nodes
from src.models.enums import ProcessStatus, TaskStatus, WorkflowType
from src.models.process import (
    ProcessAuditTrail,
    ProcessDefinition,
    ProcessInstance,
    ProcessTaskAssignment,
)
from src.repositories.process_repository import ProcessRepository
from src.schemas.process import (
    CreateProcessDefinitionRequest,
    DecideTaskRequest,
    ProcessInstanceResponse,
    ReminderDispatchResponse,
    SubmitProcessRequest,
)


class ProcessService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ProcessRepository(session)
        self.settings = get_settings()

    def create_definition(
        self,
        organization_id: str,
        request: CreateProcessDefinitionRequest,
    ) -> ProcessDefinition:
        try:
            workflow_type = WorkflowType(request.workflow_type)
        except ValueError as exc:
            raise ValidationError("Invalid workflow type") from exc

        json.loads(request.definition_json)
        definition = ProcessDefinition(
            organization_id=organization_id,
            name=request.name,
            workflow_type=workflow_type,
            definition_json=request.definition_json,
            version=1,
            is_active=True,
        )
        self.repository.create_definition(definition)
        self.session.commit()
        return definition

    def submit_process(
        self,
        organization_id: str,
        user_id: str,
        request: SubmitProcessRequest,
    ) -> ProcessInstanceResponse:
        existing_by_idempotency = self.repository.find_by_idempotency_key(
            organization_id,
            request.idempotency_key,
        )
        if existing_by_idempotency is not None:
            return self._map_instance(existing_by_idempotency)

        recent_by_business = self.repository.find_recent_by_business_number(
            organization_id,
            request.business_number,
        )
        if recent_by_business is not None:
            return self._map_instance(recent_by_business)

        definition = self.repository.find_definition(organization_id, request.process_definition_id)
        if definition is None:
            raise NotFoundError("Process definition not found")

        due_at = datetime.utcnow() + timedelta(hours=self.settings.default_sla_hours)
        instance = ProcessInstance(
            organization_id=organization_id,
            process_definition_id=definition.id,
            requested_by_user_id=user_id,
            business_number=request.business_number,
            idempotency_key=request.idempotency_key,
            status=ProcessStatus.IN_PROGRESS,
            submitted_at=datetime.utcnow(),
            due_at=due_at,
            payload_json=request.payload_json,
            final_result_json=None,
        )
        self.repository.create_instance(instance)

        tasks = self._build_initial_tasks(
            organization_id,
            instance.id,
            user_id,
            due_at,
            definition.definition_json,
            request.payload_json,
        )
        self.repository.create_tasks(tasks)
        reminder_at = due_at - timedelta(hours=self.settings.reminder_lead_hours)
        self.repository.add_audit(
            ProcessAuditTrail(
                organization_id=organization_id,
                process_instance_id=instance.id,
                actor_user_id=user_id,
                event_type="process_submitted",
                event_payload_json=json.dumps(
                    {
                        "payload": json.loads(request.payload_json),
                        "reminder_at": reminder_at.isoformat(),
                        "task_count": len(tasks),
                    }
                ),
            )
        )
        self.session.commit()
        return self._map_instance(instance)

    def dispatch_sla_reminders(self, organization_id: str) -> ReminderDispatchResponse:
        reminder_deadline = datetime.utcnow() + timedelta(hours=self.settings.reminder_lead_hours)
        instances = self.repository.list_instances_due_for_reminder(
            organization_id, reminder_deadline
        )

        reminded_instance_ids: list[str] = []
        for instance in instances:
            if self.repository.has_reminder_audit(instance.id):
                continue

            self.repository.add_audit(
                ProcessAuditTrail(
                    organization_id=organization_id,
                    process_instance_id=instance.id,
                    actor_user_id=None,
                    event_type="sla_reminder_sent",
                    event_payload_json=json.dumps(
                        {
                            "due_at": instance.due_at.isoformat(),
                            "business_number": instance.business_number,
                        }
                    ),
                )
            )
            reminded_instance_ids.append(instance.id)

        self.session.commit()
        return ReminderDispatchResponse(
            reminded_count=len(reminded_instance_ids),
            process_instance_ids=reminded_instance_ids,
        )

    def list_pending_tasks(self, organization_id: str, user_id: str) -> list[dict[str, str]]:
        tasks = self.repository.get_pending_tasks(organization_id, user_id)
        return [
            {
                "id": task.id,
                "process_instance_id": task.process_instance_id,
                "task_status": task.task_status.value,
                "task_node_key": task.task_node_key,
                "is_parallel": str(task.is_parallel).lower(),
                "is_joint_sign": str(task.is_joint_sign).lower(),
            }
            for task in tasks
        ]

    def decide_task(
        self, organization_id: str, user_id: str, request: DecideTaskRequest
    ) -> dict[str, str]:
        task = self.repository.get_task_by_id(organization_id, request.task_id)
        if task is None:
            raise NotFoundError("Task not found")
        if task.assignee_user_id != user_id:
            raise ForbiddenError("Task is not assigned to current user")
        if task.task_status not in [TaskStatus.PENDING, TaskStatus.CLAIMED]:
            raise ValidationError("Task already decided")

        task.task_status = (
            TaskStatus.APPROVED if request.decision == "approve" else TaskStatus.REJECTED
        )
        task.decided_at = datetime.utcnow()
        task.comment = request.comment

        instance = self.repository.get_instance_by_id(organization_id, task.process_instance_id)
        if instance is None:
            raise NotFoundError("Process instance not found")

        tasks = self.repository.get_instance_tasks(instance.id)
        has_rejection = any(item.task_status == TaskStatus.REJECTED for item in tasks)
        all_done = all(
            item.task_status in [TaskStatus.APPROVED, TaskStatus.REJECTED] for item in tasks
        )

        if has_rejection:
            self.repository.finalize_instance(
                instance, approved=False, result_json='{"result":"rejected"}'
            )
        elif all_done:
            self.repository.finalize_instance(
                instance, approved=True, result_json='{"result":"approved"}'
            )

        self.repository.add_audit(
            ProcessAuditTrail(
                organization_id=organization_id,
                process_instance_id=instance.id,
                actor_user_id=user_id,
                event_type="task_decided",
                event_payload_json=json.dumps({"task_id": task.id, "decision": request.decision}),
            )
        )
        self.session.commit()
        return {"task_id": task.id, "status": task.task_status.value}

    def _build_initial_tasks(
        self,
        organization_id: str,
        process_instance_id: str,
        fallback_assignee_user_id: str,
        due_at: datetime,
        definition_json: str,
        payload_json: str,
    ) -> list[ProcessTaskAssignment]:
        import json

        payload = json.loads(payload_json)
        workflow_nodes = parse_workflow_nodes(definition_json, fallback_assignee_user_id)

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
        import json

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

    def _map_instance(self, instance: ProcessInstance) -> ProcessInstanceResponse:
        return ProcessInstanceResponse(
            id=instance.id,
            status=instance.status.value,
            business_number=instance.business_number,
            submitted_at=instance.submitted_at,
            due_at=instance.due_at,
        )
