"""FEAT-04: knowledge base schema — domain rename + CSV columns + citation_ref

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-31

ADR-07: milestones.domain and flags.domain change {DLD, Hearing} →
{Speech_Language, Hearing}.
ADR-08: milestones gains citation_ref (unique, indexed) — the human-readable
knowledge-base ID cited by reasoning trails — while id stays UUID v4 (TRD §4).
Extends milestones to the signal_knowledge_base_v2.csv column set
(entry_type, age_min/max_months rename, severity, cross_check_domain,
suggested_follow_up_question, phase_scope, provenance).

flags' domain/grade/status constraints are aligned in the SAME migration
because ADR-07 mandates the flag domain rename before FEAT-05 and ADR-06's
four-state scheme replaces the old three-tier enum ("no_concern" removed —
there is deliberately no "no concern" outcome).

RLS statement (FEAT-04): milestones is a GLOBAL reference table. It carries
no institution_id, so Row-Level Security does not apply — there is no tenant
column to scope on, and by design every institution reads the identical
curated knowledge base. Access control instead comes from grants: FEAT-01
gave the unprivileged app role SELECT-only on milestones, so tenants cannot
mutate the shared reference data; ingestion runs under the privileged
migration role. flags (tenant-scoped, RLS-protected) reference it by
citation_ref string, not FK.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── milestones: domain rename (ADR-07) ────────────────────────────────
    # Widen first: "Speech_Language" is 16 chars, the column is varchar(16) —
    # keep headroom for future domain names.
    op.alter_column(
        "milestones", "domain", existing_type=sa.String(length=16),
        type_=sa.String(length=32), existing_nullable=False,
    )
    op.drop_constraint("ck_milestone_domain", "milestones", type_="check")
    op.create_check_constraint(
        "ck_milestone_domain", "milestones",
        "domain IN ('Speech_Language', 'Hearing')",
    )

    # ── milestones: CSV column set ────────────────────────────────────────
    op.alter_column(
        "milestones", "age_band_min_months", new_column_name="age_min_months"
    )
    op.alter_column(
        "milestones", "age_band_max_months", new_column_name="age_max_months"
    )
    op.add_column(
        "milestones", sa.Column("citation_ref", sa.String(length=32), nullable=False)
    )
    op.add_column(
        "milestones", sa.Column("entry_type", sa.String(length=16), nullable=False)
    )
    op.add_column(
        "milestones", sa.Column("severity", sa.String(length=16), nullable=True)
    )
    op.add_column(
        "milestones",
        sa.Column("cross_check_domain", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "milestones",
        sa.Column("suggested_follow_up_question", sa.Text(), nullable=True),
    )
    op.add_column(
        "milestones", sa.Column("phase_scope", sa.String(length=32), nullable=False)
    )
    op.add_column(
        "milestones", sa.Column("provenance", sa.String(length=120), nullable=False)
    )
    # ADR-08: citation_ref is the loader's upsert key and the clinician-facing
    # identifier — unique AND indexed.
    op.create_index(
        "ix_milestones_citation_ref", "milestones", ["citation_ref"], unique=True
    )
    op.create_index("ix_milestones_domain", "milestones", ["domain"])
    op.create_check_constraint(
        "ck_milestone_entry_type", "milestones",
        "entry_type IN ('milestone', 'red_flag', 'risk_modifier')",
    )
    op.create_check_constraint(
        "ck_milestone_severity", "milestones",
        "severity IS NULL OR severity IN ('HIGH', 'MODERATE', 'MODIFIER')",
    )
    op.create_check_constraint(
        "ck_milestone_severity_consistency", "milestones",
        "(entry_type = 'milestone' AND severity IS NULL) "
        "OR (entry_type IN ('red_flag', 'risk_modifier') AND severity IS NOT NULL)",
    )

    # ── flags: domain rename + ADR-06 grade/status alignment ─────────────
    op.alter_column(
        "flags", "domain", existing_type=sa.String(length=16),
        type_=sa.String(length=32), existing_nullable=False,
    )
    op.drop_constraint("ck_flag_domain", "flags", type_="check")
    op.create_check_constraint(
        "ck_flag_domain", "flags", "domain IN ('Speech_Language', 'Hearing')"
    )
    op.alter_column(
        "flags", "confidence_grade", existing_type=sa.String(length=16),
        type_=sa.String(length=32), existing_nullable=False,
    )
    op.drop_constraint("ck_flag_confidence", "flags", type_="check")
    op.create_check_constraint(
        "ck_flag_confidence", "flags",
        "confidence_grade IN ('high', 'moderate', 'low_monitor', "
        "'insufficient_information')",
    )
    op.drop_constraint("ck_flag_status", "flags", type_="check")
    op.create_check_constraint(
        "ck_flag_status", "flags",
        "status IN ('insufficient_information', 'flagged')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_flag_status", "flags", type_="check")
    op.create_check_constraint(
        "ck_flag_status", "flags",
        "status IN ('insufficient_information', 'flagged', 'no_concern')",
    )
    op.drop_constraint("ck_flag_confidence", "flags", type_="check")
    op.create_check_constraint(
        "ck_flag_confidence", "flags",
        "confidence_grade IN ('high', 'moderate', 'low')",
    )
    op.alter_column(
        "flags", "confidence_grade", existing_type=sa.String(length=32),
        type_=sa.String(length=16), existing_nullable=False,
    )
    op.drop_constraint("ck_flag_domain", "flags", type_="check")
    op.create_check_constraint(
        "ck_flag_domain", "flags", "domain IN ('DLD', 'Hearing')"
    )
    op.alter_column(
        "flags", "domain", existing_type=sa.String(length=32),
        type_=sa.String(length=16), existing_nullable=False,
    )

    op.drop_constraint("ck_milestone_severity_consistency", "milestones", type_="check")
    op.drop_constraint("ck_milestone_severity", "milestones", type_="check")
    op.drop_constraint("ck_milestone_entry_type", "milestones", type_="check")
    op.drop_index("ix_milestones_domain", table_name="milestones")
    op.drop_index("ix_milestones_citation_ref", table_name="milestones")
    for column in (
        "provenance",
        "phase_scope",
        "suggested_follow_up_question",
        "cross_check_domain",
        "severity",
        "entry_type",
        "citation_ref",
    ):
        op.drop_column("milestones", column)
    op.alter_column(
        "milestones", "age_max_months", new_column_name="age_band_max_months"
    )
    op.alter_column(
        "milestones", "age_min_months", new_column_name="age_band_min_months"
    )
    op.drop_constraint("ck_milestone_domain", "milestones", type_="check")
    op.create_check_constraint(
        "ck_milestone_domain", "milestones", "domain IN ('DLD', 'Hearing')"
    )
    op.alter_column(
        "milestones", "domain", existing_type=sa.String(length=32),
        type_=sa.String(length=16), existing_nullable=False,
    )
