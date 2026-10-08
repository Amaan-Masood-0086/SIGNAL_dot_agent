from app.services.knowledge_preview import preview


def test_preview_is_non_clinical_and_returns_followups():
    result = preview("child does not respond to name", 24, 36)
    assert result["preview_only"] is True
    assert result["runtime_enabled"] is False
    assert result["clinical_grade"] is None
    assert result["candidates"]
    assert all(c["follow_up_en"] and c["follow_up_ur_latn"] for c in result["candidates"])


def test_preview_domain_and_age_filter():
    result = preview("hearing", 0, 216, domain="Vision")
    assert all(c["domain"] == "Vision" for c in result["candidates"])
