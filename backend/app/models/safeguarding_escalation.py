"""Safeguarding escalation — DELIBERATELY separate from `flags`.

TRD business rule #6: abuse/neglect-pattern signals are never written to or
merged with the flags table — separate table, separate service, no shared
write path. Access stays deliberately conservative (THREAT_MODEL RBAC note:
no full read access until mandatory-reporting design lands, Open Item #6).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin

ESCALATION_STATUSES = ("open", "under_review", "closed")


class SafeguardingEscalation(IdMixin, TimestampMixin, Base):
    __tablename__ = "safeguarding_escalations"

    # Denormalized tenant column for RLS (masterDataSDLC §3.2).
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("sessions.id"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("children.id"), nullable=False, index=True
    )
    signal_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*ESCALATION_STATUSES, name="escalation_status", native_enum=False),
        nullable=False,
        default="open",
    )
