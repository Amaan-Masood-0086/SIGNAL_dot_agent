from app.services.knowledge_release import compare_manifests


def test_content_diff_is_explicit():
    left = {"release_id": "a", "entries": [{"citation_ref": "x", "content_sha256": "1"}, {"citation_ref": "y", "content_sha256": "2"}]}
    right = {"release_id": "b", "entries": [{"citation_ref": "x", "content_sha256": "3"}, {"citation_ref": "z", "content_sha256": "4"}]}
    assert compare_manifests(left, right) == {"added": ["z"], "removed": ["y"], "changed": ["x"], "from_release": "a", "to_release": "b"}
