"""Admin usage must separate the two vendors (operator-reported).

STT and the LLM are different companies with different invoices. The admin
console showed one merged "9 calls · $0.0151", which cannot be reconciled
against either bill — the operator asked, correctly, which provider it was
even counting.

The `UsageByProvider` schema already existed for the caretaker's own
/usage/me view; the admin endpoint simply never surfaced it.
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


def _admin(db_session, settings, rsa_keypair):
    from app.core import security
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name=f"Usage {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="admin", is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    private_pem, _ = rsa_keypair
    token = security.create_access_token(
        staff_id=str(staff.id), institution_id=str(inst.id), role="admin",
        private_key_pem=private_pem, expires_minutes=15, settings=settings,
    )
    return inst, staff, token


def _usage(db_session, inst_id, staff_id, provider, call_type, cost):
    from decimal import Decimal

    from app.models.usage_log import UsageLog

    db_session.add(
        UsageLog(
            id=uuid.uuid4(), staff_id=staff_id, institution_id=inst_id,
            provider=provider, call_type=call_type,
            estimated_cost=Decimal(str(cost)),
        )
    )
    db_session.flush()


def test_usage_is_split_by_vendor(client, settings, rsa_keypair, db_session):
    inst, staff, token = _admin(db_session, settings, rsa_keypair)
    # Two vendors, deliberately different costs so a merged total cannot
    # accidentally satisfy the assertions below.
    _usage(db_session, inst.id, staff.id, "llm", "risk_reasoning", "0.0100")
    _usage(db_session, inst.id, staff.id, "llm", "observation", "0.0030")
    _usage(db_session, inst.id, staff.id, "stt", "transcribe", "0.0002")

    data = client.get(
        "/api/v1/admin/usage", headers={"Authorization": f"Bearer {token}"}
    ).json()["data"]

    assert data["by_provider"]["llm"]["calls"] == 2
    assert data["by_provider"]["stt"]["calls"] == 1
    assert data["by_provider"]["llm"]["estimated_cost"] == pytest.approx(0.0130)
    assert data["by_provider"]["stt"]["estimated_cost"] == pytest.approx(0.0002)


def test_split_still_reconciles_to_the_total(client, settings, rsa_keypair, db_session):
    """The two halves must add up — otherwise the split is just a third number."""
    inst, staff, token = _admin(db_session, settings, rsa_keypair)
    _usage(db_session, inst.id, staff.id, "llm", "explanation", "0.0007")
    _usage(db_session, inst.id, staff.id, "stt", "transcribe", "0.0003")

    data = client.get(
        "/api/v1/admin/usage", headers={"Authorization": f"Bearer {token}"}
    ).json()["data"]

    assert (
        data["by_provider"]["llm"]["calls"] + data["by_provider"]["stt"]["calls"]
        == data["total"]["calls"]
    )
    assert data["by_provider"]["llm"]["estimated_cost"] + data["by_provider"]["stt"][
        "estimated_cost"
    ] == pytest.approx(data["total"]["estimated_cost"])


def test_a_vendor_with_no_calls_reports_zero_not_absent(
    client, settings, rsa_keypair, db_session
):
    """With STT unconfigured the key must still be present and zero — a
    missing key would render as blank rather than 'nothing spent here'."""
    inst, staff, token = _admin(db_session, settings, rsa_keypair)
    _usage(db_session, inst.id, staff.id, "llm", "observation", "0.0011")

    data = client.get(
        "/api/v1/admin/usage", headers={"Authorization": f"Bearer {token}"}
    ).json()["data"]

    assert data["by_provider"]["stt"]["calls"] == 0
    assert data["by_provider"]["stt"]["estimated_cost"] == 0.0


def test_provider_test_connection_lands_in_the_ledger(
    client, settings, rsa_keypair, db_session, monkeypatch
):
    """A test connection is a real provider call, and for the LLM a billed one.

    It was audit-logged but never written to usage_log, so the page whose only
    job is cost visibility under-reported actual billed calls.
    """
    import httpx

    inst, staff, token = _admin(db_session, settings, rsa_keypair)
    settings.LLM_PROVIDER = "openai_compatible"
    settings.LLM_API_KEY = "SENTINEL-not-a-real-key"

    monkeypatch.setattr(
        "app.services.provider_checks.httpx.post",
        lambda url, **kw: httpx.Response(
            200, request=httpx.Request("POST", url), content=b"{}"
        ),
    )

    resp = client.post(
        "/api/v1/admin/providers/llm/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text

    data = client.get(
        "/api/v1/admin/usage", headers={"Authorization": f"Bearer {token}"}
    ).json()["data"]
    assert data["by_provider"]["llm"]["calls"] == 1, "the billed test call was not counted"


def test_unconfigured_provider_test_records_nothing(
    client, settings, rsa_keypair, db_session
):
    """No call left the process, so there is nothing to account for.
    Counting it would inflate the ledger with calls that never happened."""
    inst, staff, token = _admin(db_session, settings, rsa_keypair)
    settings.LLM_PROVIDER = "none"
    settings.LLM_API_KEY = None

    client.post(
        "/api/v1/admin/providers/llm/test",
        headers={"Authorization": f"Bearer {token}"},
    )

    data = client.get(
        "/api/v1/admin/usage", headers={"Authorization": f"Bearer {token}"}
    ).json()["data"]
    assert data["by_provider"]["llm"]["calls"] == 0


def test_llm_test_cost_is_null_not_invented(
    client, settings, rsa_keypair, db_session, monkeypatch
):
    """The token usage of the ping is not parsed on this path, so the cost is
    honestly unknown. A fabricated figure in a money column is worse than a
    blank one — the call still shows up in the count."""
    import httpx
    from sqlalchemy import select

    from app.models.usage_log import UsageLog

    inst, staff, token = _admin(db_session, settings, rsa_keypair)
    settings.LLM_PROVIDER = "openai_compatible"
    settings.LLM_API_KEY = "SENTINEL-not-a-real-key"
    monkeypatch.setattr(
        "app.services.provider_checks.httpx.post",
        lambda url, **kw: httpx.Response(
            200, request=httpx.Request("POST", url), content=b"{}"
        ),
    )

    client.post(
        "/api/v1/admin/providers/llm/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    row = db_session.execute(
        select(UsageLog).where(UsageLog.call_type == "test_connection")
    ).scalars().first()
    assert row is not None
    assert row.estimated_cost is None
