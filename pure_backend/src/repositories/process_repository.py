from datetime import datetime, timedelta, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.enums import ProcessStatus, TaskStatus
from src.models.process import (
    ProcessAuditTrail,
    ProcessDefinition,
    ProcessInstance,
    ProcessTaskAssignment,
)


class ProcessRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_definition(self, definition: ProcessDefinition) -> ProcessDefinition:
        self.session.add(definition)
        self.session.flush()
        return definition

    def find_definition(self, organization_id: str, definition_id: str) -> ProcessDefinition | None:
        stmt = select(ProcessDefinition).where(
            ProcessDefinition.id == definition_id,
            ProcessDefinition.organization_id == organization_id,
            ProcessDefinition.is_active.is_(True),
        )
        return self.session.scalar(stmt)

    def find_definition_by_id(self, definition_id: str) -> ProcessDefinition | None:
        stmt = select(ProcessDefinition).where(ProcessDefinition.id == definition_id)
        return self.session.scalar(stmt)

    def find_recent_by_business_number(
        self, organization_id: str, business_number: str
    ) -> ProcessInstance | None:
        threshold = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(ProcessInstance)
            .where(
                ProcessInstance.organization_id == organization_id,
                ProcessInstance.business_number == business_number,
                ProcessInstance.submitted_at >= threshold,
            )
            .order_by(ProcessInstance.submitted_at.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def find_by_idempotency_key(
        self, organization_id: str, idempotency_key: str
    ) -> ProcessInstance | None:
        stmt = select(ProcessInstance).where(
            ProcessInstance.organization_id == organization_id,
            ProcessInstance.idempotency_key == idempotency_key,
        )
        return self.session.scalar(stmt)

    def create_instance(self, instance: ProcessInstance) -> ProcessInstance:
        self.session.add(instance)
        self.session.flush()
        return instance

    def create_tasks(self, tasks: list[ProcessTaskAssignment]) -> None:
        self.session.add_all(tasks)
        self.session.flush()

    def get_pending_tasks(self, organization_id: str, user_id: str) -> list[ProcessTaskAssignment]:
        stmt = select(ProcessTaskAssignment).where(
            ProcessTaskAssignment.organization_id == organization_id,
            ProcessTaskAssignment.assignee_user_id == user_id,
            ProcessTaskAssignment.task_status.in_([TaskStatus.PENDING, TaskStatus.CLAIMED]),
        )
        return list(self.session.scalars(stmt))

    def get_task_by_id(self, organization_id: str, task_id: str) -> ProcessTaskAssignment | None:
        stmt = select(ProcessTaskAssignment).where(
            ProcessTaskAssignment.id == task_id,
            ProcessTaskAssignment.organization_id == organization_id,
        )
        return self.session.scalar(stmt)

    def get_instance_by_id(self, organization_id: str, instance_id: str) -> ProcessInstance | None:
        stmt = select(ProcessInstance).where(
            ProcessInstance.id == instance_id,
            ProcessInstance.organization_id == organization_id,
        )
        return self.session.scalar(stmt)

    def get_instance_tasks(self, instance_id: str) -> list[ProcessTaskAssignment]:
        stmt = select(ProcessTaskAssignment).where(
            ProcessTaskAssignment.process_instance_id == instance_id
        )
        return list(self.session.scalars(stmt))

    def add_audit(self, audit: ProcessAuditTrail) -> None:
        self.session.add(audit)
        self.session.flush()

    def finalize_instance(
        self, instance: ProcessInstance, approved: bool, result_json: str
    ) -> None:
        instance.status = ProcessStatus.APPROVED if approved else ProcessStatus.REJECTED
        instance.completed_at = datetime.now(UTC)
        instance.final_result_json = result_json
        self.session.flush()

    def list_instances_due_for_reminder(
        self, organization_id: str, reminder_deadline: datetime
    ) -> list[ProcessInstance]:
        stmt = select(ProcessInstance).where(
            ProcessInstance.organization_id == organization_id,
            ProcessInstance.status == ProcessStatus.IN_PROGRESS,
            ProcessInstance.due_at <= reminder_deadline,
            ProcessInstance.completed_at.is_(None),
        )
        return list(self.session.scalars(stmt))

    def has_reminder_audit(self, process_instance_id: str) -> bool:
        stmt = select(ProcessAuditTrail).where(
            ProcessAuditTrail.process_instance_id == process_instance_id,
            ProcessAuditTrail.event_type == "sla_reminder_sent",
        )
        return self.session.scalar(stmt) is not None
