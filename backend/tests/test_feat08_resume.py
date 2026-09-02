"""FEAT-08 — session save/resume (interrupted-shift handling).

Acceptance: interrupt mid-conversation, resume via a new request, full
context intact. "Interrupted" = an in_progress session left idle; RESUME
stamps it (`resumed_at`) via a new request and the accumulated turn history
+ reasoning state carries over untouched. Completed sessions cannot be
resumed (409); cross-institution resume is 403 (IDOR T1).
"""

from __future__ import annotations

import datetime
import json
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def loaded_kb(pg_engine):
    from sqlalchemy import delete
    from sqlalchemy.orm import Session

    from app.models.milestone import Milestone
    from app.services.knowledge import load_knowledge_base

    session = Session(bind=pg_engine, expire_on_commit=False)
    load_knowledge_base(session)
    session.commit()
    yield session
    session.execute(delete(Milestone))
    session.commit()
    session.close()


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
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def _mint(settings, rsa_keypair, *, institution_id, staff_id, role="caretaker"):
    private_pem, _ = rsa_keypair
    from app.core import security

    return security.create_access_token(
        staff_id=str(staff_id),
        institution_id=str(institution_id),
        role=role,
        private_key_pem=private_pem,
        expires_minutes=15,
        settings=settings,
    )


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _seed(db_session):
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="FEAT-08 Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(staff)
    child = Child(
        institution_id=inst.id, name="Resume Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True, dob=datetime.date(2025, 8, 15),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return inst, staff, child


def _start(client, token, child_id):
    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child_id), "mode": "text"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


def test_resume_requires_auth_401(client):
    assert client.post(f"/api/v1/sessions/{uuid.uuid4()}/resume").status_code == 401


def test_resume_interrupted_session_stamps_resumed_at(
    client, settings, rsa_keypair, db_session
):
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _start(client, token, child.id)

    # Two turns captured before the "shift interruption".
    for text in ("first turn", "second turn"):
        assert client.post(
            f"/api/v1/sessions/{session_id}/observations",
            headers=_auth(token),
            json={"raw_input": text},
        ).status_code == 201

    # Simulated interruption: nothing happens; then a NEW request resumes.
    resp = client.post(f"/api/v1/sessions/{session_id}/resume", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "in_progress"
    assert data["resumed_at"] is not None


def test_resume_keeps_full_context_intact(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    """After resume, turn history is complete AND reasoning continues from
    the accumulated turns (server-side turn accounting sees both pre-
    interruption turns)."""
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _start(client, token, child.id)
    for text in ("turn one", "turn two"):
        client.post(
            f"/api/v1/sessions/{session_id}/observations",
            headers=_auth(token),
            json={"raw_input": text},
        )

    client.post(f"/api/v1/sessions/{session_id}/resume", headers=_auth(token))

    # History intact.
    page = client.get(
        f"/api/v1/sessions/{session_id}/observations", headers=_auth(token)
    )
    assert page.json()["data"]["total"] == 2

    # Reasoning sees this as turn 3 — context survived the interruption.
    class ScriptedProvider:
        def __init__(self, *responses):
            self.responses = list(responses)

        def complete(self, *, agent, tier, system, user):
            return self.responses.pop(0)

    from app.api.v1.endpoints.reasoning import get_reasoning_provider

    provider = ScriptedProvider(
        json.dumps({"signals": ["s"], "safeguarding_pattern": False,
                    "key_items_missing": False}),
        json.dumps({"concluded": False, "follow_up_question": "q?",
                    "key_items_missing": False, "confirmed_red_flags": [],
                    "missed_milestones": [], "met_milestones": [],
                    "risk_modifiers": []}),
    )
    client.app.dependency_overrides[get_reasoning_provider] = lambda: provider
    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(token),
        json={"raw_input": "third turn after the break"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["turn"] == 3


def test_resume_completed_session_409(client, settings, rsa_keypair, db_session):
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _start(client, token, child.id)
    client.post(f"/api/v1/sessions/{session_id}/complete", headers=_auth(token))

    resp = client.post(f"/api/v1/sessions/{session_id}/resume", headers=_auth(token))
    assert resp.status_code == 409


def test_resume_cross_institution_403(client, settings, rsa_keypair, db_session):
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _start(client, token, child.id)

    other_inst, other_staff, _ = _seed(db_session)
    other_token = _mint(
        settings, rsa_keypair, institution_id=other_inst.id, staff_id=other_staff.id
    )
    resp = client.post(f"/api/v1/sessions/{session_id}/resume", headers=_auth(other_token))
    assert resp.status_code == 403
