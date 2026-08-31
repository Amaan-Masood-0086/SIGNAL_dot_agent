"""Flag — confidence-graded developmental concern.

`reasoning_trail` is NOT NULL per ADR-03 — a flag without a cited basis is a
compliance failure, not a data quality issue. The service-layer rejection of
empty trails lives in FlagService (FEAT-05); the schema constraint makes it
structurally impossible to skip the field entirely.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, JSONVariant, TimestampMixin

# ADR-07: domain renamed DLD → Speech_Language (no diagnostic labels).
FLAG_DOMAINS = ("Speech_Language", "Hearing")
# ADR-06 four-state scheme: HIGH | MODERATE | LOW_MONITOR |
# INSUFFICIENT_INFORMATION. There is deliberately no "no concern" outcome.
CONFIDENCE_GRADES = ("high", "moderate", "low_monitor", "insufficient_information")
# ADR-06 sub-rule 1: "no_concern" was removed — INSUFFICIENT_INFORMATION
# is a grade now, not only a status.
FLAG_STATUSES = ("insufficient_information", "flagged")


class Flag(IdMixin, TimestampMixin, Base):
    __tablename__ = "flags"

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
    domain: Mapped[str] = mapped_column(
        Enum(*FLAG_DOMAINS, name="flag_domain", native_enum=False), nullable=False
    )
    confidence_grade: Mapped[str] = mapped_column(
        Enum(*CONFIDENCE_GRADES, name="confidence_grade", native_enum=False),
        nullable=False,
    )
    # ADR-03 + ADR-08: jsonb list citing one or more knowledge-base entries
    # by human-readable citation_ref (e.g. "HEAR-RF-014"), never the UUID.
    # NOT NULL at the schema level; emptiness is additionally rejected in
    # FlagService.
    reasoning_trail: Mapped[list] = mapped_column(JSONVariant, nullable=False)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(*FLAG_STATUSES, name="flag_status", native_enum=False), nullable=False
    )
