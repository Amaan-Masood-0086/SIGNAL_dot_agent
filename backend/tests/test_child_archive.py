"""Child archive — reversible removal from the active roster (migration 0006).

Before this there was no way to take a child off the roster at all: a
duplicate or mistyped registration stayed forever. The obvious fix — a
DELETE — is the wrong one here, and these tests pin why:

  - a mistaken registration and a child who has LEFT the institution both
    leave the roster, but only one of them has a retention question
  - children's health records carry long, legally mandated retention, and
    that policy is not this feature's decision to make
  - the flags, sessions and observations already written about a child must
    keep their foreign keys

So: archive, with a mandatory reason, reversible, audit-chained, and no
DELETE grant anywhere.
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
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


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


def _tenant(db_session):
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name=f"Archive {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused",
        role="caretaker",
        is_active=True,
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return inst, staff


def _child(db_session, institution_id, name="Archive Child"):
    from app.models.child import Child

    child = Child(
        id=uuid.uuid4(),
        institution_id=institution_id,
        name=name,
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True,
        dob=datetime.date(2024, 1, 1),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


def test_archiving_removes_the_child_from_the_roster(
    client, settings, rsa_keypair, db_session
):
    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    before = client.get("/api/v1/children", headers=_auth(token)).json()["data"]
    assert before["total"] == 1

    resp = client.post(
        f"/api/v1/children/{child.id}/archive",
        headers=_auth(token),
        json={"reason": "Duplicate registration"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["archived_reason"] == "Duplicate registration"

    after = client.get("/api/v1/children", headers=_auth(token)).json()["data"]
    assert after["total"] == 0
    assert after["items"] == []


def test_archiving_does_not_destroy_the_record(client, settings, rsa_keypair, db_session):
    """The whole point: the row survives for whatever retention policy is set."""
    from app.models.child import Child

    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    client.post(
        f"/api/v1/children/{child.id}/archive",
        headers=_auth(token),
        json={"reason": "Left the institution"},
    )
    db_session.flush()

    row = db_session.get(Child, child.id)
    assert row is not None, "archive must never delete the row"
    assert row.archived_at is not None
    assert row.name == "Archive Child"
    # The profile is still reachable — a clinician reviewing an old flag must
    # still be able to see whose record it was.
    assert client.get(f"/api/v1/children/{child.id}", headers=_auth(token)).status_code == 200


def test_archive_requires_a_meaningful_reason(client, settings, rsa_keypair, db_session):
    """"Why is this child off the roster" is the question an auditor asks."""
    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    for bad in ({}, {"reason": ""}, {"reason": "x"}):
        resp = client.post(
            f"/api/v1/children/{child.id}/archive", headers=_auth(token), json=bad
        )
        assert resp.status_code == 422, f"accepted a blank reason: {bad}"


def test_archive_is_reversible(client, settings, rsa_keypair, db_session):
    """A caretaker who archives the wrong child must not need a DBA."""
    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    client.post(
        f"/api/v1/children/{child.id}/archive",
        headers=_auth(token),
        json={"reason": "Archived by mistake"},
    )
    resp = client.post(f"/api/v1/children/{child.id}/restore", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["archived_at"] is None
    assert resp.json()["data"]["archived_reason"] is None

    roster = client.get("/api/v1/children", headers=_auth(token)).json()["data"]
    assert roster["total"] == 1


def test_double_archive_and_stray_restore_are_refused(
    client, settings, rsa_keypair, db_session
):
    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    assert client.post(f"/api/v1/children/{child.id}/restore", headers=_auth(token)).status_code == 409

    client.post(
        f"/api/v1/children/{child.id}/archive",
        headers=_auth(token),
        json={"reason": "Left the institution"},
    )
    second = client.post(
        f"/api/v1/children/{child.id}/archive",
        headers=_auth(token),
        json={"reason": "again"},
    )
    assert second.status_code == 409


def test_cannot_archive_another_institutions_child(
    client, settings, rsa_keypair, db_session
):
    """IDOR T2: uniform 403, never a hint that the record exists."""
    inst_a, staff_a = _tenant(db_session)
    inst_b, _ = _tenant(db_session)
    foreign = _child(db_session, inst_b.id)
    token = _mint(settings, rsa_keypair, institution_id=inst_a.id, staff_id=staff_a.id)

    resp = client.post(
        f"/api/v1/children/{foreign.id}/archive",
        headers=_auth(token),
        json={"reason": "not mine to archive"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Access denied"


def test_archive_and_restore_are_audit_chained(client, settings, rsa_keypair, db_session):
    from sqlalchemy import select

    from app.models.audit_log import AuditLogEntry
    from app.services.audit import verify_audit_chain_detail

    inst, staff = _tenant(db_session)
    child = _child(db_session, inst.id)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    client.post(
        f"/api/v1/children/{child.id}/archive",
        headers=_auth(token),
        json={"reason": "Left the institution"},
    )
    client.post(f"/api/v1/children/{child.id}/restore", headers=_auth(token))
    db_session.flush()

    actions = db_session.execute(
        select(AuditLogEntry.action).where(
            AuditLogEntry.resource_id == str(child.id)
        )
    ).scalars().all()
    assert "child.archive" in actions
    assert "child.restore" in actions

    intact, checked, first_broken = verify_audit_chain_detail(db_session)
    assert intact, f"chain broke at sequence {first_broken}"
    assert checked > 0


# ── Finding an archived child again (the archive must not be a black hole) ──


def test_archived_children_are_listable(client, settings, rsa_keypair, db_session):
    """Hiding a child with no way to list them again would make archiving a
    one-way door — the caretaker could not even check what they archived."""
    inst, staff = _tenant(db_session)
    kept = _child(db_session, inst.id, name="Still Here")
    gone = _child(db_session, inst.id, name="Moved On")
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    client.post(
        f"/api/v1/children/{gone.id}/archive",
        headers=_auth(token),
        json={"reason": "Left the institution"},
    )

    active = client.get("/api/v1/children", headers=_auth(token)).json()["data"]
    assert [c["name"] for c in active["items"]] == ["Still Here"]

    archived = client.get(
        "/api/v1/children?status=archived", headers=_auth(token)
    ).json()["data"]
    assert [c["name"] for c in archived["items"]] == ["Moved On"]
    assert archived["items"][0]["archived_reason"] == "Left the institution"

    every = client.get("/api/v1/children?status=all", headers=_auth(token)).json()["data"]
    assert every["total"] == 2


def test_status_filter_rejects_anything_unexpected(
    client, settings, rsa_keypair, db_session
):
    """Allowlisted values only — an unrecognised status must not fall through
    to 'show everything'."""
    inst, staff = _tenant(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    resp = client.get("/api/v1/children?status=everything", headers=_auth(token))
    assert resp.status_code == 422


def test_archived_list_stays_institution_scoped(
    client, settings, rsa_keypair, db_session
):
    """The new filter must not become a way around tenant isolation."""
    inst_a, staff_a = _tenant(db_session)
    inst_b, staff_b = _tenant(db_session)
    theirs = _child(db_session, inst_b.id, name="Other Tenant Child")
    token_b = _mint(settings, rsa_keypair, institution_id=inst_b.id, staff_id=staff_b.id)
    client.post(
        f"/api/v1/children/{theirs.id}/archive",
        headers=_auth(token_b),
        json={"reason": "Left the institution"},
    )

    token_a = _mint(settings, rsa_keypair, institution_id=inst_a.id, staff_id=staff_a.id)
    for scope in ("archived", "all"):
        page = client.get(
            f"/api/v1/children?status={scope}", headers=_auth(token_a)
        ).json()["data"]
        assert all(c["name"] != "Other Tenant Child" for c in page["items"]), scope
