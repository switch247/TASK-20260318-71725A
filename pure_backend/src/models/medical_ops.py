from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.common import TimestampMixin, UuidPrimaryKeyMixin


class Patient(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    patient_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)


class Doctor(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "doctors"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    doctor_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(255), nullable=False, index=True)


class Appointment(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "appointments"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id", ondelete="CASCADE"), index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    anomaly_flag: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)


class Expense(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "expenses"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    patient_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    doctor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    expense_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
