"""FEAT-12 — security pass: TEST_PLAN §1 IDOR suite T1–T5 consolidated.

T1 direct object swap, T2 forced browsing (enumeration), T3 parameter
tampering (client-supplied scope ignored), T4 missing function-level access
control (non-admin vs admin surface), T5 object-property authorization
(no field-level leakage — cross-institution reads return NO data fields).

Per-endpoint T1 coverage already lives in each feature's test file; this
module is the consolidated regression gate across the whole API surface.
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


def _two_tenants(db_session):
    """Victim tenant with full data + attacker tenant with a token."""
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.session import Session as ConversationSession
    from app.models.staff import Staff
    from app.services.flag_service import FlagService

    victim_inst = Institution(name="Victim Tenant", is_synthetic=True)
    db_session.add(victim_inst)
    db_session.flush()
    victim_staff = Staff(
        id=uuid.uuid4(), institution_id=victim_inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(victim_staff)
    child = Child(
        institution_id=victim_inst.id, name="Victim Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True, dob=datetime.date(2026, 1, 1),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    session = ConversationSession(
        institution_id=victim_inst.id, child_id=child.id,
        staff_id=victim_staff.id, mode="text",
    )
    db_session.add(session)
    db_session.flush()
    flag = FlagService(db_session).create_flag(
        institution_id=victim_inst.id, session_id=session.id, child_id=child.id,
        domain="Hearing", confidence_grade="high",
        reasoning_trail=[{"citation_ref": "HEAR-RF-016", "basis": "b"}],
        explanation_text="e", status="flagged",
    )
    db_session.flush()

    attacker_inst = Institution(name="Attacker Tenant", is_synthetic=True)
    db_session.add(attacker_inst)
    db_session.flush()
    attacker_staff = Staff(
        id=uuid.uuid4(), institution_id=attacker_inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(attacker_staff)
    db_session.flush()

    return {
        "victim_inst": victim_inst,
        "child": child,
        "session": session,
        "flag": flag,
        "attacker_inst": attacker_inst,
        "attacker_staff": attacker_staff,
    }


# ── T1: direct object reference swap (cross-institution reads) ──────────────


def test_t1_direct_swap_blocked_everywhere(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    data = _two_tenants(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=data["attacker_inst"].id,
        staff_id=data["attacker_staff"].id,
    )
    headers = _auth(token)

    assert client.get(f"/api/v1/children/{data['child'].id}", headers=headers).status_code == 403
    assert client.get(f"/api/v1/sessions/{data['session'].id}", headers=headers).status_code == 403
    assert client.get(f"/api/v1/flags/{data['flag'].id}", headers=headers).status_code == 403
    assert (
        client.get(f"/api/v1/children/{data['child'].id}/flags", headers=headers).status_code
        == 403
    )
    assert (
        client.get(f"/api/v1/sessions/{data['session'].id}/flags", headers=headers).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/sessions/{data['session'].id}/reason",
            headers=headers, json={"raw_input": "snooping"},
        ).status_code
        == 403
    )


# ── T2: forced browsing — enumeration yields uniform 403, zero leakage ──────


def test_t2_enumeration_uniform_403_no_leakage(
    client, settings, rsa_keypair, db_session
):
    data = _two_tenants(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=data["attacker_inst"].id,
        staff_id=data["attacker_staff"].id,
    )
    headers = _auth(token)

    bodies = set()
    for _ in range(10):
        guess = str(uuid.uuid4())
        resp_child = client.get(f"/api/v1/children/{guess}", headers=headers)
        resp_session = client.get(f"/api/v1/sessions/{guess}", headers=headers)
        resp_flag = client.get(f"/api/v1/flags/{guess}", headers=headers)
        for resp in (resp_child, resp_session, resp_flag):
            assert resp.status_code == 403
            body = resp.json()
            # Error shape is identical for missing vs foreign — existence
            # never leaks, and no data fields ride along.
            assert set(body.keys()) == {"detail"}
            bodies.add(body["detail"])
    assert bodies == {"Access denied"}


# ── T3: parameter tampering — client-supplied scope is ignored ──────────────


def test_t3_client_supplied_scope_ignored(
    client, settings, rsa_keypair, db_session
):
    """The attacker smuggles institution_id / child ownership fields into
    request bodies — scope must derive ONLY from the signed JWT claim."""
    data = _two_tenants(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=data["attacker_inst"].id,
        staff_id=data["attacker_staff"].id,
    )
    headers = _auth(token)

    # Smuggled institution_id on session creation: the server scopes by JWT,
    # so the victim's child is still unreachable.
    resp = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={
            "child_id": str(data["child"].id),
            "mode": "text",
            "institution_id": str(data["victim_inst"].id),
        },
    )
    assert resp.status_code == 403

    # Smuggled turn_number / institution on observations is likewise inert
    # against a victim session.
    resp = client.post(
        f"/api/v1/sessions/{data['session'].id}/observations",
        headers=headers,
        json={"raw_input": "tampered", "turn_number": 99,
              "institution_id": str(data["victim_inst"].id)},
    )
    assert resp.status_code == 403


# ── T4: missing function-level access control (non-admin vs admin) ──────────


def test_t4_caretaker_locked_out_of_all_admin_surfaces(
    client, settings, rsa_keypair, db_session
):
    data = _two_tenants(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=data["attacker_inst"].id,
        staff_id=data["attacker_staff"].id,
    )
    headers = _auth(token)

    assert client.get("/api/v1/audit_log", headers=headers).status_code == 403
    assert client.get("/api/v1/audit_log/integrity", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/staff", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/providers", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/usage", headers=headers).status_code == 403


# ── T5: object-property authorization — no field-level leakage ──────────────


def test_t5_cross_institution_responses_carry_no_fields(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    """A blocked cross-institution read must not leak even one property of
    the target object (name, id echo, timestamps, nested fields)."""
    data = _two_tenants(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=data["attacker_inst"].id,
        staff_id=data["attacker_staff"].id,
    )
    headers = _auth(token)

    for url in (
        f"/api/v1/children/{data['child'].id}",
        f"/api/v1/sessions/{data['session'].id}",
        f"/api/v1/flags/{data['flag'].id}",
    ):
        resp = client.get(url, headers=headers)
        assert resp.status_code == 403
        text = resp.text
        assert str(data["child"].id) not in text
        assert "Victim Child" not in text
        assert "success" not in resp.json()  # envelope never wraps a 403


# ── §4 supporting checks: rate limiting + audit tamper-evidence exist ───────


def test_rate_limit_guards_remain_on_paid_surfaces():
    """Regression pin: the 30/min budget stays on the turn-capture and STT
    surfaces, and the reasoning surface gets one too (paid LLM calls)."""
    from app.api.v1.endpoints.reasoning import REASON_LIMITER
    from app.api.v1.endpoints.sessions import OBSERVATION_LIMITER
    from app.api.v1.endpoints.stt import TRANSCRIBE_LIMITER

    for limiter in (OBSERVATION_LIMITER, TRANSCRIBE_LIMITER, REASON_LIMITER):
        assert limiter.limit == 30
        assert limiter.window_seconds == 60.0


def test_audit_log_stays_append_only_at_db_level(pg_engine):
    """FEAT-01 grants: the app role has SELECT+INSERT only on audit_log —
    UPDATE/DELETE revoked (tamper-evidence foundation, THREAT_MODEL §1)."""
    from sqlalchemy import text

    with pg_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT privilege_type FROM information_schema.role_table_grants "
                "WHERE table_name = 'audit_log' AND grantee = 'signal_app'"
            )
        ).scalars().all()
    assert set(rows) == {"INSERT", "SELECT"}
