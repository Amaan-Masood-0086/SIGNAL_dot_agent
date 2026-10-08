"""Enforce release immutability in PostgreSQL, including privileged app writes."""
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE FUNCTION signal_reject_release_mutation() RETURNS trigger
    LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'Knowledge release snapshots are immutable';
    END $$;
    """)
    op.execute("""
    CREATE TRIGGER knowledge_release_immutable
    BEFORE UPDATE OR DELETE ON knowledge_releases
    FOR EACH ROW EXECUTE FUNCTION signal_reject_release_mutation();
    """)
    op.execute("""
    CREATE TRIGGER knowledge_release_no_truncate
    BEFORE TRUNCATE ON knowledge_releases
    FOR EACH STATEMENT EXECUTE FUNCTION signal_reject_release_mutation();
    """)


def downgrade():
    op.execute("DROP TRIGGER knowledge_release_no_truncate ON knowledge_releases")
    op.execute("DROP TRIGGER knowledge_release_immutable ON knowledge_releases")
    op.execute("DROP FUNCTION signal_reject_release_mutation()")
