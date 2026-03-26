from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.security import Attachment, ImmutableAuditLog, OperationLog
from src.repositories.process_repository import ProcessRepository


class SecurityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_attachment_by_fingerprint(
        self, organization_id: str, fingerprint: str
    ) -> Attachment | None:
        stmt = select(Attachment).where(
            Attachment.organization_id == organization_id,
            Attachment.sha256_fingerprint == fingerprint,
        )
        return self.session.scalar(stmt)

    def create_attachment(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        self.session.flush()
        return attachment

    def get_attachment(self, attachment_id: str) -> Attachment | None:
        stmt = select(Attachment).where(Attachment.id == attachment_id)
        return self.session.scalar(stmt)

    def process_instance_belongs_to_business(
        self, organization_id: str, process_instance_id: str, business_number: str
    ) -> bool:
        process_repository = ProcessRepository(self.session)
        instance = process_repository.get_instance_by_id(organization_id, process_instance_id)
        if instance is None:
            return False
        return instance.business_number == business_number

    def create_operation_log(self, log: OperationLog) -> None:
        self.session.add(log)
        self.session.flush()

    def latest_audit_log(self) -> ImmutableAuditLog | None:
        stmt = select(ImmutableAuditLog).order_by(desc(ImmutableAuditLog.created_at)).limit(1)
        return self.session.scalar(stmt)

    def create_immutable_audit_log(self, log: ImmutableAuditLog) -> ImmutableAuditLog:
        self.session.add(log)
        self.session.flush()
        return log
