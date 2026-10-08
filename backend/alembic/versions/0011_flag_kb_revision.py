import sqlalchemy as sa
from alembic import op
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("flags", sa.Column("kb_release_id", sa.String(120), nullable=False, server_default="v2-active"))
    op.add_column("flags", sa.Column("kb_entry_revision", sa.String(64), nullable=True))
def downgrade():
    op.drop_column("flags", "kb_entry_revision")
    op.drop_column("flags", "kb_release_id")
