"""RBAC + Admin Panel: staff soft-delete flag + usage_log ledger

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-31

staff gains is_active for account deactivation — a SOFT delete: staff rows
are never hard-deleted (health-adjacent data with an audit trail). Default
TRUE keeps every existing account active.

usage_log is the cost-visibility ledger backing RISK_REGISTER's cost-DoS
mitigation: every paid STT/LLM call is recorded with staff + institution
attribution and a best-effort estimated cost. Like audit_log it is
append-only for the app role (SELECT + INSERT; UPDATE/DELETE revoked) and
tenant-scoped via RLS — usage rows never cross the institution boundary for
non-admin roles; the admin cross-institution usage view is an application-
layer SYSTEM-LEVEL bypass restricted to the explicit admin endpoints
(THREAT_MODEL §2 RBAC matrix).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "signal_app"


def upgrade() -> None:
    # ── staff: soft-delete flag ───────────────────────────────────────────
    op.add_column(
        "staff",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # ── usage_log: paid-call ledger ───────────────────────────────────────
    op.create_table(
        "usage_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=8), nullable=False),
        sa.Column("call_type", sa.String(length=40), nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        # Best-effort cost estimate; NULL until a provider cost model exists.
        sa.Column("estimated_cost", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.CheckConstraint("provider IN ('stt', 'llm')", name="ck_usage_provider"),
    )
    op.create_index("ix_usage_log_staff_id", "usage_log", ["staff_id"])
    op.create_index("ix_usage_log_institution_id", "usage_log", ["institution_id"])
    op.create_index("ix_usage_log_timestamp", "usage_log", ["timestamp"])

    # ── grants + RLS (same pattern as FEAT-01 migration 0001) ─────────────
    # Append-only ledger: INSERT + SELECT only for the unprivileged app role.
    op.execute(f"GRANT SELECT, INSERT ON usage_log TO {APP_ROLE}")
    op.execute(f"REVOKE UPDATE, DELETE ON usage_log FROM {APP_ROLE}, PUBLIC")

    op.execute("ALTER TABLE usage_log ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE usage_log FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY institution_isolation ON usage_log
            USING (institution_id = current_setting('app.institution_id', true)::uuid)
            WITH CHECK (institution_id = current_setting('app.institution_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS institution_isolation ON usage_log")
    op.execute("ALTER TABLE usage_log DISABLE ROW LEVEL SECURITY")
    op.execute(f"REVOKE ALL ON usage_log FROM {APP_ROLE}")
    op.drop_index("ix_usage_log_timestamp", table_name="usage_log")
    op.drop_index("ix_usage_log_institution_id", table_name="usage_log")
    op.drop_index("ix_usage_log_staff_id", table_name="usage_log")
    op.drop_table("usage_log")
    op.drop_column("staff", "is_active")
