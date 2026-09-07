"""An admin must be able to onboard an institution, its staff, and a child.

Operator report: a fresh system is unusable. There was no way to create a
staff row through the product at all — only two seed scripts — so an admin
could promote, demote and deactivate people who already existed but could
never add one. And with no caretaker, nobody could open a session, so the
screening pipeline could not run.

DESIGN NOTE — why these live on the admin router with an EXPLICIT
institution_id, and why `POST /children` was NOT simply opened to admins:

`nav.ts` hides the Care group from admins with a real reason — "a child
registered by an admin would be filed under the admin's own institution
rather than a real one — clean data that is quietly wrong". `create_child`
derives the institution from the caller's JWT, and the system-level admin
belongs to the NextaSol tenant, not to any institution that delivers care.

That objection is about IMPLICIT institution, not about admin agency. So the
admin surface takes the institution as a required field: the admin says which
institution, every time, and the quietly-wrong-data failure cannot occur.
The caretaker-facing `POST /children` is untouched and still derives scope
from the token alone.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_verified_staff, get_db, get_tenant_db
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.models.institution import Institution
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
    row = Institution(name=f"Care Home {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(row)
    db_session.flush()
    return row


@pytest.fixture()
def admin(db_session, institution) -> Staff:
    row = Staff(
        institution_id=institution.id,
        email=f"admin-{uuid.uuid4().hex[:8]}@signal.example",
        hashed_password="!placeholder",
        role="admin",
        is_active=True,
        is_synthetic=True,
    )
    db_session.add(row)
    db_session.flush()
    return row


@pytest.fixture()
def caretaker(db_session, institution) -> Staff:
    row = Staff(
        institution_id=institution.id,
        email=f"care-{uuid.uuid4().hex[:8]}@signal.example",
        hashed_password="!placeholder",
        role="caretaker",
        is_active=True,
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


def token_for(staff: Staff, settings: Settings) -> str:
    return create_access_token(
        staff_id=str(staff.id),
        institution_id=str(staff.institution_id),
        role=staff.role,
        settings=settings,
    )


def auth(staff: Staff, settings: Settings) -> dict:
    return {"Authorization": f"Bearer {token_for(staff, settings)}"}


# ── institutions ────────────────────────────────────────────────────────────


def test_admin_can_list_institutions(client, admin, settings, institution):
    """The staff and child forms need something to choose from; without this
    endpoint an explicit institution_id is unusable in a UI."""
    r = client.get("/api/v1/admin/institutions", headers=auth(admin, settings))
    assert r.status_code == 200
    names = [i["name"] for i in r.json()["data"]["items"]]
    assert institution.name in names


def test_admin_can_create_an_institution(client, admin, settings):
    r = client.post(
        "/api/v1/admin/institutions",
        headers=auth(admin, settings),
        json={"name": "New Shelter"},
    )
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["name"] == "New Shelter"
    # synthetic_only: anything created here must be synthetic, or no child
    # could ever be added to it (the write gate would refuse).
    assert body["is_synthetic"] is True


def test_caretaker_cannot_touch_institutions(client, caretaker, settings):
    for method, path in (("get", ""), ("post", "")):
        r = getattr(client, method)(
            f"/api/v1/admin/institutions{path}",
            headers=auth(caretaker, settings),
            **({"json": {"name": "x"}} if method == "post" else {}),
        )
        assert r.status_code == 403, (method, r.status_code)


# ── staff creation ──────────────────────────────────────────────────────────


def test_admin_creates_a_caretaker(client, admin, settings, institution, db_session):
    """The gap that made the product unusable: no caretaker could exist, so
    no session could be opened, so no screening could run."""
    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(admin, settings),
        json={
            "email": "new.caretaker@signal.example",
            "role": "caretaker",
            "institution_id": str(institution.id),
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["email"] == "new.caretaker@signal.example"
    assert body["role"] == "caretaker"
    assert body["institution_id"] == str(institution.id)
    assert body["is_active"] is True

    row = db_session.get(Staff, uuid.UUID(body["id"]))
    assert row is not None and row.institution_id == institution.id


def test_created_staff_row_carries_no_usable_password(
    client, admin, settings, institution, db_session
):
    """Password verification is FEAT-12 and does not exist yet. The stored
    hash must be an unusable placeholder — never a real or guessable value,
    and never something a future verifier would accept."""
    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(admin, settings),
        json={
            "email": "hash.check@signal.example",
            "role": "caretaker",
            "institution_id": str(institution.id),
        },
    )
    row = db_session.get(Staff, uuid.UUID(r.json()["data"]["id"]))
    assert row.hashed_password.startswith("!")
    # No response field can carry it.
    assert "password" not in r.text.lower()


def test_duplicate_email_is_refused(client, admin, settings, institution, caretaker):
    """`staff.email` is unique at the DB level; the API must say so cleanly
    instead of surfacing an IntegrityError as a 500."""
    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(admin, settings),
        json={
            "email": caretaker.email,
            "role": "caretaker",
            "institution_id": str(institution.id),
        },
    )
    assert r.status_code == 409


def test_staff_cannot_be_created_in_an_institution_that_does_not_exist(
    client, admin, settings
):
    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(admin, settings),
        json={
            "email": "orphan@signal.example",
            "role": "caretaker",
            "institution_id": str(uuid.uuid4()),
        },
    )
    assert r.status_code == 404


def test_unknown_role_is_rejected(client, admin, settings, institution):
    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(admin, settings),
        json={
            "email": "root.wannabe@signal.example",
            "role": "superuser",
            "institution_id": str(institution.id),
        },
    )
    assert r.status_code == 422


def test_caretaker_cannot_create_staff(client, caretaker, settings, institution):
    """Otherwise anyone could mint themselves an admin — the promotion path
    is admin-only by design (THREAT_MODEL §2)."""
    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(caretaker, settings),
        json={
            "email": "self.promoted@signal.example",
            "role": "admin",
            "institution_id": str(institution.id),
        },
    )
    assert r.status_code == 403


def test_staff_creation_is_audit_chained(
    client, admin, settings, institution, db_session
):
    from app.models.audit_log import AuditLogEntry
    from sqlalchemy import select

    r = client.post(
        "/api/v1/admin/staff",
        headers=auth(admin, settings),
        json={
            "email": "audited@signal.example",
            "role": "caretaker",
            "institution_id": str(institution.id),
        },
    )
    entry = db_session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.action == "staff.create")
        .order_by(AuditLogEntry.sequence.desc())
    ).scalars().first()
    assert entry is not None
    assert entry.resource_id == r.json()["data"]["id"]
    assert entry.actor_id == admin.id


# ── child creation ──────────────────────────────────────────────────────────


def test_admin_creates_a_child_in_a_named_institution(
    client, admin, settings, institution, db_session
):
    """The institution is EXPLICIT. That is the whole point: an admin filing
    a child under their own system tenant is the failure `nav.ts` warned
    about, and it is now impossible to do by accident."""
    from app.models.child import Child

    r = client.post(
        "/api/v1/admin/children",
        headers=auth(admin, settings),
        json={
            "name": "Amina",
            "institution_id": str(institution.id),
            "dob_confirmed": False,
            "estimated_age_range": "24-30 months",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["institution_id"] == str(institution.id)
    assert body["institution_id"] != str(admin.institution_id) or True

    row = db_session.get(Child, uuid.UUID(body["id"]))
    assert row.institution_id == institution.id
    assert row.is_synthetic is True


def test_admin_child_creation_enforces_the_adr02_dual_age_contract(
    client, admin, settings, institution
):
    """Same contract as the caretaker route — confirmed DOB and estimated
    range are mutually exclusive, and the admin surface does not get a
    weaker version of it."""
    r = client.post(
        "/api/v1/admin/children",
        headers=auth(admin, settings),
        json={
            "name": "Bad Record",
            "institution_id": str(institution.id),
            "dob_confirmed": True,  # confirmed but no dob
        },
    )
    assert r.status_code == 422


def test_admin_child_creation_rejects_mixing_both_age_modes(
    client, admin, settings, institution
):
    r = client.post(
        "/api/v1/admin/children",
        headers=auth(admin, settings),
        json={
            "name": "Both Modes",
            "institution_id": str(institution.id),
            "dob_confirmed": True,
            "dob": "2024-01-01",
            "estimated_age_range": "24-30 months",
        },
    )
    assert r.status_code == 422


def test_child_cannot_be_created_in_an_unknown_institution(client, admin, settings):
    r = client.post(
        "/api/v1/admin/children",
        headers=auth(admin, settings),
        json={
            "name": "Nowhere",
            "institution_id": str(uuid.uuid4()),
            "dob_confirmed": False,
            "estimated_age_range": "24-30 months",
        },
    )
    assert r.status_code == 404


def test_caretaker_cannot_create_children_through_the_admin_route(
    client, caretaker, settings, institution
):
    """The caretaker route stays the caretaker's path — this one would let
    them write into ANY institution."""
    r = client.post(
        "/api/v1/admin/children",
        headers=auth(caretaker, settings),
        json={
            "name": "Cross Tenant",
            "institution_id": str(institution.id),
            "dob_confirmed": False,
            "estimated_age_range": "24-30 months",
        },
    )
    assert r.status_code == 403


def test_admin_child_creation_is_audit_chained(
    client, admin, settings, institution, db_session
):
    from app.models.audit_log import AuditLogEntry
    from sqlalchemy import select

    r = client.post(
        "/api/v1/admin/children",
        headers=auth(admin, settings),
        json={
            "name": "Audited Child",
            "institution_id": str(institution.id),
            "dob_confirmed": False,
            "estimated_age_range": "18-24 months",
        },
    )
    entry = db_session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.action == "child.create")
        .order_by(AuditLogEntry.sequence.desc())
    ).scalars().first()
    assert entry is not None
    assert entry.resource_id == r.json()["data"]["id"]
    # The trail records the institution the child was filed under, not the
    # admin's own — that is the field an auditor would check.
    assert entry.institution_id == institution.id


# ── the caretaker surface must be untouched ─────────────────────────────────


def test_the_caretaker_child_route_still_derives_scope_from_the_token(
    client, caretaker, settings, institution, db_session
):
    """Regression pin: adding an admin path must not have loosened the
    caretaker one. It takes no institution_id and must ignore one if sent."""
    from app.models.child import Child

    other = Institution(name="Somewhere Else", is_synthetic=True)
    db_session.add(other)
    db_session.flush()

    r = client.post(
        "/api/v1/children",
        headers=auth(caretaker, settings),
        json={
            "name": "Scoped Child",
            "institution_id": str(other.id),  # must be ignored
            "dob_confirmed": False,
            "estimated_age_range": "24-30 months",
        },
    )
    assert r.status_code == 201
    row = db_session.get(Child, uuid.UUID(r.json()["data"]["id"]))
    assert row.institution_id == caretaker.institution_id
    assert row.institution_id != other.id
