"""FEAT-03 — Voice + Text Input Layer.

Acceptance criteria under test:
- BOTH input modes (voice-transcript and typed text) produce the same
  downstream observation format — same endpoint, same schema.
- Text fallback works with zero STT dependency: the STT seam degrades to a
  clean 503 when unconfigured and never blocks the text path.

TRD §3: `sessions` (mode ∈ {voice, text}, status lifecycle) and
`observations` (turn_number, raw_input — server-assigned). Backend coding
contracts: every write audit-chained, every query institution-scoped,
server-generated values never from the request body, list endpoints paginate.

All tests run against real PostgreSQL (conftest.py::pg_engine).
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def settings(rsa_keypair):
    private_pem, public_pem = rsa_keypair
    from app.core.config import Settings

    return Settings(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY=private_pem.decode(),
        JWT_PUBLIC_KEY=public_pem.decode(),
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
    )


@pytest.fixture()
def client(settings, db_session):
    from app.api.deps import get_db, get_tenant_db
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app(settings)
    # Endpoint DB session is the transaction-isolated test session.
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def _mint_token(settings, rsa_keypair, *, institution_id, staff_id=None, role="caretaker"):
    private_pem, _ = rsa_keypair
    from app.core import security

    staff_id = staff_id or uuid.uuid4()
    token = security.create_access_token(
        staff_id=str(staff_id),
        institution_id=str(institution_id),
        role=role,
        private_key_pem=private_pem,
        expires_minutes=15,
        settings=settings,
    )
    return token, staff_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_institution(db_session, *, name="Synthetic Institution"):
    from app.models.institution import Institution

    inst = Institution(name=name, is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    return inst


def _seed_staff(db_session, *, institution_id, staff_id, email=None):
    from app.models.staff import Staff

    staff = Staff(
        id=staff_id,
        institution_id=institution_id,
        email=email or f"{staff_id.hex}@signal.example",
        hashed_password="unused-in-phase-1-stub",
        role="caretaker",
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return staff


def _seed_child(db_session, *, institution_id, name="Seeded Child"):
    from app.models.child import Child

    child = Child(
        institution_id=institution_id,
        name=name,
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=False,
        estimated_age_range="24-30 months",
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


def _start_session(client, settings, rsa_keypair, db_session, *, mode="text"):
    """Seed tenant + staff + child, then open a session. Returns (session, token)."""
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)
    child = _seed_child(db_session, institution_id=inst.id)
    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child.id), "mode": mode},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"], token


# ── Session lifecycle ───────────────────────────────────────────────────────


def test_create_session_for_own_child_201(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)
    child = _seed_child(db_session, institution_id=inst.id)

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child.id), "mode": "text"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["child_id"] == str(child.id)
    assert data["staff_id"] == str(staff_id)
    assert data["mode"] == "text"
    assert data["status"] == "in_progress"
    # Server-generated timestamps never come from the client (MUST #5).
    assert data["started_at"]


def test_create_session_voice_mode_persisted(client, settings, rsa_keypair, db_session):
    session_data, _ = _start_session(client, settings, rsa_keypair, db_session, mode="voice")
    assert session_data["mode"] == "voice"


def test_create_session_invalid_mode_rejected_422(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)
    child = _seed_child(db_session, institution_id=inst.id)

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child.id), "mode": "audio"},
    )
    assert resp.status_code == 422


def test_create_session_cross_institution_child_403(client, settings, rsa_keypair, db_session):
    """IDOR T1: opening a session on another institution's child is forbidden."""
    inst_b = _seed_institution(db_session, name="Institution B")
    child_b = _seed_child(db_session, institution_id=inst_b.id)
    inst_a = _seed_institution(db_session, name="Institution A")
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst_a.id)
    _seed_staff(db_session, institution_id=inst_a.id, staff_id=staff_id)

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child_b.id), "mode": "text"},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert "detail" in body and "data" not in body


def test_create_session_unknown_child_403_not_404(client, settings, rsa_keypair, db_session):
    """Uniform 403 — existence must never leak across the tenant boundary."""
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(uuid.uuid4()), "mode": "text"},
    )
    assert resp.status_code == 403


def test_create_session_unverified_staff_identity_403(client, settings, rsa_keypair, db_session):
    """Fail closed: a JWT staff identity with no staff row is not recognized."""
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)  # no staff row
    child = _seed_child(db_session, institution_id=inst.id)

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child.id), "mode": "text"},
    )
    assert resp.status_code == 403


def test_sessions_require_auth_401(client):
    assert client.post("/api/v1/sessions", json={"child_id": str(uuid.uuid4())}).status_code == 401
    assert client.get(f"/api/v1/sessions/{uuid.uuid4()}").status_code == 401


def test_create_session_audit_logged(client, settings, rsa_keypair, db_session):
    session_data, _ = _start_session(client, settings, rsa_keypair, db_session)

    from app.models.audit_log import AuditLogEntry

    entry = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_id == session_data["id"])
        .one()
    )
    assert entry.action == "session.create"
    assert entry.resource_type == "session"
    assert entry.actor_id == uuid.UUID(session_data["staff_id"])


def test_get_session_scoped_by_institution(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)

    resp = client.get(f"/api/v1/sessions/{session_data['id']}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == session_data["id"]

    # Another institution's staff cannot read it.
    other_inst = _seed_institution(db_session, name="Other")
    foreign_token, foreign_staff = _mint_token(settings, rsa_keypair, institution_id=other_inst.id)
    _seed_staff(db_session, institution_id=other_inst.id, staff_id=foreign_staff)
    resp = client.get(f"/api/v1/sessions/{session_data['id']}", headers=_auth(foreign_token))
    assert resp.status_code == 403


def test_complete_session_200_and_audited(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)

    resp = client.post(f"/api/v1/sessions/{session_data['id']}/complete", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"

    from app.models.audit_log import AuditLogEntry

    complete_entries = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.action == "session.complete")
        .all()
    )
    assert len(complete_entries) == 1
    assert complete_entries[0].resource_id == session_data["id"]


# ── Observations: identical format for voice and text ───────────────────────


def test_add_observation_text_mode_201(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session, mode="text")

    resp = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "bacha do saal ka hai, abhi bolna shuru nahi kiya"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["session_id"] == session_data["id"]
    assert data["turn_number"] == 1
    assert data["raw_input"] == "bacha do saal ka hai, abhi bolna shuru nahi kiya"


def test_voice_and_text_modes_produce_identical_observation_format(
    client, settings, rsa_keypair, db_session
):
    """FEAT-03 acceptance: the downstream observation shape is mode-agnostic.

    Voice input arrives as a transcript through the SAME endpoint as typed
    text — the observation row knows no difference.
    """
    text_session, token = _start_session(client, settings, rsa_keypair, db_session, mode="text")
    text_resp = client.post(
        f"/api/v1/sessions/{text_session['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "typed turn"},
    )
    assert text_resp.status_code == 201

    voice_session, voice_token = _start_session(
        client, settings, rsa_keypair, db_session, mode="voice"
    )
    voice_resp = client.post(
        f"/api/v1/sessions/{voice_session['id']}/observations",
        headers=_auth(voice_token),
        json={"raw_input": "transcribed turn"},
    )
    assert voice_resp.status_code == 201

    text_obs = text_resp.json()["data"]
    voice_obs = voice_resp.json()["data"]
    assert set(text_obs.keys()) == set(voice_obs.keys())
    for key in ("session_id", "turn_number", "raw_input", "extracted_signals", "created_at"):
        assert key in voice_obs


def test_turn_numbers_increment_server_side(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)

    first = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "turn one"},
    )
    second = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "turn two"},
    )
    assert first.json()["data"]["turn_number"] == 1
    assert second.json()["data"]["turn_number"] == 2


def test_turn_number_never_client_supplied(client, settings, rsa_keypair, db_session):
    """Server-generated values MUST NOT come from the request body (MUST #5)."""
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)

    resp = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "spoofed turn", "turn_number": 99},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["turn_number"] == 1


def test_observation_blank_or_oversized_rejected_422(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)
    url = f"/api/v1/sessions/{session_data['id']}/observations"

    assert client.post(url, headers=_auth(token), json={"raw_input": "   "}).status_code == 422
    assert client.post(url, headers=_auth(token), json={"raw_input": "x" * 10_001}).status_code == 422


def test_observation_cross_institution_403(client, settings, rsa_keypair, db_session):
    """IDOR T1: observations are only writable/readable inside the session's tenant."""
    session_data, _ = _start_session(client, settings, rsa_keypair, db_session)
    other_inst = _seed_institution(db_session, name="Other")
    foreign_token, foreign_staff = _mint_token(settings, rsa_keypair, institution_id=other_inst.id)
    _seed_staff(db_session, institution_id=other_inst.id, staff_id=foreign_staff)

    resp = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(foreign_token),
        json={"raw_input": "cross-tenant turn"},
    )
    assert resp.status_code == 403
    assert "data" not in resp.json()


def test_observation_on_completed_session_409(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)
    complete = client.post(
        f"/api/v1/sessions/{session_data['id']}/complete", headers=_auth(token)
    )
    assert complete.status_code == 200

    resp = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "too late"},
    )
    assert resp.status_code == 409


def test_observation_requires_auth_401(client):
    assert (
        client.post(f"/api/v1/sessions/{uuid.uuid4()}/observations", json={"raw_input": "x"}).status_code
        == 401
    )


def test_observation_creation_audit_logged(client, settings, rsa_keypair, db_session):
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)
    resp = client.post(
        f"/api/v1/sessions/{session_data['id']}/observations",
        headers=_auth(token),
        json={"raw_input": "audited turn"},
    )
    observation_id = resp.json()["data"]["id"]

    from app.models.audit_log import AuditLogEntry

    entry = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_id == observation_id)
        .one()
    )
    assert entry.action == "observation.create"
    assert entry.resource_type == "observation"
    assert entry.actor_id == uuid.UUID(session_data["staff_id"])


def test_list_observations_paginated(client, settings, rsa_keypair, db_session):
    """List endpoints MUST paginate; page_size MUST NOT exceed 100."""
    session_data, token = _start_session(client, settings, rsa_keypair, db_session)
    url = f"/api/v1/sessions/{session_data['id']}/observations"
    for i in range(3):
        assert client.post(url, headers=_auth(token), json={"raw_input": f"turn {i}"}).status_code == 201

    page = client.get(url, headers=_auth(token), params={"page": 1, "page_size": 2})
    assert page.status_code == 200
    body = page.json()["data"]
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert [item["turn_number"] for item in body["items"]] == [1, 2]

    assert client.get(url, headers=_auth(token), params={"page_size": 101}).status_code == 422


# ── STT seam: backend transcribe endpoint (voice mode only) ─────────────────


def test_stt_unconfigured_returns_503(client, settings, rsa_keypair, db_session):
    """Text fallback has zero STT dependency: without provider config the
    transcribe seam fails cleanly and never blocks the text path."""
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers=_auth(token),
        files={"audio": ("turn.webm", b"\x00\x01fakeaudio", "audio/webm")},
    )
    assert resp.status_code == 503
    assert "detail" in resp.json()


def test_stt_configured_provider_transcribes(client, settings, rsa_keypair, db_session):
    """With a provider wired in, the seam returns the transcript; audio is
    processed in-memory and never persisted (data minimization)."""

    class FakeProvider:
        language = "ur-PK"

        def transcribe(self, audio: bytes) -> str:
            assert audio  # bytes arrive intact
            return "bacha do saal ka hai"

    from app.api.v1.endpoints.stt import get_stt_provider

    client.app.dependency_overrides[get_stt_provider] = lambda: FakeProvider()
    try:
        inst = _seed_institution(db_session)
        token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
        _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)
        resp = client.post(
            "/api/v1/stt/transcribe",
            headers=_auth(token),
            files={"audio": ("turn.webm", b"\x00\x01fakeaudio", "audio/webm")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["transcript"] == "bacha do saal ka hai"
        assert data["language"] == "ur-PK"
    finally:
        client.app.dependency_overrides.pop(get_stt_provider, None)


def test_stt_requires_auth_401(client):
    assert (
        client.post(
            "/api/v1/stt/transcribe",
            files={"audio": ("turn.webm", b"\x00\x01", "audio/webm")},
        ).status_code
        == 401
    )
