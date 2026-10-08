import sqlalchemy as sa
from alembic import op
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("referrals", sa.Column("outcome", sa.String(32), nullable=False, server_default="not_yet_assessed"))
    op.add_column("referrals", sa.Column("clinician_note", sa.String(2000), nullable=True))
    op.create_check_constraint("ck_referral_outcome", "referrals", "outcome IN ('confirmed','ruled_out','lost_to_followup','not_yet_assessed')")
def downgrade():
    op.drop_constraint("ck_referral_outcome", "referrals", type_="check")
    op.drop_column("referrals", "clinician_note")
    op.drop_column("referrals", "outcome")
