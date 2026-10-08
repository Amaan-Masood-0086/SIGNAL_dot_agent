import json
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from app.models.knowledge_release import KnowledgeRelease


def test_release_snapshot_cannot_be_rewritten(db_session):
    row = KnowledgeRelease(release_id="synthetic-test", content_sha256="f" * 64, status="research_draft", manifest_json=json.dumps({"runtime_enabled": False}))
    db_session.add(row)
    db_session.flush()
    for statement in ("UPDATE knowledge_releases SET status='rollback_candidate' WHERE id=:id", "DELETE FROM knowledge_releases WHERE id=:id", "TRUNCATE knowledge_releases CASCADE"):
        with pytest.raises(DBAPIError, match="immutable"):
            with db_session.begin_nested():
                db_session.execute(text(statement), {"id": row.id})
