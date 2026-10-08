"""Dormant V3 reference storage; no live activation or milestone migration."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0014"
down_revision = "0013"
branch_labels = depends_on = None


def upgrade():
    op.create_table("knowledge_revisions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("release_snapshot_id", sa.BigInteger(), sa.ForeignKey("knowledge_releases.id"), nullable=False),
        sa.Column("citation_ref", sa.String(80), nullable=False),
        sa.Column("revision", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("snapshot", JSONB(), nullable=False),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="needs_clinical_review"),
        sa.Column("runtime_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.UniqueConstraint("release_snapshot_id", "citation_ref", "revision", name="uq_knowledge_revision"),
        sa.CheckConstraint("domain IN ('Speech_Language','Hearing','Vision','Motor','Social_Communication','Attention','Attachment','Context','Safety','Safeguarding')", name="ck_revision_domain"),
        sa.CheckConstraint("review_status IN ('needs_clinical_review','approved','excluded')", name="ck_revision_review"),
        sa.CheckConstraint("NOT runtime_enabled OR review_status = 'approved'", name="ck_revision_activation"),
    )
    op.execute("REVOKE ALL ON knowledge_revisions FROM signal_app")
    op.execute("REVOKE ALL ON SEQUENCE knowledge_revisions_id_seq FROM signal_app")
    op.execute("""CREATE FUNCTION signal_protect_revision() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Knowledge revisions cannot be deleted'; END IF;
      IF NEW.snapshot IS DISTINCT FROM OLD.snapshot OR NEW.revision IS DISTINCT FROM OLD.revision
         OR NEW.citation_ref IS DISTINCT FROM OLD.citation_ref OR NEW.domain IS DISTINCT FROM OLD.domain
         OR NEW.release_snapshot_id IS DISTINCT FROM OLD.release_snapshot_id THEN
        RAISE EXCEPTION 'Knowledge revision content is immutable';
      END IF;
      RETURN NEW;
    END $$""")
    op.execute("CREATE TRIGGER protect_knowledge_revision BEFORE UPDATE OR DELETE ON knowledge_revisions FOR EACH ROW EXECUTE FUNCTION signal_protect_revision()")


def downgrade():
    op.drop_table("knowledge_revisions")
    op.execute("DROP FUNCTION signal_protect_revision()")
