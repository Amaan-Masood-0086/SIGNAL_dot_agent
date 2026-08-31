"""Referral — loop-closing record (feature #9).

`caretaker_confirmed` is the persistence gate for TRD business rule #3: a
referral can never auto-populate without an explicit caretaker confirmation
step. ReferralService.create_referral() (FEAT-10) rejects confirmed=False.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin

REFERRAL_STATUSES = ("referred", "pending_capacity", "closed")


class Referral(IdMixin, TimestampMixin, Base):
    __tablename__ = "referrals"

    # Denormalized tenant column for RLS (masterDataSDLC §3.2).
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    flag_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("flags.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(*REFERRAL_STATUSES, name="referral_status", native_enum=False),
        nullable=False,
    )
    responsible_person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    review_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Business rule #3 gate — see ReferralService (FEAT-10).
    caretaker_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
