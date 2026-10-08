import json
from app.models.knowledge_release import KnowledgeRelease
from app.services.knowledge_release import review_manifest
from app.services.knowledge_storage import store_revisions, eligible_runtime_revisions


def test_draft_import_is_idempotent_and_never_retrievable(db_session):
    manifest = review_manifest()
    release = KnowledgeRelease(release_id=manifest["release_id"], content_sha256=manifest["content_sha256"], status="research_draft", manifest_json=json.dumps(manifest))
    db_session.add(release)
    db_session.flush()
    assert store_revisions(db_session, release.id, manifest) == 88
    assert store_revisions(db_session, release.id, manifest) == 0
    assert eligible_runtime_revisions(db_session, release.id) == []
