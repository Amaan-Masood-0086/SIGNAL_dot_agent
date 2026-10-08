"""Admin-only KB review notes; no runtime KB or clinical activation changes."""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("knowledge_review_notes",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("citation_ref", sa.String(80), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reviewer_name", sa.String(200), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("attachment_name", sa.String(200)),
        sa.Column("attachment_text", sa.Text()),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'changes_requested', 'reviewed')", name="ck_kb_review_status"),
    )
    op.create_index("ix_knowledge_review_notes_citation_ref", "knowledge_review_notes", ["citation_ref"])
    # Global reference-review workflow: no caretaker/tenant grants. Access
    # is exclusively through the DB-verified system-admin dependency.
    op.execute("REVOKE ALL ON knowledge_review_notes FROM signal_app")
    op.execute("REVOKE ALL ON SEQUENCE knowledge_review_notes_id_seq FROM signal_app")


def downgrade():
    op.drop_table("knowledge_review_notes")
