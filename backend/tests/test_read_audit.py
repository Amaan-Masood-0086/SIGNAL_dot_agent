"""Read-access auditing (audit finding F3).

Before this, every one of the fifteen audited actions was a WRITE. Seven
endpoints returned child health data and none of them left a trace, so
"who opened this child's record" was unanswerable — a compliance-forced
requirement in a clinical product, and the exact question the tamper-evident
chain exists to answer.

These tests pin the behaviour, including the deliberate decision NOT to log
denied attempts (see test at the bottom).
"""

from __future__ import annotations

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


def _mint(settings, rsa_keypair, *, institution_id, staff_id, role):
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


def _tenant(db_session, *, role="caretaker"):
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name=f"Read Tenant {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused",
        role=role,
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return inst, staff


def _child(db_session, institution_id):
    import datetime

    from app.models.child import Child

    child = Child(
        id=uuid.uuid4(),
        institution_id=institution_id,
        name="Read Audit Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True,
        dob=datetime.date(2024, 1, 1),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


def _actions(db_session, action):
    from app.models.audit_log import AuditLogEntry
    from sqlalchemy import select

    return db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.action == action)
    ).scalars().all()


def test_opening_a_child_record_is_audited(client, settings, rsa_keypair, db_session):
    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id, role="caretaker")

    before = len(_actions(db_session, "child.read"))
    assert client.get(f"/api/v1/children/{child.id}", headers=_auth(token)).status_code == 200

    rows = _actions(db_session, "child.read")
    assert len(rows) == before + 1
    entry = rows[-1]
    assert entry.resource_id == str(child.id)
    assert entry.actor_id == staff.id


def test_screening_history_read_is_audited_once_per_query(
    client, settings, rsa_keypair, db_session
):
    """Per query, not per row — a roster read is one act of access, and a row
    per flag would bury the chain it is meant to make readable."""
    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id, role="caretaker")

    before = len(_actions(db_session, "flag.list"))
    assert client.get(f"/api/v1/children/{child.id}/flags", headers=_auth(token)).status_code == 200

    rows = _actions(db_session, "flag.list")
    assert len(rows) == before + 1
    assert rows[-1].resource_id == str(child.id)


def test_cross_institution_admin_roster_read_is_audited(
    client, settings, rsa_keypair, db_session
):
    """The one read that crosses the tenant boundary is the one that most
    needs a trail."""
    inst, admin = _tenant(db_session, role="admin")
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")

    before = len(_actions(db_session, "admin.children_list"))
    assert client.get("/api/v1/admin/children", headers=_auth(token)).status_code == 200

    rows = _actions(db_session, "admin.children_list")
    assert len(rows) == before + 1
    assert rows[-1].actor_id == admin.id


def test_denied_reads_are_not_audited_against_the_target_id(
    client, settings, rsa_keypair, db_session
):
    """A 403 never confirms the record exists. Writing an audit row keyed to
    an id the caller may not own would leak exactly what the uniform 403 is
    there to hide — so denied reads are deliberately not logged here."""
    inst_a, staff_a = _tenant(db_session)
    inst_b, _ = _tenant(db_session)
    foreign_child = _child(db_session, inst_b.id)
    token = _mint(
        settings, rsa_keypair, institution_id=inst_a.id, staff_id=staff_a.id, role="caretaker"
    )

    before = len(_actions(db_session, "child.read"))
    resp = client.get(f"/api/v1/children/{foreign_child.id}", headers=_auth(token))
    assert resp.status_code == 403

    assert len(_actions(db_session, "child.read")) == before


def test_read_entries_extend_the_same_hash_chain(client, settings, rsa_keypair, db_session):
    """Read entries are ordinary chain members — tamper-evidence must cover
    them exactly as it covers writes."""
    from app.services.audit import verify_audit_chain_detail

    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id, role="caretaker")

    client.get(f"/api/v1/children/{child.id}", headers=_auth(token))
    db_session.flush()

    intact, checked, first_broken = verify_audit_chain_detail(db_session)
    assert intact, f"chain broke at sequence {first_broken}"
    assert checked > 0
