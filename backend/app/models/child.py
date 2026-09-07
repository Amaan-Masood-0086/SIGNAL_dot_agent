"""Child — dual confirmed/estimated age representation per ADR-02."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin


class Child(IdMixin, TimestampMixin, Base):
    __tablename__ = "children"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    intake_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    # ADR-02: dual representation, never a single assumed DOB.
    # dob_confirmed=False → dob stays NULL, estimated_age_range is populated,
    # and every age-dependent check downgrades confidence one tier.
    dob_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    dob: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    estimated_age_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_age_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Archive, not delete (migration 0006). A mistaken registration and a
    # child who has left the institution both leave the roster, but neither
    # destroys the clinical record — retention for children's health data is
    # a policy decision this column deliberately leaves open. A reason is
    # required whenever archived_at is set (DB check constraint).
    archived_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Which staff member is responsible for this child (migration 0007).
    #
    # RESPONSIBILITY, not ACCESS. Nothing reads this to decide what a
    # caretaker may see — every institution member still sees every child.
    # Narrowing that is REMEDIATION_BACKLOG R8 and carries a real question
    # this column does not answer: a child whose assigned caretaker is off
    # shift must not become invisible to whoever is covering.
    #
    # Nullable because unassigned is a legitimate state, not a defect.
    assigned_staff_id: Mapped[uuid.UUID | None] = mapped_column(
        UuidType,
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
