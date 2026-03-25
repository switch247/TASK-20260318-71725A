from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.medical_ops import Appointment, Doctor, Expense, Patient
from src.schemas.medical_ops import AdvancedSearchRequest


class MedicalOpsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def advanced_search(
        self, organization_id: str, request: AdvancedSearchRequest
    ) -> list[dict[str, object]]:
        if request.resource == "appointments":
            return self._search_appointments(organization_id, request)
        if request.resource == "patients":
            return self._search_patients(organization_id, request)
        if request.resource == "doctors":
            return self._search_doctors(organization_id, request)
        return self._search_expenses(organization_id, request)

    def _search_appointments(
        self, organization_id: str, request: AdvancedSearchRequest
    ) -> list[dict[str, object]]:
        stmt = select(Appointment).where(Appointment.organization_id == organization_id)
        if request.status is not None:
            stmt = stmt.where(Appointment.status == request.status)
        if request.from_time is not None:
            stmt = stmt.where(Appointment.scheduled_at >= request.from_time)
        if request.to_time is not None:
            stmt = stmt.where(Appointment.scheduled_at <= request.to_time)

        items = list(self.session.scalars(stmt))
        return [
            {
                "id": item.id,
                "patient_id": item.patient_id,
                "doctor_id": item.doctor_id,
                "scheduled_at": item.scheduled_at.isoformat(),
                "status": item.status,
                "anomaly_flag": item.anomaly_flag,
            }
            for item in items
        ]

    def _search_patients(
        self, organization_id: str, request: AdvancedSearchRequest
    ) -> list[dict[str, object]]:
        stmt = select(Patient).where(Patient.organization_id == organization_id)
        if request.keyword is not None:
            stmt = stmt.where(Patient.name.ilike(f"%{request.keyword}%"))
        items = list(self.session.scalars(stmt))
        return [
            {"id": item.id, "patient_number": item.patient_number, "name": item.name}
            for item in items
        ]

    def _search_doctors(
        self, organization_id: str, request: AdvancedSearchRequest
    ) -> list[dict[str, object]]:
        stmt = select(Doctor).where(Doctor.organization_id == organization_id)
        if request.keyword is not None:
            stmt = stmt.where(Doctor.name.ilike(f"%{request.keyword}%"))
        if request.department is not None:
            stmt = stmt.where(Doctor.department == request.department)
        items = list(self.session.scalars(stmt))
        return [
            {
                "id": item.id,
                "doctor_number": item.doctor_number,
                "name": item.name,
                "department": item.department,
            }
            for item in items
        ]

    def _search_expenses(
        self, organization_id: str, request: AdvancedSearchRequest
    ) -> list[dict[str, object]]:
        stmt = select(Expense).where(Expense.organization_id == organization_id)
        if request.min_amount is not None:
            stmt = stmt.where(Expense.amount >= request.min_amount)
        if request.max_amount is not None:
            stmt = stmt.where(Expense.amount <= request.max_amount)
        items = list(self.session.scalars(stmt))
        return [
            {
                "id": item.id,
                "expense_type": item.expense_type,
                "amount": float(item.amount),
                "patient_id": item.patient_id,
                "doctor_id": item.doctor_id,
            }
            for item in items
        ]
