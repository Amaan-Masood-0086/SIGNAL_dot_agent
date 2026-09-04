"""FEAT-05 reasoning endpoint — POST /sessions/{id}/reason.

Caretaker-facing turn-capture surface for the pipeline: institution-scoped
like every business endpoint (an admin token gets NO cross-institution
reach here), audit-chained, rate-limited, and provider-injectable exactly
like the FEAT-03 STT seam.
"""

from __future__ import annotations

import datetime
import json
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
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture(scope="module")
def loaded_kb(pg_engine):
    """Knowledge base present for tests that reach the grounding layer."""
    from sqlalchemy import delete
    from sqlalchemy.orm import Session

    from app.models.milestone import Milestone
    from app.services.knowledge import load_knowledge_base

    session = Session(bind=pg_engine, expire_on_commit=False)
    load_knowledge_base(session)
    session.commit()
    yield session
    # Keep the shared session DB clean for the FEAT-04 loader tests.
    session.execute(delete(Milestone))
    session.commit()
    session.close()


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


def _seed(db_session, *, child_age_months=8, estimated=None):
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="Reasoning Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused",
        role="caretaker",
        is_synthetic=True,
    )
    db_session.add(staff)
    reference = datetime.date(2026, 8, 31)
    if estimated:
        child = Child(
            institution_id=inst.id, name="Reasoning Child",
            intake_date=datetime.date(2026, 8, 1),
            dob_confirmed=False, estimated_age_range=estimated, is_synthetic=True,
        )
    else:
        total_months = reference.year * 12 + (reference.month - 1) - child_age_months
        dob = datetime.date(total_months // 12, total_months % 12 + 1, min(reference.day, 28))
        child = Child(
            institution_id=inst.id, name="Reasoning Child",
            intake_date=datetime.date(2026, 8, 1),
            dob_confirmed=True, dob=dob, is_synthetic=True,
        )
    db_session.add(child)
    db_session.flush()
    return inst, staff, child


def _open_session(client, token, child_id):
    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child_id), "mode": "text"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


class ScriptedProvider:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, agent, tier, system, user):
        self.calls.append({"agent": agent, "tier": tier, "system": system, "user": user})
        return self.responses.pop(0)


def _obs(signals, **kw):
    return json.dumps({"signals": signals, "safeguarding_pattern": kw.get("safeguarding", False),
                       "key_items_missing": kw.get("key_missing", False)})


def _reason(**kw):
    payload = {"concluded": True, "follow_up_question": None, "key_items_missing": False,
               "confirmed_red_flags": [], "missed_milestones": [], "met_milestones": [],
               "risk_modifiers": []}
    payload.update(kw)
    return json.dumps(payload)


def _with_provider(client, provider):
    from app.api.v1.endpoints.reasoning import get_reasoning_provider

    client.app.dependency_overrides[get_reasoning_provider] = lambda: provider


# ── Auth + scoping ───────────────────────────────────────────────────────────


def test_reason_requires_auth_401(client, db_session):
    assert client.post(
        f"/api/v1/sessions/{uuid.uuid4()}/reason", json={"raw_input": "x"}
    ).status_code == 401


def test_reason_validation_422(client, settings, rsa_keypair, db_session):
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)
    url = f"/api/v1/sessions/{session_id}/reason"
    assert client.post(url, headers=_auth(token), json={"raw_input": "   "}).status_code == 422
    assert client.post(url, headers=_auth(token), json={}).status_code == 422


def test_reason_cross_institution_403(client, settings, rsa_keypair, db_session):
    """IDOR T1: reasoning on another institution's session is forbidden."""
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)

    other_inst, other_staff, _ = _seed(db_session)
    other_token = _mint(settings, rsa_keypair, institution_id=other_inst.id, staff_id=other_staff.id)
    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(other_token),
        json={"raw_input": "snooping"},
    )
    assert resp.status_code == 403


def test_admin_token_stays_institution_scoped_on_reason(
    client, settings, rsa_keypair, db_session
):
    """RLS-boundary regression: the system-level admin role gains NOTHING on
    the caretaker-facing reasoning surface."""
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)

    admin_inst, admin_staff, _ = _seed(db_session)
    admin_staff.role = "admin"
    db_session.flush()
    admin_token = _mint(
        settings, rsa_keypair, institution_id=admin_inst.id,
        staff_id=admin_staff.id, role="admin",
    )
    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(admin_token),
        json={"raw_input": "admin reaching across"},
    )
    assert resp.status_code == 403


# ── Provider resolution ─────────────────────────────────────────────────────


def test_reason_unconfigured_llm_503_with_fallback_guidance(
    client, settings, rsa_keypair, db_session
):
    """No LLM provider and no synthetic fallback → clean 503 (STT pattern)."""
    from app.api.v1.endpoints.reasoning import get_reasoning_provider

    client.app.dependency_overrides[get_reasoning_provider] = lambda: None

    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)
    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(token),
        json={"raw_input": "he doesn't react to sounds"},
    )
    assert resp.status_code == 503
    assert "detail" in resp.json()


# ── Happy path + persistence ────────────────────────────────────────────────


def test_reason_flagged_run_persists_flag_and_audits(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    inst, staff, child = _seed(db_session, child_age_months=8)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)
    provider = ScriptedProvider(
        _obs(["no response to loud sounds"]),
        _reason(confirmed_red_flags=["HEAR-RF-003"]),
        "Please see a doctor soon about what you described.",
    )
    _with_provider(client, provider)

    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(token),
        json={"raw_input": "He doesn't turn around even when I clap loudly"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "flagged"
    assert data["grade"] == "HIGH"
    assert data["domain"] == "Hearing"
    assert data["citations"] == ["HEAR-RF-003"]
    assert data["age_uncertain"] is False
    assert data["flag_id"]
    assert "HEAR-RF-003" in data["explanation_text"]

    from app.models.audit_log import AuditLogEntry
    from app.models.flag import Flag

    assert db_session.query(Flag).count() == 1
    actions = {
        e.action for e in db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_type.in_(["flag", "reasoning"])).all()
    }
    assert actions == {"reasoning.run", "flag.create"}


def test_reason_follow_up_then_conclusion_two_turns(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    inst, staff, child = _seed(db_session, child_age_months=8)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)
    provider = ScriptedProvider(
        _obs(["no response to sounds"]),
        _reason(concluded=False, follow_up_question="Does he react to a door slamming?"),
        _obs(["still no response"]),
        _reason(confirmed_red_flags=["HEAR-RF-003"]),
        "Please see a doctor soon.",
    )
    _with_provider(client, provider)
    url = f"/api/v1/sessions/{session_id}/reason"

    first = client.post(url, headers=_auth(token), json={"raw_input": "he doesn't react to sounds"})
    assert first.status_code == 200
    body = first.json()["data"]
    assert body["status"] == "follow_up"
    assert body["follow_up_question"] == "Does he react to a door slamming?"
    assert body["turn"] == 1 and body["max_turns"] == 5

    second = client.post(url, headers=_auth(token), json={"raw_input": "No, he doesn't seem to notice"})
    assert second.status_code == 200
    body2 = second.json()["data"]
    assert body2["status"] == "flagged"
    assert body2["turn"] == 2

    # The follow-up question and both caretaker turns are stored in the
    # session's turn history (multi-turn continuity groundwork).
    from app.models.observation import Observation

    rows = (
        db_session.query(Observation)
        .filter(Observation.session_id == uuid.UUID(session_id))
        .order_by(Observation.turn_number.asc())
        .all()
    )
    assert len(rows) == 3
    assert rows[1].raw_input == "Does he react to a door slamming?"
    assert rows[1].extracted_signals == {"role": "risk_reasoning", "follow_up": True}


def test_reason_refuses_turn_beyond_cap_409(client, settings, rsa_keypair, db_session):
    inst, staff, child = _seed(db_session, child_age_months=8)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)

    from app.models.observation import Observation

    # Six prior caretaker turns already on record.
    for i in range(6):
        db_session.add(Observation(
            institution_id=inst.id, session_id=uuid.UUID(session_id),
            turn_number=i + 1, raw_input=f"turn {i}",
        ))
    db_session.flush()

    provider = ScriptedProvider()
    _with_provider(client, provider)
    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(token),
        json={"raw_input": "one more"},
    )
    assert resp.status_code == 409
    assert provider.calls == []  # nothing runs past the cap


def test_reason_on_completed_session_409(client, settings, rsa_keypair, db_session):
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)
    client.post(f"/api/v1/sessions/{session_id}/complete", headers=_auth(token))

    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(token),
        json={"raw_input": "too late"},
    )
    assert resp.status_code == 409


def test_deactivated_staff_cannot_reason(client, settings, rsa_keypair, db_session):
    inst, staff, child = _seed(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    session_id = _open_session(client, token, child.id)

    staff.is_active = False
    db_session.flush()

    resp = client.post(
        f"/api/v1/sessions/{session_id}/reason",
        headers=_auth(token),
        json={"raw_input": "should be refused"},
    )
    assert resp.status_code == 403
