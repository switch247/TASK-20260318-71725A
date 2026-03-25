"""Implement operational resource search with consistent pagination semantics."""

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
        total_count = len(items)
        start = (request.page - 1) * request.limit
        end = start + request.limit
        paged_items = items[start:end]
        return {
            "resource": request.resource,
            "count": len(paged_items),
            "total_count": total_count,
            "page": request.page,
            "limit": request.limit,
            "items": paged_items,
        }
