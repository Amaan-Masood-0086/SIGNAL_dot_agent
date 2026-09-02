"""child archive — reversible removal from the active roster

Revision ID: 0006
Revises: 0005

A caretaker needs a way to take a child off the roster: a duplicate or
mistyped registration, or a child who has left the institution. Until now
there was no path at all, and the roster could only grow.

This is deliberately an ARCHIVE, not a delete. Two very different situations
look the same in the UI and must not be treated the same in the data:

  - a mistaken registration  → the row should stop appearing
  - a child who has left     → the clinical record must survive, because
                               retention periods for children's health data
                               are long and are not this feature's decision
                               to make

Archiving satisfies both without destroying anything, and leaves the actual
retention policy free to be decided later and applied to archived rows. No
DELETE grant is added: `signal_app` still cannot remove a child row, and
`flags` / `sessions` / `observations` keep their foreign keys intact.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "children",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "children",
        sa.Column("archived_reason", sa.String(length=200), nullable=True),
    )
    # A reason is mandatory whenever a row is archived: "why is this child no
    # longer on the roster" is the question an auditor asks, and a nullable
    # free-for-all would answer it with silence.
    op.create_check_constraint(
        "ck_child_archive_reason",
        "children",
        "(archived_at IS NULL AND archived_reason IS NULL) "
        "OR (archived_at IS NOT NULL AND archived_reason IS NOT NULL)",
    )
    # The roster query filters on this constantly; the flag column is low
    # cardinality, so index only the active rows.
    op.create_index(
        "ix_children_active",
        "children",
        ["institution_id"],
        postgresql_where=sa.text("archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_children_active", table_name="children")
    op.drop_constraint("ck_child_archive_reason", "children", type_="check")
    op.drop_column("children", "archived_reason")
    op.drop_column("children", "archived_at")
