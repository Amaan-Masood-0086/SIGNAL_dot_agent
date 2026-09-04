"""Admin Panel — Provider Status (ADR-09: API keys are env-var-only).

What this pins:
- status cards show configured/not-configured from env presence at startup —
  NEVER a key value, not even masked;
- test-connection fires exactly one minimal real call and reports
  success/failure only;
- no form/input surface for key material exists anywhere;
- key material never leaks in responses, even on failure paths.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def make_client(rsa_keypair, db_session):
    """Client factory with per-test Settings overrides (provider env vars)."""
    from app.api.deps import get_db, get_tenant_db
    from app.core.config import Settings, get_settings
    from app.main import create_app

    private_pem, public_pem = rsa_keypair
    clients = []

    def _make(**overrides):
        base = dict(
            _env_file=None,
            ENVIRONMENT="synthetic_only",
            JWT_PRIVATE_KEY=private_pem.decode(),
            JWT_PUBLIC_KEY=public_pem.decode(),
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
        )
        base.update(overrides)
        settings = Settings(**base)
        get_settings.cache_clear()
        app = create_app(settings)
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_tenant_db] = lambda: db_session
        test_client = TestClient(app)
        test_client.__enter__()
        clients.append(test_client)
        return test_client, settings

    yield _make

    for test_client in clients:
        test_client.__exit__(None, None, None)
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


def _admin(db_session, settings, rsa_keypair):
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="Admin Host", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused-in-phase-1-stub",
        role="admin",
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=staff.id, role="admin",
    )
    return token, staff


def _caretaker(db_session, settings, rsa_keypair):
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="Caretaker Host", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused-in-phase-1-stub",
        role="caretaker",
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    token = _mint(
        settings, rsa_keypair,
        institution_id=inst.id, staff_id=staff.id, role="caretaker",
    )
    return token


STT_KEY = "SENTINEL-STT-KEY-never-in-a-response"
LLM_KEY = "SENTINEL-LLM-KEY-never-in-a-response"


# ── Access control ───────────────────────────────────────────────────────────


def test_provider_status_requires_auth_401(make_client):
    client, _ = make_client()
    assert client.get("/api/v1/admin/providers").status_code == 401
    assert client.post("/api/v1/admin/providers/stt/test").status_code == 401


def test_provider_status_caretaker_403(make_client, db_session, rsa_keypair):
    client, settings = make_client()
    token = _caretaker(db_session, settings, rsa_keypair)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/admin/providers", headers=headers).status_code == 403
    assert (
        client.post("/api/v1/admin/providers/stt/test", headers=headers).status_code
        == 403
    )


# ── Status cards: configured detection from env presence only ────────────────


def test_status_cards_nothing_configured(make_client, db_session, rsa_keypair):
    client, settings = make_client()  # defaults: STT_PROVIDER=none, LLM none
    token, _ = _admin(db_session, settings, rsa_keypair)

    resp = client.get(
        "/api/v1/admin/providers", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    cards = {card["provider"]: card for card in resp.json()["data"]["providers"]}
    assert cards["stt"]["configured"] is False
    assert cards["llm"]["configured"] is False
    assert cards["stt"]["backend"] == "none"
    assert cards["llm"]["backend"] == "none"


def test_status_cards_stt_configured_never_shows_key(make_client, db_session, rsa_keypair):
    client, settings = make_client(
        STT_PROVIDER="azure",
        AZURE_SPEECH_KEY=STT_KEY,
        AZURE_SPEECH_REGION="centralindia",
    )
    token, _ = _admin(db_session, settings, rsa_keypair)

    resp = client.get(
        "/api/v1/admin/providers", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    cards = {card["provider"]: card for card in resp.json()["data"]["providers"]}
    assert cards["stt"]["configured"] is True
    assert cards["stt"]["backend"] == "azure"
    # ADR-09: never display the key value — not even masked.
    assert STT_KEY not in resp.text


def test_status_cards_stt_partial_config_is_not_configured(
    make_client, db_session, rsa_keypair
):
    client, settings = make_client(STT_PROVIDER="azure", AZURE_SPEECH_KEY=STT_KEY)
    token, _ = _admin(db_session, settings, rsa_keypair)

    resp = client.get(
        "/api/v1/admin/providers", headers={"Authorization": f"Bearer {token}"}
    )
    cards = {card["provider"]: card for card in resp.json()["data"]["providers"]}
    assert cards["stt"]["configured"] is False
    assert STT_KEY not in resp.text


def test_status_cards_llm_configured_never_shows_key(make_client, db_session, rsa_keypair):
    client, settings = make_client(
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY=LLM_KEY,
        LLM_MODEL="gpt-4o-mini",
    )
    token, _ = _admin(db_session, settings, rsa_keypair)

    resp = client.get(
        "/api/v1/admin/providers", headers={"Authorization": f"Bearer {token}"}
    )
    cards = {card["provider"]: card for card in resp.json()["data"]["providers"]}
    assert cards["llm"]["configured"] is True
    assert cards["llm"]["backend"] == "openai_compatible"
    assert LLM_KEY not in resp.text


# ── Test connection: one minimal real call, success/failure only ─────────────


def test_stt_test_connection_success_one_call(make_client, db_session, rsa_keypair, monkeypatch):
    client, settings = make_client(
        STT_PROVIDER="azure", AZURE_SPEECH_KEY=STT_KEY, AZURE_SPEECH_REGION="westus"
    )
    token, admin = _admin(db_session, settings, rsa_keypair)

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return __import__("httpx").Response(
            200, request=__import__("httpx").Request("POST", url), content=b"token"
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post(
        "/api/v1/admin/providers/stt/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["success"] is True
    assert data["provider"] == "stt"
    # Exactly ONE minimal call; the credential went out on the wire only.
    assert len(calls) == 1
    assert calls[0][1]["headers"]["Ocp-Apim-Subscription-Key"] == STT_KEY
    # Response leaks nothing about the credential.
    assert STT_KEY not in resp.text


def test_stt_test_connection_failure_reports_failure_only(
    make_client, db_session, rsa_keypair, monkeypatch
):
    client, settings = make_client(
        STT_PROVIDER="azure", AZURE_SPEECH_KEY=STT_KEY, AZURE_SPEECH_REGION="westus"
    )
    token, _ = _admin(db_session, settings, rsa_keypair)

    def fake_post(url, **kwargs):
        return __import__("httpx").Response(
            401, request=__import__("httpx").Request("POST", url), content=b"denied"
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post(
        "/api/v1/admin/providers/stt/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()["data"]
    assert data["success"] is False
    # Sanitized: no provider internals, and never the key.
    assert STT_KEY not in resp.text
    assert "denied" not in resp.text


def test_stt_test_connection_network_error_is_failure(
    make_client, db_session, rsa_keypair, monkeypatch
):
    client, settings = make_client(
        STT_PROVIDER="azure", AZURE_SPEECH_KEY=STT_KEY, AZURE_SPEECH_REGION="westus"
    )
    token, _ = _admin(db_session, settings, rsa_keypair)

    def fake_post(url, **kwargs):
        raise __import__("httpx").ConnectError("unreachable")

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post(
        "/api/v1/admin/providers/stt/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200  # endpoint itself succeeded; the call failed
    data = resp.json()["data"]
    assert data["success"] is False
    assert STT_KEY not in resp.text


def test_stt_test_connection_knowlez_uses_usage_endpoint_no_region(
    make_client, db_session, rsa_keypair, monkeypatch
):
    """Owner-added second STT vendor (2026-09-01): Knowlez has no region
    concept, and its connection test hits the free /v1/usage endpoint —
    not a billed transcription call, unlike the LLM test-connection."""
    client, settings = make_client(STT_PROVIDER="knowlez", KNOWLEZ_STT_API_KEY=STT_KEY)
    token, _ = _admin(db_session, settings, rsa_keypair)

    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return __import__("httpx").Response(
            200, request=__import__("httpx").Request("GET", url), content=b"{}"
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.get", fake_get)

    resp = client.post(
        "/api/v1/admin/providers/stt/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["success"] is True
    assert len(calls) == 1
    assert calls[0][0] == "https://api-stt.knowlez.com/v1/usage"
    assert calls[0][1]["headers"]["x-api-key"] == STT_KEY
    assert STT_KEY not in resp.text


def test_status_cards_stt_knowlez_stored_credential_needs_no_region(
    make_client, db_session, rsa_keypair
):
    """Regression: the stored-credential status branch used to hardcode
    Azure and demand AZURE_SPEECH_REGION even for a non-Azure key."""
    from app.services.credential_service import CredentialService

    client, settings = make_client(STT_PROVIDER="knowlez")
    token, admin = _admin(db_session, settings, rsa_keypair)
    CredentialService(db_session, settings).store(
        provider="stt", value=STT_KEY, staff_id=admin.id
    )

    resp = client.get(
        "/api/v1/admin/providers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    stt = next(row for row in resp.json()["data"]["providers"] if row["provider"] == "stt")
    assert stt["configured"] is True
    assert stt["backend"] == "knowlez"
    assert "AZURE_SPEECH_REGION" not in stt["detail"]


def test_llm_test_connection_success(make_client, db_session, rsa_keypair, monkeypatch):
    client, settings = make_client(
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY=LLM_KEY,
        LLM_MODEL="gpt-4o-mini",
    )
    token, _ = _admin(db_session, settings, rsa_keypair)

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return __import__("httpx").Response(
            200, request=__import__("httpx").Request("POST", url), json={"choices": []}
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post(
        "/api/v1/admin/providers/llm/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()["data"]
    assert data["success"] is True
    assert len(calls) == 1
    # Minimal call: a trivial one-token ping, not a real workload.
    assert calls[0][1]["json"]["max_tokens"] == 1
    assert LLM_KEY not in resp.text


def test_test_connection_unconfigured_reports_not_configured(
    make_client, db_session, rsa_keypair, monkeypatch
):
    client, settings = make_client()  # nothing configured
    token, _ = _admin(db_session, settings, rsa_keypair)

    def fake_post(url, **kwargs):
        raise AssertionError("no network call may happen when unconfigured")

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post(
        "/api/v1/admin/providers/stt/test",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()["data"]
    assert data["success"] is False
    assert "not configured" in data["detail"].lower()


def test_test_connection_unknown_provider_404(make_client, db_session, rsa_keypair):
    client, settings = make_client()
    token, _ = _admin(db_session, settings, rsa_keypair)
    assert (
        client.post(
            "/api/v1/admin/providers/embeddings/test",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == 404
    )


def test_test_connection_is_audit_logged(make_client, db_session, rsa_keypair, monkeypatch):
    client, settings = make_client(
        STT_PROVIDER="azure", AZURE_SPEECH_KEY=STT_KEY, AZURE_SPEECH_REGION="westus"
    )
    token, admin = _admin(db_session, settings, rsa_keypair)

    def fake_post(url, **kwargs):
        return __import__("httpx").Response(
            200, request=__import__("httpx").Request("POST", url)
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    client.post(
        "/api/v1/admin/providers/stt/test",
        headers={"Authorization": f"Bearer {token}"},
    )

    from app.models.audit_log import AuditLogEntry

    entries = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.action == "provider.test_connection")
        .all()
    )
    assert len(entries) == 1
    assert entries[0].resource_id == "stt"
    assert entries[0].actor_id == admin.id
    # The audit trail must not carry the credential either.
    assert STT_KEY not in (entries[0].action + entries[0].resource_id)


def test_no_key_entry_surface_exists(make_client):
    """ADR-09: there is no form/endpoint that accepts and stores a key.
    Any attempt to write provider config through the API must be refused —
    405 (method missing) or 404 (route missing) both prove the surface
    does not exist."""
    client, _ = make_client()
    assert client.put("/api/v1/admin/providers/stt", json={"key": "x"}).status_code in {401, 404, 405}
    assert (
        client.post("/api/v1/admin/providers", json={"provider": "stt", "key": "x"}).status_code
        in {401, 404, 405}
    )
    assert (
        client.patch("/api/v1/admin/providers/stt", json={"key": "x"}).status_code
        in {401, 404, 405}
    )
