import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_releases",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("release_id", sa.String(120), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('research_draft','rollback_candidate')", name="ck_knowledge_release_status"),
    )
    op.create_index("ix_knowledge_releases_release_id", "knowledge_releases", ["release_id"])
    op.execute("REVOKE ALL ON knowledge_releases FROM signal_app")
    op.execute("REVOKE ALL ON SEQUENCE knowledge_releases_id_seq FROM signal_app")


def downgrade():
    op.drop_table("knowledge_releases")
