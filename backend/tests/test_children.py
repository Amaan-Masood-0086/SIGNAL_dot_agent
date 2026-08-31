"""FEAT-02 — Child Profile & Estimated-Age Intake.

ADR-02: the confirmed-DOB-vs-estimated-range dual field is a server-side
contract, never a UI-only nicety. TRD §4: GET /children/{id} is
IDOR-sensitive (T1 mandatory), Pydantic validation on every route, and all
responses use the canonical envelope.

All tests run against real PostgreSQL (conftest.py::pg_engine).
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
    from app.api.deps import get_db
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app(settings)
    # Endpoint DB session is the transaction-isolated test session.
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def _mint_token(settings, rsa_keypair, *, institution_id, role="caretaker"):
    private_pem, _ = rsa_keypair
    from app.core import security

    staff_id = uuid.uuid4()
    token = security.create_access_token(
        staff_id=str(staff_id),
        institution_id=str(institution_id),
        role=role,
        private_key_pem=private_pem,
        expires_minutes=15,
        settings=settings,
    )
    return token, staff_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_institution(db_session, *, name="Synthetic Institution"):
    from app.models.institution import Institution

    inst = Institution(name=name, is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    return inst


def _seed_child(db_session, *, institution_id, name="Seeded Child"):
    from app.models.child import Child

    child = Child(
        institution_id=institution_id,
        name=name,
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=False,
        estimated_age_range="24-30 months",
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


# ── Intake: ADR-02 dual-age contract ────────────────────────────────────────


def test_intake_confirmed_dob_stores_adr02_fields(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)

    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={
            "name": "Child Confirmed",
            "intake_date": "2026-08-20",
            "dob_confirmed": True,
            "dob": "2023-05-14",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["name"] == "Child Confirmed"
    assert data["dob_confirmed"] is True
    assert data["dob"] == "2023-05-14"
    # Confirmed mode: estimated fields MUST stay empty (ADR-02).
    assert data["estimated_age_range"] is None
    assert data["estimated_age_note"] is None
    assert data["institution_id"] == str(inst.id)
    assert data["is_synthetic"] is True


def test_intake_estimated_age_stores_range(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)

    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={
            "name": "Child Estimated",
            "intake_date": "2026-08-20",
            "dob_confirmed": False,
            "estimated_age_range": "30-36 months",
            "estimated_age_note": "intake worker estimate",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["dob_confirmed"] is False
    # Estimated mode: dob MUST stay NULL (ADR-02).
    assert data["dob"] is None
    assert data["estimated_age_range"] == "30-36 months"
    assert data["estimated_age_note"] == "intake worker estimate"


def test_intake_confirmed_without_dob_rejected_422(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={"name": "X", "dob_confirmed": True},
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_intake_estimated_without_range_rejected_422(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={"name": "X", "dob_confirmed": False},
    )
    assert resp.status_code == 422


def test_intake_confirmed_rejects_estimated_fields_422(client, settings, rsa_keypair, db_session):
    """Mixed-mode intake is a data-integrity violation (ADR-02)."""
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={
            "name": "X",
            "dob_confirmed": True,
            "dob": "2023-05-14",
            "estimated_age_range": "30-36 months",
        },
    )
    assert resp.status_code == 422


def test_intake_estimated_rejects_dob_422(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={"name": "X", "dob_confirmed": False, "dob": "2023-05-14",
              "estimated_age_range": "30-36 months"},
    )
    assert resp.status_code == 422


def test_intake_missing_name_rejected_422(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={"dob_confirmed": True, "dob": "2023-05-14"},
    )
    assert resp.status_code == 422


def test_intake_date_defaults_to_server_today(client, settings, rsa_keypair, db_session):
    """Server-derived default — never a client-supplied timestamp assumption."""
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={"name": "X", "dob_confirmed": True, "dob": "2023-05-14"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["intake_date"] == datetime.date.today().isoformat()


# ── Profile read: IDOR T1 (TRD §4) ──────────────────────────────────────────


def test_get_child_own_institution_returns_profile(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    child = _seed_child(db_session, institution_id=inst.id)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)

    resp = client.get(f"/api/v1/children/{child.id}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == str(child.id)
    assert data["dob_confirmed"] is False
    assert data["estimated_age_range"] == "24-30 months"


def test_get_child_cross_institution_403(client, settings, rsa_keypair, db_session):
    """IDOR T1: institution A staff must never read institution B's child."""
    inst_b = _seed_institution(db_session, name="Institution B")
    child = _seed_child(db_session, institution_id=inst_b.id)
    inst_a = _seed_institution(db_session, name="Institution A")
    foreign_token, _ = _mint_token(settings, rsa_keypair, institution_id=inst_a.id)

    resp = client.get(f"/api/v1/children/{child.id}", headers=_auth(foreign_token))
    assert resp.status_code == 403
    body = resp.json()
    # No data leakage in the error response (T2 companion).
    assert "detail" in body and "data" not in body


def test_get_unknown_child_403_not_404(client, settings, rsa_keypair, db_session):
    """404 would leak existence across the tenant boundary — stay at 403."""
    inst = _seed_institution(db_session)
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    resp = client.get(f"/api/v1/children/{uuid.uuid4()}", headers=_auth(token))
    assert resp.status_code == 403


def test_children_endpoints_require_auth_401(client):
    assert client.post("/api/v1/children", json={"name": "X"}).status_code == 401
    assert client.get(f"/api/v1/children/{uuid.uuid4()}").status_code == 401


# ── List: institution-scoped roster for the dashboard ──────────────────────


def test_list_children_returns_own_institution_only(client, settings, rsa_keypair, db_session):
    """The dashboard roster must never leak cross-tenant children (IDOR)."""
    inst_a = _seed_institution(db_session, name="Institution A")
    inst_b = _seed_institution(db_session, name="Institution B")
    child_a1 = _seed_child(db_session, institution_id=inst_a.id, name="A One")
    child_a2 = _seed_child(db_session, institution_id=inst_a.id, name="A Two")
    _seed_child(db_session, institution_id=inst_b.id, name="B One")
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst_a.id)

    resp = client.get("/api/v1/children", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    page = body["data"]
    assert page["total"] == 2
    names = {item["name"] for item in page["items"]}
    assert names == {"A One", "A Two"}
    assert {item["id"] for item in page["items"]} == {str(child_a1.id), str(child_a2.id)}
    # Every row carries the caller's tenant — never another institution.
    assert all(item["institution_id"] == str(inst_a.id) for item in page["items"])


def test_list_children_paginates(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    for index in range(3):
        _seed_child(db_session, institution_id=inst.id, name=f"Child {index}")
    token, _ = _mint_token(settings, rsa_keypair, institution_id=inst.id)

    resp = client.get("/api/v1/children?page=2&page_size=2", headers=_auth(token))
    assert resp.status_code == 200
    page = resp.json()["data"]
    assert page["total"] == 3
    assert page["page"] == 2
    assert page["page_size"] == 2
    assert len(page["items"]) == 1


def test_list_children_requires_auth_401(client):
    assert client.get("/api/v1/children").status_code == 401


# ── Non-repudiation: intake writes are audit-chained ────────────────────────


def test_child_creation_is_audit_logged(client, settings, rsa_keypair, db_session):
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)

    resp = client.post(
        "/api/v1/children",
        headers=_auth(token),
        json={"name": "Audited Child", "dob_confirmed": True, "dob": "2023-05-14"},
    )
    assert resp.status_code == 201, resp.text
    child_id = resp.json()["data"]["id"]

    from app.models.audit_log import AuditLogEntry

    # .one() asserts exactly one row was written for this resource.
    entry = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_id == child_id)
        .one()
    )
    assert entry.action == "child.create"
    assert entry.resource_type == "child"
    assert entry.institution_id == inst.id
    # Non-repudiation: actor_id MUST be the JWT's staff identity, never
    # client-supplied input.
    assert entry.actor_id == staff_id
