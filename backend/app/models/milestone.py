"""Milestone — curated knowledge base (Speech_Language + Hearing indicators).

Global reference table — NOT institution-scoped, therefore no RLS (no
institution_id column exists to scope on). FEAT-01 granted the app role
SELECT-only; ingestion runs under the privileged migration role.

Columns follow signal_knowledge_base_v2.csv (FEAT-04). Dual identity per
ADR-08: UUID v4 primary key (TRD §4 MUST #8) plus the human-readable
`citation_ref` (SL-RF-009, HEAR-RF-014) — unique and indexed; reasoning
trails cite citation_ref, never the UUID. Domain renamed DLD →
Speech_Language per ADR-07 (the system never emits a diagnostic label).
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin

# ADR-07: "DLD" is scientifically indefensible for this population and
# contradicts the non-diagnostic positioning — renamed everywhere.
MILESTONE_DOMAINS = ("Speech_Language", "Hearing")
ENTRY_TYPES = ("milestone", "red_flag", "risk_modifier")
SEVERITIES = ("HIGH", "MODERATE", "MODIFIER")


class Milestone(IdMixin, TimestampMixin, Base):
    __tablename__ = "milestones"
    __table_args__ = (
        # Red flags and risk modifiers carry a graded severity; plain
        # milestones do not (NULL severity).
        CheckConstraint(
            "(entry_type = 'milestone' AND severity IS NULL) "
            "OR (entry_type IN ('red_flag', 'risk_modifier') "
            "AND severity IS NOT NULL)",
            name="ck_milestone_severity_consistency",
        ),
    )

    # ADR-08: stable human-readable identifier; the loader upserts on it.
    citation_ref: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    entry_type: Mapped[str] = mapped_column(
        Enum(*ENTRY_TYPES, name="entry_type", native_enum=False), nullable=False
    )
    domain: Mapped[str] = mapped_column(
        Enum(*MILESTONE_DOMAINS, name="milestone_domain", native_enum=False),
        nullable=False,
    )
    age_min_months: Mapped[int] = mapped_column(Integer, nullable=False)
    age_max_months: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(
        Enum(*SEVERITIES, name="milestone_severity", native_enum=False),
        nullable=True,
    )
    # ADR-05 cross-domain differential: the companion domain a clinician
    # must also consider for this entry (e.g. a speech milestone whose
    # absence may be hearing-driven).
    cross_check_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_follow_up_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Provenance is mandatory — the reasoning trail is only as credible as the
    # underlying data's source (ai-agent-development.md RAG rules).
    source: Mapped[str] = mapped_column(String(300), nullable=False)
    # "in scope" / "in scope (any age)" / "PHASE 2 (6+)" — PHASE 2 rows are
    # stored but excluded from every pipeline query (FEAT-04 rule 5).
    phase_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    provenance: Mapped[str] = mapped_column(String(120), nullable=False)
