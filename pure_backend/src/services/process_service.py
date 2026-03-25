"""Implement process definition parsing, task execution, and SLA reminder orchestration."""

import json
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.models.enums import ProcessStatus, TaskStatus, WorkflowType
from src.models.process import (
    ProcessAuditTrail,
    ProcessDefinition,
    ProcessInstance,
)
from src.repositories.process_repository import ProcessRepository
from src.schemas.process import (
    CreateProcessDefinitionRequest,
    DecideTaskRequest,
    ProcessInstanceResponse,
    ReminderDispatchResponse,
    SubmitProcessRequest,
)
from src.services.operation_logger import OperationLogger
from src.services.process_engine import ProcessEngine
from src.services.process_handlers import ProcessDecisionHandler
from src.services.process_parser import ProcessParser


class ProcessService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ProcessRepository(session)
        self.settings = get_settings()
        self.operation_logger = OperationLogger(session)
        self.parser = ProcessParser()
        self.engine = ProcessEngine()
        self.decision_handler = ProcessDecisionHandler()

    def create_definition(
        self,
        organization_id: str,
        request: CreateProcessDefinitionRequest,
        trace_id: str | None = None,
    ) -> ProcessDefinition:
        try:
            workflow_type = WorkflowType(request.workflow_type)
        except ValueError as exc:
            raise ValidationError("Invalid workflow type") from exc

        self.parser.parse_definition_json(request.definition_json)
        definition = ProcessDefinition(
            organization_id=organization_id,
            name=request.name,
            workflow_type=workflow_type,
            definition_json=request.definition_json,
            version=1,
            is_active=True,
        )
        self.repository.create_definition(definition)
        self.operation_logger.log(
            actor_id=None,
            organization_id=organization_id,
            resource_type="process_definition",
            resource_id=definition.id,
            operation="create",
            trace_id=trace_id,
            after={"name": definition.name, "workflow_type": definition.workflow_type.value},
        )
        self.session.commit()
        return definition

    def submit_process(
        self,
        organization_id: str,
        user_id: str,
        request: SubmitProcessRequest,
        trace_id: str | None = None,
    ) -> ProcessInstanceResponse:
        existing_by_idempotency = self.repository.find_by_idempotency_key(
            organization_id,
            request.idempotency_key,
        )
        if existing_by_idempotency is not None:
            if existing_by_idempotency.business_number != request.business_number:
                raise ConflictError(
                    "Idempotency key already exists for a different business number",
                    details={"idempotency_key": request.idempotency_key},
                )
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
        try:
            self.repository.create_instance(instance)

            tasks = self.engine.build_initial_tasks(
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
            response = ProcessInstanceResponse(
                id=instance.id,
                status=instance.status.value,
                business_number=instance.business_number,
                submitted_at=instance.submitted_at,
                due_at=instance.due_at,
            )
            self.operation_logger.log(
                actor_id=user_id,
                organization_id=organization_id,
                resource_type="process_instance",
                resource_id=instance.id,
                operation="create",
                trace_id=trace_id,
                after={
                    "business_number": instance.business_number,
                    "status": instance.status.value,
                },
            )
            self.session.commit()
            return response
        except IntegrityError as exc:
            self.session.rollback()
            existing = self.repository.find_by_idempotency_key(
                organization_id, request.idempotency_key
            )
            if existing is not None and existing.business_number == request.business_number:
                return self._map_instance(existing)
            raise ConflictError(
                "Idempotency key already exists for a different business number",
                details={"idempotency_key": request.idempotency_key},
            ) from exc

    def dispatch_sla_reminders(
        self, organization_id: str, trace_id: str | None = None
    ) -> ReminderDispatchResponse:
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
            self.operation_logger.log(
                actor_id=None,
                organization_id=organization_id,
                resource_type="process_instance",
                resource_id=instance.id,
                operation="reminder_sent",
                trace_id=trace_id,
                after={"due_at": instance.due_at.isoformat()},
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
        self,
        organization_id: str,
        user_id: str,
        request: DecideTaskRequest,
        trace_id: str | None = None,
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
        has_rejection, all_done = self.decision_handler.determine_completion(tasks)

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
        self.operation_logger.log(
            actor_id=user_id,
            organization_id=organization_id,
            resource_type="process_task",
            resource_id=task.id,
            operation="decision",
            trace_id=trace_id,
            before={"task_status": "pending"},
            after={"task_status": task.task_status.value, "decision": request.decision},
        )
        self.session.commit()
        return {"task_id": task.id, "status": task.task_status.value}

    def _map_instance(self, instance: ProcessInstance) -> ProcessInstanceResponse:
        return ProcessInstanceResponse(
            id=instance.id,
            status=instance.status.value,
            business_number=instance.business_number,
            submitted_at=instance.submitted_at,
            due_at=instance.due_at,
        )
