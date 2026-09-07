"""assigned caretaker — which staff member is responsible for a child

Revision ID: 0007
Revises: 0006

Today every staff member at an institution sees every child there, and no
record says who is actually responsible for any of them. In a place where
staff rotate and no single adult follows one child for years — the exact
structural gap SIGNAL exists to close — "nobody owns the observation" applies
to the roster itself.

SCOPE — read before building on this. This column is RESPONSIBILITY, not
ACCESS. It records and displays who is assigned; it does not change who can
see or do anything. Narrowing visibility to assigned children only is
REMEDIATION_BACKLOG R8, and it is a product decision with real failure modes:
a child whose assigned caretaker is off shift must not become invisible to
the colleague covering for them. Wiring enforcement to this column without
answering that would trade one safety problem for a worse one.

Nullable on purpose: unassigned is a legitimate and common state, not a
defect. A newly registered child has no caretaker yet, and forcing one at
intake would produce a wrong answer rather than an empty one.

ON DELETE SET NULL: a staff row that goes away must not take the child's
record with it, and must not leave a dangling reference either. The child
simply becomes unassigned, which is true and visible.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "children",
        sa.Column("assigned_staff_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_children_assigned_staff_id",
        "children",
        "staff",
        ["assigned_staff_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # "Which children am I responsible for" is the query this exists to
    # answer, so it gets an index rather than a sequential scan per caretaker.
    op.create_index(
        "ix_children_assigned_staff_id", "children", ["assigned_staff_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_children_assigned_staff_id", table_name="children")
    op.drop_constraint(
        "fk_children_assigned_staff_id", "children", type_="foreignkey"
    )
    op.drop_column("children", "assigned_staff_id")
