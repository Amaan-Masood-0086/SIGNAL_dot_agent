"""Documented estimated ages; no speculative backfill of old records."""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = depends_on = None


def upgrade():
    op.add_column("children", sa.Column("estimated_age_lower_months", sa.Integer()))
    op.add_column("children", sa.Column("estimated_age_upper_months", sa.Integer()))
    op.add_column("children", sa.Column("age_reference_date", sa.Date()))
    op.add_column("children", sa.Column("prematurity_context", sa.Text()))
    op.create_check_constraint("ck_child_structured_age", "children", """
      (estimated_age_lower_months IS NULL AND estimated_age_upper_months IS NULL AND age_reference_date IS NULL)
      OR (NOT dob_confirmed AND estimated_age_lower_months IS NOT NULL
          AND estimated_age_upper_months IS NOT NULL AND age_reference_date IS NOT NULL
          AND estimated_age_lower_months >= 0
          AND estimated_age_upper_months >= estimated_age_lower_months
          AND estimated_age_upper_months < 216)
    """)


def downgrade():
    op.drop_constraint("ck_child_structured_age", "children", type_="check")
    for column in ("prematurity_context", "age_reference_date", "estimated_age_upper_months", "estimated_age_lower_months"):
        op.drop_column("children", column)
