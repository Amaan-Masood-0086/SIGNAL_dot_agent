"""pgvector: optional semantic-retrieval embeddings on milestones (ADR-11)."""
import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = depends_on = None


def upgrade():
    # Fails loudly if the server lacks the pgvector package — by design: a
    # silently missing extension would only surface later, mid-screening.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE milestones ADD COLUMN embedding vector(1024)")
    op.add_column("milestones", sa.Column("embedding_model", sa.String(120)))
    op.add_column("milestones", sa.Column("embedding_hash", sa.String(64)))
    # No ANN index on purpose: ~100 rows, an exact scan is exact and faster.


def downgrade():
    op.drop_column("milestones", "embedding_hash")
    op.drop_column("milestones", "embedding_model")
    op.execute("ALTER TABLE milestones DROP COLUMN embedding")
