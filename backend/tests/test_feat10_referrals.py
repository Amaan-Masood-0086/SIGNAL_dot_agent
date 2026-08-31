"""FEAT-10 — loop-closing referral record.

Backlog contract: status {referred, pending_capacity, closed}, responsible
person, review date, escalation on missed review date, and the explicit
caretaker-confirmation gate (backend MUST #15 / TEST_PLAN §2: a referral
without the confirm step is REJECTED at the service layer).

A flag cannot silently sit unactioned: the referral closes the loop from
"concern raised" to "someone owns the follow-up with a date".
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


def _seed_flagged(db_session):
    """Tenant + child + session + one flagged row to refer from."""
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.session import Session as ConversationSession
    from app.models.staff import Staff
    from app.services.flag_service import FlagService

    inst = Institution(name="FEAT-10 Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(staff)
    child = Child(
        institution_id=inst.id, name="Referral Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True, dob=datetime.date(2025, 1, 1),
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
        reasoning_trail=[{"citation_ref": "HEAR-RF-003", "basis": "no response"}],
        explanation_text="See a clinician.",
        status="flagged",
    )
    db_session.flush()
    return inst, staff, flag


def test_referral_requires_auth_401(client):
    assert (
        client.post(f"/api/v1/flags/{uuid.uuid4()}/referral", json={}).status_code
        == 401
    )


def test_confirmed_referral_created_and_audited(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    inst, staff, flag = _seed_flagged(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    resp = client.post(
        f"/api/v1/flags/{flag.id}/referral",
        headers=_auth(token),
        json={
            "caretaker_confirmed": True,
            "responsible_person": "Sister Ayesha",
            "review_date": "2026-09-15",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["status"] == "referred"
    assert data["caretaker_confirmed"] is True
    assert data["responsible_person"] == "Sister Ayesha"
    assert data["escalated"] is False

    from app.models.audit_log import AuditLogEntry

    entry = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_id == data["id"])
        .one()
    )
    assert entry.action == "referral.create"


def test_referral_without_confirmation_rejected(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    """TEST_PLAN §2: persisting a referral without the explicit confirm step
    is rejected — a flag can never auto-populate a referral."""
    inst, staff, flag = _seed_flagged(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    for body in (
        {"caretaker_confirmed": False},
        {"responsible_person": "someone"},
    ):
        resp = client.post(
            f"/api/v1/flags/{flag.id}/referral", headers=_auth(token), json=body
        )
        assert resp.status_code == 409, body

    from app.models.referral import Referral

    assert db_session.query(Referral).count() == 0


def test_referral_cross_institution_flag_403(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    inst, staff, flag = _seed_flagged(db_session)

    from app.models.institution import Institution
    from app.models.staff import Staff

    other_inst = Institution(name="Other", is_synthetic=True)
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

    resp = client.post(
        f"/api/v1/flags/{flag.id}/referral",
        headers=_auth(other_token),
        json={"caretaker_confirmed": True},
    )
    assert resp.status_code == 403


def test_referral_status_update_and_close(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    inst, staff, flag = _seed_flagged(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    created = client.post(
        f"/api/v1/flags/{flag.id}/referral",
        headers=_auth(token),
        json={"caretaker_confirmed": True, "review_date": "2026-09-15"},
    ).json()["data"]

    patched = client.patch(
        f"/api/v1/referrals/{created['id']}",
        headers=_auth(token),
        json={"status": "closed"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"]["status"] == "closed"


def test_referral_invalid_status_422(client, settings, rsa_keypair, db_session, loaded_kb):
    inst, staff, flag = _seed_flagged(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    created = client.post(
        f"/api/v1/flags/{flag.id}/referral",
        headers=_auth(token),
        json={"caretaker_confirmed": True},
    ).json()["data"]

    resp = client.patch(
        f"/api/v1/referrals/{created['id']}",
        headers=_auth(token),
        json={"status": "archived"},
    )
    assert resp.status_code == 422


def test_missed_review_date_escalates(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    """Acceptance: escalation logic against a PASSED review date. An open
    referral past its review date must surface escalated=true; closing it
    clears the escalation."""
    inst, staff, flag = _seed_flagged(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)
    created = client.post(
        f"/api/v1/flags/{flag.id}/referral",
        headers=_auth(token),
        json={"caretaker_confirmed": True, "review_date": "2026-08-01"},
    ).json()["data"]

    overdue = client.get(f"/api/v1/referrals/{created['id']}", headers=_auth(token))
    assert overdue.status_code == 200
    assert overdue.json()["data"]["escalated"] is True

    closed = client.patch(
        f"/api/v1/referrals/{created['id']}",
        headers=_auth(token),
        json={"status": "closed"},
    )
    assert closed.json()["data"]["escalated"] is False
