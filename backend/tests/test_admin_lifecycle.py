"""Admin removal and assignment.

Two operator requests, and they landed on opposite sides of a line this
codebase draws deliberately.

DELETION. Nothing in SIGNAL was hard-deletable: staff deactivate, children
archive, `signal_app` holds no DELETE grant, and REMEDIATION_BACKLOG R7
("retention + defensible deletion") is explicitly open pending a policy
decision. That is not bureaucracy — a flag is a clinical finding, the audit
chain names the staff member who produced it, and destroying either removes
the evidence the product exists to create.

But that reasoning only applies to records that HAVE such content. A mistyped
registration with no sessions, no flags and no observations carries no
clinical record and raises no retention question at all. So deletion is
allowed exactly there, and refused — with the safe alternative named —
everywhere else. The rule is a property of the row, not a permission of the
caller, which is why an admin cannot override it.

ASSIGNMENT (migration 0007) records WHO IS RESPONSIBLE for a child. It is
deliberately NOT access control: every institution member still sees every
child. Narrowing that is R8, and it has a failure mode worth stating — a
child whose assigned caretaker is off shift must not vanish for the
colleague covering the ward.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.deps import get_db, get_tenant_db
from app.core.config import Settings
from app.core.security import create_access_token
from app.main import create_app
from app.models.audit_log import AuditLogEntry
from app.models.child import Child
from app.models.institution import Institution
from app.models.session import Session as ConversationSession
from app.models.staff import Staff


@pytest.fixture()
def settings(rsa_keypair) -> Settings:
    private_pem, public_pem = rsa_keypair
    return Settings(
        ENVIRONMENT="synthetic_only",
        CREDENTIAL_ENCRYPTION_KEY="MeogHhAdoVZ279u9hf3BlSQxH3rqq89e538bAoC8tQg=",
        JWT_PRIVATE_KEY=private_pem.decode(),
        JWT_PUBLIC_KEY=public_pem.decode(),
    )


@pytest.fixture()
def institution(db_session) -> Institution:
    row = Institution(name=f"Home {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(row)
    db_session.flush()
    return row


def _staff(db_session, institution, role="caretaker") -> Staff:
    row = Staff(
        institution_id=institution.id,
        email=f"{role}-{uuid.uuid4().hex[:8]}@signal.example",
        hashed_password="!placeholder",
        role=role,
        is_active=True,
        is_synthetic=True,
    )
    db_session.add(row)
    db_session.flush()
    return row


@pytest.fixture()
def admin(db_session, institution) -> Staff:
    return _staff(db_session, institution, "admin")


@pytest.fixture()
def caretaker(db_session, institution) -> Staff:
    return _staff(db_session, institution, "caretaker")


@pytest.fixture()
def child(db_session, institution) -> Child:
    import datetime

    row = Child(
        institution_id=institution.id,
        name="Test Child",
        intake_date=datetime.date.today(),
        dob_confirmed=False,
        estimated_age_range="24-30 months",
        is_synthetic=True,
    )
    db_session.add(row)
    db_session.flush()
    return row


@pytest.fixture()
def client(db_session, settings) -> TestClient:
    app = create_app(settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    return TestClient(app)


def auth(staff: Staff, settings: Settings) -> dict:
    token = create_access_token(
        staff_id=str(staff.id),
        institution_id=str(staff.institution_id),
        role=staff.role,
        settings=settings,
    )
    return {"Authorization": f"Bearer {token}"}


def _session_for(db_session, child: Child, staff: Staff) -> ConversationSession:
    row = ConversationSession(
        institution_id=child.institution_id,
        child_id=child.id,
        staff_id=staff.id,
        mode="text",
    )
    db_session.add(row)
    db_session.flush()
    return row


# ── deleting a child ────────────────────────────────────────────────────────


def test_a_child_with_no_history_can_be_deleted(
    client, admin, settings, child, db_session
):
    """The case that actually prompted this: a mistyped registration. No
    session, no flag, no observation — nothing a retention policy governs."""
    r = client.delete(
        f"/api/v1/admin/children/{child.id}", headers=auth(admin, settings)
    )
    assert r.status_code == 200, r.text
    assert db_session.get(Child, child.id) is None


def test_a_child_with_a_screening_history_is_refused(
    client, admin, settings, child, caretaker, db_session
):
    """A session means a clinical record exists. Deleting it would destroy
    the thing the product is for, and the answer is archive, not delete."""
    _session_for(db_session, child, caretaker)

    r = client.delete(
        f"/api/v1/admin/children/{child.id}", headers=auth(admin, settings)
    )
    assert r.status_code == 409
    assert "archive" in r.json()["detail"].lower()
    assert db_session.get(Child, child.id) is not None


def test_the_refusal_is_a_property_of_the_row_not_the_caller(
    client, admin, settings, child, caretaker, db_session
):
    """No force flag, no admin override. Whether deletion is safe depends on
    what the record contains, and no privilege changes that."""
    _session_for(db_session, child, caretaker)

    for params in ({"force": "true"}, {"confirm": "true"}):
        r = client.delete(
            f"/api/v1/admin/children/{child.id}",
            headers=auth(admin, settings),
            params=params,
        )
        assert r.status_code == 409, params
    assert db_session.get(Child, child.id) is not None


def test_child_deletion_is_audit_chained(client, admin, settings, child, db_session):
    child_id = str(child.id)
    client.delete(f"/api/v1/admin/children/{child.id}", headers=auth(admin, settings))

    entry = db_session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.action == "child.delete")
        .order_by(AuditLogEntry.sequence.desc())
    ).scalars().first()
    assert entry is not None and entry.resource_id == child_id
    assert entry.actor_id == admin.id


def test_caretaker_cannot_delete_a_child(client, caretaker, settings, child):
    r = client.delete(
        f"/api/v1/admin/children/{child.id}", headers=auth(caretaker, settings)
    )
    assert r.status_code == 403


def test_deleting_an_unknown_child_is_404(client, admin, settings):
    r = client.delete(
        f"/api/v1/admin/children/{uuid.uuid4()}", headers=auth(admin, settings)
    )
    assert r.status_code == 404


# ── deleting staff ──────────────────────────────────────────────────────────


def test_a_staff_member_with_no_activity_can_be_deleted(
    client, admin, settings, caretaker, db_session
):
    r = client.delete(
        f"/api/v1/admin/staff/{caretaker.id}", headers=auth(admin, settings)
    )
    assert r.status_code == 200, r.text
    assert db_session.get(Staff, caretaker.id) is None


def test_a_staff_member_who_ran_sessions_is_refused(
    client, admin, settings, caretaker, child, db_session
):
    """The audit chain names this person as the actor behind graded findings.
    Removing the row leaves those entries pointing at nobody, which is
    exactly the non-repudiation the chain exists to provide."""
    _session_for(db_session, child, caretaker)

    r = client.delete(
        f"/api/v1/admin/staff/{caretaker.id}", headers=auth(admin, settings)
    )
    assert r.status_code == 409
    assert "deactivate" in r.json()["detail"].lower()
    assert db_session.get(Staff, caretaker.id) is not None


def test_an_admin_cannot_delete_themselves(client, admin, settings, db_session):
    """Same anti-lockout rail as role change and deactivation: the last admin
    deleting themselves leaves a system nobody can administer."""
    r = client.delete(f"/api/v1/admin/staff/{admin.id}", headers=auth(admin, settings))
    assert r.status_code == 409
    assert db_session.get(Staff, admin.id) is not None


def test_deleting_staff_unassigns_rather_than_removing_their_children(
    client, admin, settings, caretaker, child, db_session
):
    """ON DELETE SET NULL: losing a staff row must never take a child's
    record with it, and must not leave a dangling reference either."""
    child.assigned_staff_id = caretaker.id
    db_session.flush()

    r = client.delete(
        f"/api/v1/admin/staff/{caretaker.id}", headers=auth(admin, settings)
    )
    assert r.status_code == 200

    db_session.expire(child)
    assert db_session.get(Child, child.id) is not None
    assert child.assigned_staff_id is None


def test_staff_deletion_is_audit_chained(
    client, admin, settings, caretaker, db_session
):
    staff_id = str(caretaker.id)
    client.delete(f"/api/v1/admin/staff/{caretaker.id}", headers=auth(admin, settings))

    entry = db_session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.action == "staff.delete")
        .order_by(AuditLogEntry.sequence.desc())
    ).scalars().first()
    assert entry is not None and entry.resource_id == staff_id


def test_caretaker_cannot_delete_staff(client, caretaker, settings, admin):
    r = client.delete(
        f"/api/v1/admin/staff/{admin.id}", headers=auth(caretaker, settings)
    )
    assert r.status_code == 403


# ── archive from the admin console ──────────────────────────────────────────


def test_admin_can_archive_a_child_with_history(
    client, admin, settings, child, caretaker, db_session
):
    """The safe removal, and the one the refusal above points at. The archive
    control previously existed only on the caretaker's child profile — a page
    the admin console cannot reach."""
    _session_for(db_session, child, caretaker)

    r = client.post(
        f"/api/v1/admin/children/{child.id}/archive",
        headers=auth(admin, settings),
        json={"reason": "Duplicate registration"},
    )
    assert r.status_code == 200, r.text
    db_session.expire(child)
    assert child.archived_at is not None
    assert child.archived_reason == "Duplicate registration"


def test_admin_archive_requires_a_reason(client, admin, settings, child):
    """"Why is this child no longer on the roster" is the question an auditor
    asks, and a blank answer is not an answer."""
    r = client.post(
        f"/api/v1/admin/children/{child.id}/archive",
        headers=auth(admin, settings),
        json={"reason": ""},
    )
    assert r.status_code == 422


def test_admin_can_restore_an_archived_child(
    client, admin, settings, child, db_session
):
    client.post(
        f"/api/v1/admin/children/{child.id}/archive",
        headers=auth(admin, settings),
        json={"reason": "Left the institution"},
    )
    r = client.post(
        f"/api/v1/admin/children/{child.id}/restore", headers=auth(admin, settings)
    )
    assert r.status_code == 200
    db_session.expire(child)
    assert child.archived_at is None


# ── assignment ──────────────────────────────────────────────────────────────


def test_admin_assigns_a_child_to_a_caretaker(
    client, admin, settings, child, caretaker, db_session
):
    r = client.patch(
        f"/api/v1/admin/children/{child.id}/assignment",
        headers=auth(admin, settings),
        json={"staff_id": str(caretaker.id)},
    )
    assert r.status_code == 200, r.text
    db_session.expire(child)
    assert child.assigned_staff_id == caretaker.id


def test_assignment_can_be_cleared(
    client, admin, settings, child, caretaker, db_session
):
    """Unassigned is a legitimate state — a caretaker leaves, a child is
    between carers — not a defect to be prevented."""
    child.assigned_staff_id = caretaker.id
    db_session.flush()

    r = client.patch(
        f"/api/v1/admin/children/{child.id}/assignment",
        headers=auth(admin, settings),
        json={"staff_id": None},
    )
    assert r.status_code == 200
    db_session.expire(child)
    assert child.assigned_staff_id is None


def test_a_child_cannot_be_assigned_across_institutions(
    client, admin, settings, child, db_session
):
    """The assigned carer must actually work where the child lives. A
    cross-institution assignment would be meaningless, and would quietly
    imply a relationship that the tenant boundary forbids."""
    other = Institution(name="Elsewhere", is_synthetic=True)
    db_session.add(other)
    db_session.flush()
    outsider = _staff(db_session, other, "caretaker")

    r = client.patch(
        f"/api/v1/admin/children/{child.id}/assignment",
        headers=auth(admin, settings),
        json={"staff_id": str(outsider.id)},
    )
    assert r.status_code == 409
    db_session.expire(child)
    assert child.assigned_staff_id is None


def test_a_child_cannot_be_assigned_to_a_deactivated_account(
    client, admin, settings, child, caretaker, db_session
):
    caretaker.is_active = False
    db_session.flush()

    r = client.patch(
        f"/api/v1/admin/children/{child.id}/assignment",
        headers=auth(admin, settings),
        json={"staff_id": str(caretaker.id)},
    )
    assert r.status_code == 409


def test_assignment_is_audit_chained(
    client, admin, settings, child, caretaker, db_session
):
    client.patch(
        f"/api/v1/admin/children/{child.id}/assignment",
        headers=auth(admin, settings),
        json={"staff_id": str(caretaker.id)},
    )
    entry = db_session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.action == "child.assign")
        .order_by(AuditLogEntry.sequence.desc())
    ).scalars().first()
    assert entry is not None and entry.resource_id == str(child.id)


def test_caretaker_cannot_assign(client, caretaker, settings, child):
    r = client.patch(
        f"/api/v1/admin/children/{child.id}/assignment",
        headers=auth(caretaker, settings),
        json={"staff_id": str(caretaker.id)},
    )
    assert r.status_code == 403


def test_assignment_does_not_change_who_can_see_the_child(
    client, caretaker, settings, child, db_session, institution
):
    """The scope note in migration 0007, pinned.

    Assignment records responsibility. It must NOT narrow visibility: a child
    whose assigned caretaker is off shift has to stay visible to the
    colleague covering for them. Enforcement is R8 and a separate decision —
    if this test ever fails, that decision was made by accident.
    """
    colleague = _staff(db_session, institution, "caretaker")
    child.assigned_staff_id = colleague.id
    db_session.flush()

    r = client.get("/api/v1/children?page=1&page_size=50", headers=auth(caretaker, settings))
    assert r.status_code == 200
    names = [item["id"] for item in r.json()["data"]["items"]]
    assert str(child.id) in names, "assignment must not hide a child from colleagues"
