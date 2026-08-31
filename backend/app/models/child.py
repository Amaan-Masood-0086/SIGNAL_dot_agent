"""Child — dual confirmed/estimated age representation per ADR-02."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
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
