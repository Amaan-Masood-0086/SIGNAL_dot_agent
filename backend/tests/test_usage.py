"""Usage tracking — cost-visibility ledger (RISK_REGISTER cost-DoS mitigation).

Ticket contract under test:
- a call is logged EXACTLY ONCE per actual successful API call (never on
  refused/failed calls — nothing was billed);
- "my usage" shows only the caller's own data, no admin role needed;
- "all usage" requires the admin role and breaks down by staff + institution
  with date-range filtering.

The STT endpoint is hooked today; the LLM hook is the same UsageService seam
(the FEAT-05 reasoning pipeline will call it — no LLM calls exist yet).
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


class FakeProvider:
    language = "ur-PK"

    def transcribe(self, audio: bytes) -> str:
        return "bacha do saal ka hai"


def _with_fake_stt(client):
    from app.api.v1.endpoints.stt import get_stt_provider

    client.app.dependency_overrides[get_stt_provider] = lambda: FakeProvider()


def _seed_usage(db_session, *, staff_id, institution_id, provider="stt",
                call_type="transcribe", cost="0.000100", count=1):
    from decimal import Decimal

    from app.services.usage import UsageService

    service = UsageService(db_session)
    for _ in range(count):
        service.record(
            staff_id=staff_id,
            institution_id=institution_id,
            provider=provider,
            call_type=call_type,
            estimated_cost=Decimal(cost),
        )
    db_session.flush()


# ── Exactly-once logging on the STT hook ─────────────────────────────────────


def test_successful_transcribe_logs_exactly_one_usage_row(
    client, settings, rsa_keypair, db_session
):
    _with_fake_stt(client)
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )

    resp = client.post(
        "/api/v1/stt/transcribe",
        headers=_auth(token),
        files={"audio": ("turn.webm", b"\x00\x01" * 2000, "audio/webm")},
    )
    assert resp.status_code == 200, resp.text

    from app.models.usage_log import UsageLog

    rows = db_session.query(UsageLog).all()
    assert len(rows) == 1  # exactly one — not zero, not twice
    row = rows[0]
    assert row.staff_id == caretaker.id
    assert row.institution_id == inst.id
    assert row.provider == "stt"
    assert row.call_type == "transcribe"
    assert row.estimated_cost is not None and row.estimated_cost > 0
    assert row.timestamp is not None


def test_failed_transcribe_logs_nothing(client, settings, rsa_keypair, db_session):
    """The provider call failed (502) — nothing succeeded, nothing is billed,
    nothing is logged. Exactly-once means once per ACTUAL successful call."""

    class ExplodingProvider:
        language = "ur-PK"

        def transcribe(self, audio: bytes) -> str:
            raise RuntimeError("provider down")

    from app.api.v1.endpoints.stt import get_stt_provider

    client.app.dependency_overrides[get_stt_provider] = lambda: ExplodingProvider()

    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers=_auth(token),
        files={"audio": ("turn.webm", b"\x00\x01", "audio/webm")},
    )
    assert resp.status_code == 502

    from app.models.usage_log import UsageLog

    assert db_session.query(UsageLog).count() == 0


def test_unconfigured_transcribe_logs_nothing(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers=_auth(token),
        files={"audio": ("turn.webm", b"\x00\x01", "audio/webm")},
    )
    assert resp.status_code == 503

    from app.models.usage_log import UsageLog

    assert db_session.query(UsageLog).count() == 0


# ── "My usage" — any staff member, own data only ─────────────────────────────


def test_my_usage_requires_auth_401(client):
    assert client.get("/api/v1/usage/me").status_code == 401


def test_my_usage_shows_only_callers_own_data(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    me = _staff(db_session, institution_id=inst.id)
    colleague = _staff(db_session, institution_id=inst.id)
    _seed_usage(db_session, staff_id=me.id, institution_id=inst.id, count=2)
    _seed_usage(db_session, staff_id=colleague.id, institution_id=inst.id, count=5)

    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=me.id, role="caretaker",
    )
    resp = client.get("/api/v1/usage/me", headers=_auth(token))
    assert resp.status_code == 200, resp.text  # no admin role needed
    data = resp.json()["data"]
    assert data["staff_id"] == str(me.id)
    assert data["total"]["calls"] == 2
    assert data["total"]["estimated_cost"] == pytest.approx(0.0002)
    assert data["by_provider"]["stt"]["calls"] == 2
    assert data["by_provider"]["llm"]["calls"] == 0


def test_my_usage_empty_is_zero_not_error(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    me = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=me.id, role="caretaker",
    )
    resp = client.get("/api/v1/usage/me", headers=_auth(token))
    data = resp.json()["data"]
    assert data["total"]["calls"] == 0
    assert data["total"]["estimated_cost"] in (0, 0.0, None)


# ── "All usage" — admin-only breakdown ──────────────────────────────────────


def test_all_usage_caretaker_403(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    caretaker = _staff(db_session, institution_id=inst.id)
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=caretaker.id, role="caretaker",
    )
    assert client.get("/api/v1/admin/usage", headers=_auth(token)).status_code == 403


def test_all_usage_admin_breakdown(client, settings, rsa_keypair, db_session):
    # Two institutions, three staff members with different usage.
    inst_a = _institution(db_session, name="Institution A")
    inst_b = _institution(db_session, name="Institution B")
    admin = _staff(db_session, institution_id=inst_a.id, role="admin")
    worker_a = _staff(db_session, institution_id=inst_a.id)
    worker_b = _staff(db_session, institution_id=inst_b.id)
    _seed_usage(db_session, staff_id=admin.id, institution_id=inst_a.id, count=1)
    _seed_usage(db_session, staff_id=worker_a.id, institution_id=inst_a.id, count=2)
    _seed_usage(db_session, staff_id=worker_b.id, institution_id=inst_b.id, count=4)

    token = _mint(
        settings, rsa_keypair,
        institution_id=inst_a.id, staff_id=admin.id, role="admin",
    )
    resp = client.get("/api/v1/admin/usage", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert data["total"]["calls"] == 7

    by_staff = {item["staff_id"]: item for item in data["by_staff"]}
    assert by_staff[str(worker_b.id)]["calls"] == 4
    assert by_staff[str(worker_b.id)]["email"] == worker_b.email
    assert by_staff[str(worker_a.id)]["institution_id"] == str(inst_a.id)

    by_inst = {item["institution_id"]: item for item in data["by_institution"]}
    assert by_inst[str(inst_a.id)]["calls"] == 3
    assert by_inst[str(inst_a.id)]["name"] == "Institution A"
    assert by_inst[str(inst_b.id)]["calls"] == 4


def test_all_usage_date_range_filter(client, settings, rsa_keypair, db_session):
    inst = _institution(db_session)
    admin = _staff(db_session, institution_id=inst.id, role="admin")
    _seed_usage(db_session, staff_id=admin.id, institution_id=inst.id, count=3)

    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=admin.id, role="admin",
    )
    # Window ending far in the past excludes everything…
    empty = client.get(
        "/api/v1/admin/usage",
        headers=_auth(token),
        params={"end": "2020-01-01T00:00:00Z"},
    )
    assert empty.json()["data"]["total"]["calls"] == 0
    assert empty.json()["data"]["by_staff"] == []

    # …and a generous window keeps it all.
    full = client.get(
        "/api/v1/admin/usage",
        headers=_auth(token),
        params={"start": "2020-01-01T00:00:00Z", "end": "2100-01-01T00:00:00Z"},
    )
    assert full.json()["data"]["total"]["calls"] == 3
