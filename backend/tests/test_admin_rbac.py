"""RBAC + Admin Panel — staff management (system-level admin role).

THREAT_MODEL §2 RBAC matrix: the admin role is SYSTEM-LEVEL (NextaSol/dev),
NOT per-institution. Cross-institution visibility exists ONLY on the explicit
admin endpoints; it must never weaken institution scoping on any caretaker-
facing endpoint (regression tests at the bottom pin exactly that).

Ticket test list covered here:
- get_current_admin_staff: 403 for non-admin, 200 for admin
- staff list across institutions, view/change role, soft deactivate/reactivate
- every admin action writes to audit_log
- bootstrap: first admin comes from the seed script, never an open endpoint
- deactivated staff lose the write surface (sessions/observations/transcribe)
- RLS boundary: admin token on caretaker endpoints stays institution-scoped
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


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _institution(db_session, name="Synthetic Institution"):
    from app.models.institution import Institution

    inst = Institution(name=name, is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    return inst


def _staff(db_session, *, institution_id, role="caretaker", is_active=True, email=None):
    from app.models.staff import Staff

    staff_id = uuid.uuid4()
    staff = Staff(
        id=staff_id,
        institution_id=institution_id,
        email=email or f"{staff_id.hex}@signal.example",
        hashed_password="unused-in-phase-1-stub",
        role=role,
        is_active=is_active,
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return staff


def _admin_token(client, settings, rsa_keypair, db_session):
    """Seed a system admin and mint a matching admin token."""
    inst = _institution(db_session, name="Admin Host Institution")
    admin = _staff(db_session, institution_id=inst.id, role="admin")
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=admin.id, role="admin",
    )
    return token, admin


# ── get_current_admin_staff: 403 for non-admin, 200 for admin ──────────────


def test_admin_endpoint_missing_token_401(client):
    assert client.get("/api/v1/admin/staff").status_code == 401


def test_admin_endpoint_caretaker_403(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    resp = client.get("/api/v1/admin/staff", headers=_auth(token))
    assert resp.status_code == 403
    assert "detail" in resp.json() and "data" not in resp.json()


def test_admin_endpoint_admin_200(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    resp = client.get("/api/v1/admin/staff", headers=_auth(token))
    assert resp.status_code == 200, resp.text


def test_admin_jwt_claim_without_staff_row_403(client, settings, rsa_keypair, db_session):
    """Fail closed: a forged-looking admin claim with no DB row gets nothing.
    The DB row is the authority for privilege, not the JWT claim alone."""
    inst = _institution(db_session)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=uuid.uuid4(), role="admin",
    )
    assert client.get("/api/v1/admin/staff", headers=_auth(token)).status_code == 403


def test_admin_jwt_claim_with_caretaker_row_403(client, settings, rsa_keypair, db_session):
    """An 'admin' claim over a caretaker DB row must not elevate — the role
    change endpoint is the only promotion path (plus the seed script)."""
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id, role="caretaker")
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="admin",
    )
    assert client.get("/api/v1/admin/staff", headers=_auth(token)).status_code == 403


def test_deactivated_admin_403(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    admin = _staff(db_session, institution_id=inst.id, role="admin", is_active=False)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=admin.id, role="admin",
    )
    assert client.get("/api/v1/admin/staff", headers=_auth(token)).status_code == 403


# ── Staff list: cross-institution for admin only ────────────────────────────


def test_admin_lists_staff_across_institutions(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    inst_a = _institution(db_session, name="Institution A")
    inst_b = _institution(db_session, name="Institution B")
    staff_a = _staff(db_session, institution_id=inst_a.id)
    staff_b = _staff(db_session, institution_id=inst_b.id)

    resp = client.get("/api/v1/admin/staff", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()["data"]
    by_email = {item["email"]: item for item in body["items"]}
    assert staff_a.email in by_email and staff_b.email in by_email
    # The two seeded rows carry their (different) institutions — proof the
    # view really crosses the tenant boundary.
    assert by_email[staff_a.email]["institution_id"] == str(inst_a.id)
    assert by_email[staff_b.email]["institution_id"] == str(inst_b.id)
    for item in body["items"]:
        assert "role" in item and "is_active" in item
    # Credential material must never surface in any admin view.
    assert "hashed_password" not in resp.text


def test_admin_staff_list_paginated(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    inst = _institution(db_session)
    for _ in range(3):
        _staff(db_session, institution_id=inst.id)

    page = client.get(
        "/api/v1/admin/staff", headers=_auth(token), params={"page": 1, "page_size": 2}
    )
    body = page.json()["data"]
    assert len(body["items"]) == 2
    assert body["total"] >= 4  # 3 caretakers + the admin itself
    # page_size cap is a hard contract (MUST-NOT #7).
    assert (
        client.get(
            "/api/v1/admin/staff", headers=_auth(token), params={"page_size": 101}
        ).status_code
        == 422
    )


def test_admin_staff_detail_shows_role(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)

    resp = client.get(f"/api/v1/admin/staff/{caretaker.id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == str(caretaker.id)
    assert data["role"] == "caretaker"
    assert data["is_active"] is True


def test_admin_staff_detail_unknown_404(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    assert (
        client.get(f"/api/v1/admin/staff/{uuid.uuid4()}", headers=_auth(token)).status_code
        == 404
    )


# ── Role change (promotion/demotion) — audit-logged ─────────────────────────


def test_promote_staff_to_admin_audited(client, settings, rsa_keypair, db_session):
    token, admin = _admin_token(client, settings, rsa_keypair, db_session)
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)

    resp = client.patch(
        f"/api/v1/admin/staff/{caretaker.id}/role",
        headers=_auth(token),
        json={"role": "admin"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["role"] == "admin"

    from app.models.audit_log import AuditLogEntry

    entries = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_id == str(caretaker.id))
        .all()
    )
    assert [e.action for e in entries] == ["staff.role_change"]
    assert entries[0].actor_id == admin.id


def test_demote_admin_to_caretaker(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    inst = _institution(db_session)
    second_admin = _staff(db_session, institution_id=inst.id, role="admin")

    resp = client.patch(
        f"/api/v1/admin/staff/{second_admin.id}/role",
        headers=_auth(token),
        json={"role": "caretaker"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "caretaker"


def test_role_change_validation_422(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)

    resp = client.patch(
        f"/api/v1/admin/staff/{caretaker.id}/role",
        headers=_auth(token),
        json={"role": "superuser"},
    )
    assert resp.status_code == 422


def test_admin_cannot_demote_self(client, settings, rsa_keypair, db_session):
    """Safety rail: self-demotion risks leaving the system with zero admins.
    A second admin must perform the change."""
    token, admin = _admin_token(client, settings, rsa_keypair, db_session)
    resp = client.patch(
        f"/api/v1/admin/staff/{admin.id}/role",
        headers=_auth(token),
        json={"role": "caretaker"},
    )
    assert resp.status_code == 409


# ── Deactivate / reactivate (soft delete — never hard delete) ───────────────


def test_deactivate_reactivate_staff_audited(client, settings, rsa_keypair, db_session):
    token, admin = _admin_token(client, settings, rsa_keypair, db_session)
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)

    off = client.patch(
        f"/api/v1/admin/staff/{caretaker.id}/active",
        headers=_auth(token),
        json={"is_active": False},
    )
    assert off.status_code == 200
    assert off.json()["data"]["is_active"] is False

    on = client.patch(
        f"/api/v1/admin/staff/{caretaker.id}/active",
        headers=_auth(token),
        json={"is_active": True},
    )
    assert on.status_code == 200
    assert on.json()["data"]["is_active"] is True

    from app.models.audit_log import AuditLogEntry

    actions = [
        e.action
        for e in db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_id == str(caretaker.id))
        .order_by(AuditLogEntry.sequence.asc())
        .all()
    ]
    assert actions == ["staff.deactivate", "staff.reactivate"]
    # The row still exists — soft delete never destroys health-adjacent data.
    from app.models.staff import Staff

    assert db_session.get(Staff, caretaker.id) is not None


def test_admin_cannot_deactivate_self(client, settings, rsa_keypair, db_session):
    """Same lockout rail as self-demotion: an admin can always undo the
    change, so self-deactivation only creates confusion — another admin
    must do it."""
    token, admin = _admin_token(client, settings, rsa_keypair, db_session)
    resp = client.patch(
        f"/api/v1/admin/staff/{admin.id}/active",
        headers=_auth(token),
        json={"is_active": False},
    )
    assert resp.status_code == 409


# ── Bootstrap: the first admin is never minted by an open endpoint ──────────


def test_stub_login_mints_db_role_for_seeded_admin(client, db_session):
    """The synthetic stub login is the Phase-1 credential seam: a seeded admin
    row (seed_admin.py) must be able to obtain an admin token. This is the
    bootstrap path's consumer side — the producer is the seed script, NOT an
    open promotion endpoint."""
    inst = _institution(db_session)
    admin = _staff(db_session, institution_id=inst.id, role="admin", email="root@signal.example")

    resp = client.post(
        "/api/v1/auth/token",
        json={"email": "root@signal.example", "password": "synthetic"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]

    from app.core import security

    # Claim check via decode — the token must carry the DB row's identity.
    claims = security.decode_access_token(token, settings=client.app.state.settings)
    assert claims["sub"] == str(admin.id)
    assert claims["role"] == "admin"
    assert claims["institution_id"] == str(inst.id)


def test_stub_login_refuses_deactivated_staff(client, db_session):
    inst = _institution(db_session)
    _staff(
        db_session, institution_id=inst.id, role="caretaker",
        is_active=False, email="gone@signal.example",
    )
    resp = client.post(
        "/api/v1/auth/token",
        json={"email": "gone@signal.example", "password": "synthetic"},
    )
    assert resp.status_code == 403


# ── Deactivation must actually lock the write surface ───────────────────────


def _child(db_session, institution_id):
    from app.models.child import Child

    child = Child(
        institution_id=institution_id,
        name="Seeded Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=False,
        estimated_age_range="24-30 months",
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


def test_deactivated_staff_cannot_open_session(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    child = _child(db_session, inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )

    caretaker.is_active = False
    db_session.flush()

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child.id), "mode": "text"},
    )
    assert resp.status_code == 403


def test_deactivated_staff_cannot_add_observation(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    child = _child(db_session, inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    opened = client.post(
        "/api/v1/sessions",
        headers=_auth(token),
        json={"child_id": str(child.id), "mode": "text"},
    )
    assert opened.status_code == 201
    session_id = opened.json()["data"]["id"]

    caretaker.is_active = False
    db_session.flush()

    resp = client.post(
        f"/api/v1/sessions/{session_id}/observations",
        headers=_auth(token),
        json={"raw_input": "should be refused"},
    )
    assert resp.status_code == 403


def test_deactivated_staff_cannot_transcribe(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    caretaker.is_active = False
    db_session.flush()

    resp = client.post(
        "/api/v1/stt/transcribe",
        headers=_auth(token),
        files={"audio": ("turn.webm", b"\x00\x01fakeaudio", "audio/webm")},
    )
    # 403 account guard fires BEFORE the 503 unconfigured-provider branch.
    assert resp.status_code == 403


# ── RLS boundary regression — the highest-risk part of this ticket ──────────
# Admin cross-institution visibility exists ONLY on the admin endpoints above.
# On every caretaker-facing surface an admin token behaves exactly like any
# other staff token: institution-scoped, uniform 403 across the boundary.


def test_admin_token_stays_institution_scoped_on_session_read(
    client, settings, rsa_keypair, db_session
):
    # Institution B opens a session.
    inst_b = _institution(db_session, name="Institution B")
    caretaker_b = _staff(db_session, institution_id=inst_b.id)
    child_b = _child(db_session, inst_b.id)
    token_b = _mint(
        settings, rsa_keypair,
        institution_id=inst_b.id, staff_id=caretaker_b.id, role="caretaker",
    )
    opened = client.post(
        "/api/v1/sessions",
        headers=_auth(token_b),
        json={"child_id": str(child_b.id), "mode": "text"},
    )
    assert opened.status_code == 201
    session_id = opened.json()["data"]["id"]

    # Admin lives in a different institution — the admin claim must not
    # widen session access there.
    admin_token, _ = _admin_token(client, settings, rsa_keypair, db_session)
    resp = client.get(f"/api/v1/sessions/{session_id}", headers=_auth(admin_token))
    assert resp.status_code == 403


def test_admin_token_cannot_open_session_for_foreign_child(
    client, settings, rsa_keypair, db_session
):
    inst_b = _institution(db_session, name="Institution B")
    child_b = _child(db_session, inst_b.id)
    admin_token, _ = _admin_token(client, settings, rsa_keypair, db_session)

    resp = client.post(
        "/api/v1/sessions",
        headers=_auth(admin_token),
        json={"child_id": str(child_b.id), "mode": "text"},
    )
    assert resp.status_code == 403


def test_admin_token_child_list_stays_own_institution(
    client, settings, rsa_keypair, db_session
):
    inst_b = _institution(db_session, name="Institution B")
    child_b = _child(db_session, inst_b.id)
    admin_token, admin = _admin_token(client, settings, rsa_keypair, db_session)

    resp = client.get("/api/v1/children", headers=_auth(admin_token))
    assert resp.status_code == 200
    ids = {item["id"] for item in resp.json()["data"]["items"]}
    assert str(child_b.id) not in ids


def test_caretaker_cannot_reach_admin_staff_views(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    assert client.get("/api/v1/admin/staff", headers=_auth(token)).status_code == 403
    other = _staff(db_session, institution_id=inst.id)
    assert (
        client.get(f"/api/v1/admin/staff/{other.id}", headers=_auth(token)).status_code == 403
    )
    assert (
        client.patch(
            f"/api/v1/admin/staff/{other.id}/role",
            headers=_auth(token),
            json={"role": "admin"},
        ).status_code
        == 403
    )
