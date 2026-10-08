from sqlalchemy import select
from test_admin_rbac import client, settings, _admin_token, _institution, _staff, _mint, _auth
from app.models.knowledge_review import KnowledgeReviewNote
from app.models.audit_log import AuditLogEntry


def test_admin_review_catalog_feedback_history_and_conflicts(client, settings, rsa_keypair, db_session):
    token, admin = _admin_token(client, settings, rsa_keypair, db_session)
    headers = _auth(token)
    url = "/api/v1/admin/knowledge-review"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    catalog = response.json()["data"]
    assert len(catalog["items"]) == 88
    assert catalog["runtime_enabled"] is False
    entry = catalog["items"][0]
    assert entry["snapshot"]["entry"]["follow_up_ur_latn"]
    assert entry["snapshot"]["sources"]
    endpoint = f"{url}/{entry['citation_ref']}/notes"
    payload = {"content_sha256": entry["content_sha256"], "expected_note_id": 0, "status": "changes_requested", "reviewer_name": "Synthetic reviewer", "feedback": "Clarify wording", "attachment_name": "review.txt", "attachment_text": "Synthetic feedback attachment"}
    saved = client.post(endpoint, headers=headers, json=payload)
    assert saved.status_code == 201, saved.text
    note = saved.json()["data"]
    assert note["recorded_by"] == str(admin.id)
    assert client.post(endpoint, headers=headers, json=payload).status_code == 409
    assert client.post(endpoint, headers=headers, json={**payload, "expected_note_id": note["id"], "content_sha256": "0" * 64}).status_code == 409
    reviewed = client.post(endpoint, headers=headers, json={**payload, "expected_note_id": note["id"], "status": "reviewed"})
    assert reviewed.status_code == 201
    history = client.get(endpoint, headers=headers).json()["data"]
    assert len(history) == 2 and history[1]["attachment_text"] == payload["attachment_text"]
    refreshed = client.get(url, headers=headers).json()["data"]
    assert refreshed["runtime_enabled"] is False
    assert refreshed["items"][0]["workflow_status"] == "reviewed"
    assert db_session.execute(select(KnowledgeReviewNote)).scalars().all()
    assert len(db_session.execute(select(AuditLogEntry).where(AuditLogEntry.action == "knowledge_review.record")).scalars().all()) == 2


def test_review_dashboard_rejects_caretaker_and_invalid_input(client, settings, rsa_keypair, db_session):
    url = "/api/v1/admin/knowledge-review"
    assert client.get(url).status_code == 401
    inst = _institution(db_session)
    staff = _staff(db_session, institution_id=inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id, role="caretaker")
    assert client.get(url, headers=_auth(token)).status_code == 403
    assert client.post(url + "/V3-SL-M-024-1/notes", headers=_auth(token), json={}).status_code == 403
    token, admin = _admin_token(client, settings, rsa_keypair, db_session)
    headers = _auth(token)
    entry = client.get(url, headers=headers).json()["data"]["items"][0]
    payload = {"content_sha256": entry["content_sha256"], "expected_note_id": 0, "status": "reviewed", "reviewer_name": "Test reviewer", "feedback": "Feedback"}
    endpoint = f"{url}/{entry['citation_ref']}/notes"
    for change in ({"status": "approved"}, {"feedback": " "}, {"attachment_name": "bad.pdf", "attachment_text": "binary"}, {"attachment_name": "../bad.txt", "attachment_text": "text"}, {"runtime_enabled": True}):
        assert client.post(endpoint, headers=headers, json={**payload, **change}).status_code == 422
    admin.is_active = False
    db_session.flush()
    assert client.post(endpoint, headers=headers, json=payload).status_code == 403
