"""initial schema + role-level RLS (FEAT-01)

Revision ID: 0001
Revises:
Create Date: 2026-08-29

Creates the full TRD §3 data model and enforces Row-Level Security at the
Postgres ROLE level (locked NextaSol principle / THREAT_MODEL §1): the
application connects as the unprivileged `signal_app` role and can only see
rows whose institution_id matches the `app.institution_id` session setting —
fail-closed when the setting is absent. `audit_log` is append-only:
UPDATE/DELETE are revoked from the app role.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Institution-scoped tables: RLS policy on institution_id.
TENANT_TABLES = (
    "staff",
    "children",
    "sessions",
    "observations",
    "flags",
    "referrals",
    "safeguarding_escalations",
)

APP_ROLE = "signal_app"


def upgrade() -> None:
    # ── institutions (tenant root) ────────────────────────────────────────
    op.create_table(
        "institutions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── staff ─────────────────────────────────────────────────────────────
    op.create_table(
        "staff",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint("role IN ('caretaker', 'admin')", name="ck_staff_role"),
    )
    op.create_index("ix_staff_institution_id", "staff", ["institution_id"])

    # ── children (ADR-02: dual confirmed/estimated age) ───────────────────
    op.create_table(
        "children",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("intake_date", sa.Date(), nullable=False),
        sa.Column("dob_confirmed", sa.Boolean(), nullable=False),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("estimated_age_range", sa.String(length=50), nullable=True),
        sa.Column("estimated_age_note", sa.Text(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )
    op.create_index("ix_children_institution_id", "children", ["institution_id"])

    # ── sessions ──────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="in_progress"),
        sa.Column("mode", sa.String(length=8), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"]),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed', 'abandoned')", name="ck_session_status"
        ),
        sa.CheckConstraint("mode IN ('voice', 'text')", name="ck_session_mode"),
    )
    op.create_index("ix_sessions_institution_id", "sessions", ["institution_id"])
    op.create_index("ix_sessions_child_id", "sessions", ["child_id"])
    op.create_index("ix_sessions_staff_id", "sessions", ["staff_id"])

    # ── observations ──────────────────────────────────────────────────────
    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("extracted_signals", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
    )
    op.create_index("ix_observations_institution_id", "observations", ["institution_id"])
    op.create_index("ix_observations_session_id", "observations", ["session_id"])

    # ── milestones (global knowledge base — NOT tenant-scoped) ────────────
    op.create_table(
        "milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(length=16), nullable=False),
        sa.Column("age_band_min_months", sa.Integer(), nullable=False),
        sa.Column("age_band_max_months", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("domain IN ('DLD', 'Hearing')", name="ck_milestone_domain"),
    )

    # ── flags (ADR-03: reasoning_trail NOT NULL) ──────────────────────────
    op.create_table(
        "flags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(length=16), nullable=False),
        sa.Column("confidence_grade", sa.String(length=16), nullable=False),
        sa.Column(
            "reasoning_trail",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"]),
        sa.CheckConstraint("domain IN ('DLD', 'Hearing')", name="ck_flag_domain"),
        sa.CheckConstraint(
            "confidence_grade IN ('high', 'moderate', 'low')", name="ck_flag_confidence"
        ),
        sa.CheckConstraint(
            "status IN ('insufficient_information', 'flagged', 'no_concern')",
            name="ck_flag_status",
        ),
    )
    op.create_index("ix_flags_institution_id", "flags", ["institution_id"])
    op.create_index("ix_flags_session_id", "flags", ["session_id"])
    op.create_index("ix_flags_child_id", "flags", ["child_id"])

    # ── referrals ─────────────────────────────────────────────────────────
    op.create_table(
        "referrals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("flag_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("responsible_person", sa.String(length=200), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("caretaker_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["flag_id"], ["flags.id"]),
        sa.CheckConstraint(
            "status IN ('referred', 'pending_capacity', 'closed')", name="ck_referral_status"
        ),
    )
    op.create_index("ix_referrals_institution_id", "referrals", ["institution_id"])
    op.create_index("ix_referrals_flag_id", "referrals", ["flag_id"])

    # ── safeguarding_escalations (deliberately separate from flags) ──────
    op.create_table(
        "safeguarding_escalations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("signal_description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"]),
        sa.CheckConstraint(
            "status IN ('open', 'under_review', 'closed')", name="ck_escalation_status"
        ),
    )
    op.create_index(
        "ix_safeguarding_escalations_institution_id",
        "safeguarding_escalations",
        ["institution_id"],
    )
    op.create_index(
        "ix_safeguarding_escalations_session_id", "safeguarding_escalations", ["session_id"]
    )
    op.create_index(
        "ix_safeguarding_escalations_child_id", "safeguarding_escalations", ["child_id"]
    )

    # ── audit_log (append-only, hash-chained) ─────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("institution_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=60), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("hash_prev", sa.String(length=64), nullable=False),
        sa.Column("hash_self", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sequence"),
    )
    op.create_index("ix_audit_log_sequence", "audit_log", ["sequence"])

    # ── Application role + Row-Level Security ─────────────────────────────
    # SECURITY: the dev password below is for local development only. Any
    # non-local deployment MUST rotate it via environment-managed secrets.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD 'signal_app';
            END IF;
        END
        $$;
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON institutions, {', '.join(TENANT_TABLES)} TO {APP_ROLE}"
    )
    op.execute(f"GRANT SELECT ON milestones TO {APP_ROLE}")
    # Append-only: INSERT + SELECT only — UPDATE/DELETE stay revoked.
    op.execute(f"GRANT SELECT, INSERT ON audit_log TO {APP_ROLE}")
    op.execute(f"REVOKE UPDATE, DELETE ON audit_log FROM {APP_ROLE}, PUBLIC")

    # RLS on the tenant root: a connection only sees its own institution.
    op.execute("ALTER TABLE institutions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE institutions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY institution_isolation ON institutions
            USING (id = current_setting('app.institution_id', true)::uuid)
            WITH CHECK (id = current_setting('app.institution_id', true)::uuid)
        """
    )

    # RLS on every institution-scoped table — fail-closed when the setting
    # is absent (NULL never compares equal).
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY institution_isolation ON {table}
                USING (institution_id = current_setting('app.institution_id', true)::uuid)
                WITH CHECK (institution_id = current_setting('app.institution_id', true)::uuid)
            """
        )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS institution_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS institution_isolation ON institutions")
    op.execute("ALTER TABLE institutions DISABLE ROW LEVEL SECURITY")
    for table in (
        "audit_log",
        "safeguarding_escalations",
        "referrals",
        "flags",
        "milestones",
        "observations",
        "sessions",
        "children",
        "staff",
        "institutions",
    ):
        op.drop_table(table)
    op.execute(f"REVOKE ALL ON SCHEMA public FROM {APP_ROLE}")
