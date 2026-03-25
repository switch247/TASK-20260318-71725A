from sqlalchemy.orm import Session

from src.repositories.medical_ops_repository import MedicalOpsRepository
from src.schemas.medical_ops import AdvancedSearchRequest


class MedicalOpsService:
    def __init__(self, session: Session) -> None:
        self.repository = MedicalOpsRepository(session)

    def advanced_search(
        self, organization_id: str, request: AdvancedSearchRequest
    ) -> dict[str, object]:
        items = self.repository.advanced_search(organization_id, request)
        return {"resource": request.resource, "count": len(items), "items": items}
