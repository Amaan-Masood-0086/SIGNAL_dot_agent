"""Review identity and fail-closed status; no database or provider calls."""
import json
import shutil

from app.services.knowledge_release import fingerprint, review_manifest
from app.services.knowledge_v3 import DEFAULT_V3_DIR


def test_manifest_is_repeatable_and_never_claims_approval():
    manifest = review_manifest()
    assert manifest == review_manifest()
    assert manifest["runtime_enabled"] is False
    assert manifest["ready_for_activation"] is False
    assert len(manifest["entries"]) == 88
    assert len(manifest["blockers"]["clinical_review"]) == 88
    assert len(manifest["blockers"]["legacy_specific_review"]) == 10
    assert manifest["blockers"]["clinical_grading_decision"] == ["R14"]


def test_fingerprint_ignores_dictionary_order_but_not_wording():
    assert fingerprint({"a": 1, "b": 2}) == fingerprint({"b": 2, "a": 1})
    assert fingerprint({"text": "before"}) != fingerprint({"text": "after"})


def test_source_changes_invalidate_affected_entry_review_identity(tmp_path):
    before = review_manifest()
    for filename in ("knowledge_base.json", "sources.json", "legacy_mapping.json"):
        shutil.copyfile(DEFAULT_V3_DIR / filename, tmp_path / filename)
    path = tmp_path / "sources.json"
    sources = json.loads(path.read_text(encoding="utf-8-sig"))
    changed_source = sources[0]["source_id"]
    sources[0]["limitations"] += " Changed review scope."
    path.write_text(json.dumps(sources), encoding="utf-8")
    after = review_manifest(tmp_path)
    assert before["content_sha256"] != after["content_sha256"]
    affected = 0
    for old, new in zip(before["entries"], after["entries"], strict=True):
        if changed_source in old["snapshot"]["entry"]["source_ids"]:
            affected += 1
            assert old["content_sha256"] != new["content_sha256"]
        else:
            assert old["content_sha256"] == new["content_sha256"]
    assert affected > 0
