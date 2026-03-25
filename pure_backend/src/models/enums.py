import enum


class RoleName(str, enum.Enum):
    ADMINISTRATOR = "administrator"
    REVIEWER = "reviewer"
    GENERAL_USER = "general_user"
    AUDITOR = "auditor"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    DISABLED = "disabled"


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    INVITED = "invited"
    REVOKED = "revoked"


class WorkflowType(str, enum.Enum):
    RESOURCE_APPLICATION = "resource_application"
    CREDIT_CHANGE = "credit_change"


class ProcessStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExportStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
