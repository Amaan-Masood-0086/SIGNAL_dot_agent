"""FEAT-09 — confidence-graded flag surface + reasoning trail (TRD §4).

Backend half: `GET /flags/{id}` is IDOR-sensitive (T1 mandatory) — scope
derived ONLY from the JWT's institution claim; `GET /children/{id}/flags`
and `GET /sessions/{id}/flags` feed the caretaker-facing display. Every
returned trail entry resolves to a real knowledge-base row with its
description + source (TEST_PLAN §3 citation integrity) — a clinician can
independently review the basis (ADR-03/08).
"""

from __future__ import annotations

import datetime
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
    from app.api.deps import get_db
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app(settings)
    app.dependency_overrides[get_db] = lambda: db_session
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


def _seed_flag(db_session):
    """Institution + staff + child + session + one flagged row with a real
    two-ref trail."""
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.session import Session as ConversationSession
    from app.models.staff import Staff
    from app.services.flag_service import FlagService

    inst = Institution(name="FEAT-09 Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(staff)
    child = Child(
        institution_id=inst.id, name="Flag Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True, dob=datetime.date(2026, 1, 1),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    session = ConversationSession(
        institution_id=inst.id, child_id=child.id, staff_id=staff.id, mode="text"
    )
    db_session.add(session)
    db_session.flush()

    flag = FlagService(db_session).create_flag(
        institution_id=inst.id,
        session_id=session.id,
        child_id=child.id,
        domain="Hearing",
        confidence_grade="high",
        reasoning_trail=[
            {"citation_ref": "HEAR-RF-003", "basis": "no response to sound"},
        ],
        explanation_text="Please see a clinician soon.",
        status="flagged",
    )
    db_session.flush()
    return {"institution": inst, "staff": staff, "child": child,
            "session": session, "flag": flag}


def test_flags_require_auth_401(client):
    assert client.get(f"/api/v1/flags/{uuid.uuid4()}").status_code == 401


def test_own_flag_returns_grade_and_resolving_trail(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    seeded = _seed_flag(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=seeded["institution"].id, staff_id=seeded["staff"].id,
    )

    resp = client.get(f"/api/v1/flags/{seeded['flag'].id}", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["confidence_grade"] == "high"
    assert data["domain"] == "Hearing"
    assert data["status"] == "flagged"

    trail = data["reasoning_trail"]
    assert len(trail) == 1
    entry = trail[0]
    assert entry["citation_ref"] == "HEAR-RF-003"
    # Citation integrity (TEST_PLAN §3): the entry resolves to the real KB
    # row and carries its clinician-reviewable description + source.
    assert entry["description"]
    assert entry["source"]


def test_cross_institution_flag_403(client, settings, rsa_keypair, db_session, loaded_kb):
    """IDOR T1: another institution's staff cannot read the flag."""
    seeded = _seed_flag(db_session)

    from app.models.institution import Institution
    from app.models.staff import Staff

    other_inst = Institution(name="Other Tenant", is_synthetic=True)
    db_session.add(other_inst)
    db_session.flush()
    other_staff = Staff(
        id=uuid.uuid4(), institution_id=other_inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(other_staff)
    db_session.flush()

    other_token = _mint(
        settings, rsa_keypair, institution_id=other_inst.id, staff_id=other_staff.id
    )
    resp = client.get(f"/api/v1/flags/{seeded['flag'].id}", headers=_auth(other_token))
    assert resp.status_code == 403
    assert "data" not in resp.json()


def test_unknown_flag_uniform_403(client, settings, rsa_keypair, db_session):
    seeded = _seed_flag(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=seeded["institution"].id, staff_id=seeded["staff"].id,
    )
    assert client.get(f"/api/v1/flags/{uuid.uuid4()}", headers=_auth(token)).status_code == 403


def test_child_flags_list_scoped(client, settings, rsa_keypair, db_session, loaded_kb):
    seeded = _seed_flag(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=seeded["institution"].id, staff_id=seeded["staff"].id,
    )

    resp = client.get(
        f"/api/v1/children/{seeded['child'].id}/flags", headers=_auth(token)
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["id"] == str(seeded["flag"].id)


def test_session_flags_list_scoped(client, settings, rsa_keypair, db_session, loaded_kb):
    seeded = _seed_flag(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=seeded["institution"].id, staff_id=seeded["staff"].id,
    )

    resp = client.get(
        f"/api/v1/sessions/{seeded['session'].id}/flags", headers=_auth(token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1
