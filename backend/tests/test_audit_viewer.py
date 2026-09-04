"""Admin Panel — audit log viewer (TRD §4: GET /audit_log, admin-only).

The audit log is the product's liability-protection core (THREAT_MODEL §1
Tampering): the viewer is READ-ONLY, paginated, filterable by actor/action/
date range, and exposes the hash-chain integrity check so an admin sees
"chain intact" — or exactly where it broke.
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


def _staff(db_session, *, institution_id, role="caretaker"):
    from app.models.staff import Staff

    staff_id = uuid.uuid4()
    staff = Staff(
        id=staff_id,
        institution_id=institution_id,
        email=f"{staff_id.hex}@signal.example",
        hashed_password="unused-in-phase-1-stub",
        role=role,
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return staff


def _admin_token(settings, rsa_keypair, db_session):
    inst = _institution(db_session, name="Admin Host")
    admin = _staff(db_session, institution_id=inst.id, role="admin")
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=admin.id, role="admin",
    )
    return token, admin


def _seed_audit_entries(db_session, *, count=5, action="session.create", actor_id=None):
    """Append `count` chained entries straight through the AuditService —
    the same code path the endpoints use."""
    from app.services.audit import AuditService

    service = AuditService(db_session)
    entries = []
    for _ in range(count):
        entries.append(
            service.append(
                actor_id=str(actor_id) if actor_id else None,
                action=action,
                resource_type="session",
                resource_id=str(uuid.uuid4()),
            )
        )
    db_session.flush()
    return entries


# ── Access control: admin-only regardless of institution (TRD §4) ───────────


def test_audit_log_requires_auth_401(client):
    assert client.get("/api/v1/audit_log").status_code == 401
    assert client.get("/api/v1/audit_log/integrity").status_code == 401


def test_audit_log_caretaker_403(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    assert client.get("/api/v1/audit_log", headers=_auth(token)).status_code == 403
    assert (
        client.get("/api/v1/audit_log/integrity", headers=_auth(token)).status_code
        == 403
    )


def test_audit_log_admin_200(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    assert client.get("/api/v1/audit_log", headers=_auth(token)).status_code == 200


# ── Content + pagination (read-only viewer) ─────────────────────────────────


def test_audit_log_lists_entries_newest_first(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    entries = _seed_audit_entries(db_session, count=3)

    resp = client.get("/api/v1/audit_log", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 3
    sequences = [item["sequence"] for item in body["items"]]
    assert sequences == sorted(sequences, reverse=True)
    assert sequences[0] == entries[-1].sequence

    item = body["items"][0]
    for key in (
        "sequence", "actor_id", "institution_id", "action",
        "resource_type", "resource_id", "timestamp", "hash_prev", "hash_self",
    ):
        assert key in item


def test_audit_log_pagination(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    _seed_audit_entries(db_session, count=5)

    page = client.get(
        "/api/v1/audit_log", headers=_auth(token), params={"page": 2, "page_size": 2}
    )
    body = page.json()["data"]
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["page"] == 2

    # page_size cap (MUST-NOT #7).
    assert (
        client.get(
            "/api/v1/audit_log", headers=_auth(token), params={"page_size": 101}
        ).status_code
        == 422
    )


# ── Filters: actor / action / date range ────────────────────────────────────


def test_audit_log_filter_by_action(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    _seed_audit_entries(db_session, count=2, action="session.create")
    _seed_audit_entries(db_session, count=3, action="observation.create")

    resp = client.get(
        "/api/v1/audit_log", headers=_auth(token), params={"action": "observation.create"}
    )
    body = resp.json()["data"]
    assert body["total"] == 3
    assert {item["action"] for item in body["items"]} == {"observation.create"}


def test_audit_log_filter_by_actor(client, settings, rsa_keypair, db_session):
    token, admin = _admin_token(settings, rsa_keypair, db_session)
    other = uuid.uuid4()
    _seed_audit_entries(db_session, count=2, actor_id=admin.id)
    _seed_audit_entries(db_session, count=3, actor_id=other)

    resp = client.get(
        "/api/v1/audit_log", headers=_auth(token), params={"actor_id": str(other)}
    )
    body = resp.json()["data"]
    assert body["total"] == 3
    assert {item["actor_id"] for item in body["items"]} == {str(other)}


def test_audit_log_filter_by_date_range(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    _seed_audit_entries(db_session, count=3)

    # A window ending far in the past excludes everything…
    empty = client.get(
        "/api/v1/audit_log",
        headers=_auth(token),
        params={"end": "2020-01-01T00:00:00Z"},
    )
    assert empty.json()["data"]["total"] == 0

    # …while a generous window keeps everything.
    full = client.get(
        "/api/v1/audit_log",
        headers=_auth(token),
        params={"start": "2020-01-01T00:00:00Z", "end": "2100-01-01T00:00:00Z"},
    )
    assert full.json()["data"]["total"] == 3


# ── Hash-chain integrity: "chain intact" or a precise break alert ───────────


def test_integrity_reports_intact_chain(client, settings, rsa_keypair, db_session):
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    _seed_audit_entries(db_session, count=4)

    resp = client.get("/api/v1/audit_log/integrity", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["chain_intact"] is True
    assert data["entries_checked"] == 4
    assert data["first_broken_sequence"] is None


def test_integrity_detects_tamper(client, settings, rsa_keypair, db_session):
    """Edit a historical row directly (superuser-only in tests; the app role
    has UPDATE revoked) — the viewer must alert on the exact break point."""
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    entries = _seed_audit_entries(db_session, count=4)
    target = entries[1]

    from sqlalchemy import update

    from app.models.audit_log import AuditLogEntry

    db_session.execute(
        update(AuditLogEntry)
        .where(AuditLogEntry.id == target.id)
        .values(action="tampered.action")
    )
    db_session.flush()

    resp = client.get("/api/v1/audit_log/integrity", headers=_auth(token))
    data = resp.json()["data"]
    assert data["chain_intact"] is False
    assert data["first_broken_sequence"] == target.sequence


def test_audit_viewer_is_read_only(client, settings, rsa_keypair, db_session):
    """No write surface exists on the viewer — POST/PATCH/DELETE are 405."""
    token, _ = _admin_token(settings, rsa_keypair, db_session)
    assert client.post("/api/v1/audit_log", headers=_auth(token), json={}).status_code == 405
    assert (
        client.delete("/api/v1/audit_log", headers=_auth(token)).status_code == 405
    )
