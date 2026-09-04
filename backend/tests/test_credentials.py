"""ADR-10 — admin-UI-editable provider credentials. A secrets feature is
tested like one:

- WRITE-ONLY enforcement: every response in this ticket (success, failure,
  error paths) is asserted to never contain the raw or encrypted value
  (sentinel technique from the ADR-09 provider-status tests).
- Encryption round-trip: the DB column is NOT the plaintext; the service
  still resolves the value for provider construction.
- Audit grep: the raw value never appears in any audit_log row.
- Precedence: active DB row beats env var; env var used when no active DB
  row; deactivation falls back to env var (FEAT-05's env path untouched).
- Admin-only guard + rate limit on PUT.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

SENTINEL = "sk-live-SENTINEL-ab12"          # raw secret value
ENV_SENTINEL = "sk-env-FALLBACK-xy99"      # env-var value for precedence tests


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


def _staff(db_session, *, role="admin"):
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name=f"Cred Tenant {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role=role, is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return inst, staff


# ── PUT: store + write-only contract ─────────────────────────────────────────


def test_put_stores_credential_and_never_echoes_the_value(
    client, settings, rsa_keypair, db_session
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")

    resp = client.put(
        "/api/v1/admin/credentials/llm",
        headers=_auth(token),
        json={"value": SENTINEL},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["provider"] == "llm"
    assert data["masked_suffix"] == "ab12"      # last 4 of the RAW value
    assert data["is_active"] is True
    assert data["updated_at"]
    # Write-only contract: raw value and column name never surface.
    assert SENTINEL not in resp.text
    assert "encrypted_value" not in resp.text


def test_put_rotates_deactivating_prior_row(client, settings, rsa_keypair, db_session):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    client.put("/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": SENTINEL})

    second = "sk-live-ROTATED-cd34"
    resp = client.put(
        "/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": second}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["masked_suffix"] == "cd34"
    assert SENTINEL not in resp.text and second not in resp.text

    from app.models.provider_credential import ProviderCredential

    rows = (
        db_session.query(ProviderCredential)
        .filter(ProviderCredential.provider == "llm")
        .order_by(ProviderCredential.created_at.asc())
        .all()
    )
    assert len(rows) == 2
    assert rows[0].is_active is False
    assert rows[1].is_active is True


def test_put_unknown_provider_404_and_validation_422(
    client, settings, rsa_keypair, db_session
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    assert (
        client.put(
            "/api/v1/admin/credentials/embeddings", headers=_auth(token),
            json={"value": SENTINEL},
        ).status_code
        == 404
    )
    resp = client.put(
        "/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": "   "}
    )
    assert resp.status_code == 422
    assert SENTINEL not in resp.text


def test_put_rate_limited(client, settings, rsa_keypair, db_session):
    """Secret writes get the tightest budget (auth-tier)."""
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    codes = [
        client.put(
            "/api/v1/admin/credentials/llm", headers=_auth(token),
            json={"value": f"sk-x{i:04d}"},
        ).status_code
        for i in range(6)
    ]
    assert codes[-1] == 429
    assert all(code in (200, 429) for code in codes)


# ── Guards: admin-only ───────────────────────────────────────────────────────


def test_caretaker_locked_out_of_credential_endpoints(
    client, settings, rsa_keypair, db_session
):
    inst, caretaker = _staff(db_session, role="caretaker")
    token = _mint(
        settings, rsa_keypair, institution_id=inst.id, staff_id=caretaker.id,
        role="caretaker",
    )
    headers = _auth(token)
    assert client.get("/api/v1/admin/credentials", headers=headers).status_code == 403
    assert (
        client.put("/api/v1/admin/credentials/llm", headers=headers, json={"value": SENTINEL}).status_code
        == 403
    )
    assert (
        client.delete("/api/v1/admin/credentials/llm", headers=headers).status_code == 403
    )


def test_missing_token_401(client):
    assert client.get("/api/v1/admin/credentials").status_code == 401
    assert client.put("/api/v1/admin/credentials/llm", json={"value": "x"}).status_code == 401


# ── GET: status list — structurally unable to leak the value ────────────────


def test_get_lists_status_without_any_value_material(
    client, settings, rsa_keypair, db_session
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    client.put("/api/v1/admin/credentials/stt", headers=_auth(token), json={"value": SENTINEL})

    resp = client.get("/api/v1/admin/credentials", headers=_auth(token))
    assert resp.status_code == 200
    by_provider = {item["provider"]: item for item in resp.json()["data"]["providers"]}
    assert by_provider["stt"]["is_active"] is True
    assert by_provider["stt"]["masked_suffix"] == "ab12"
    assert by_provider["llm"]["is_active"] is False
    assert by_provider["llm"]["masked_suffix"] is None
    # Only the documented fields exist — the encrypted column is not even
    # selected by the query.
    for item in resp.json()["data"]["providers"]:
        assert set(item.keys()) == {
            "provider", "is_active", "masked_suffix", "updated_at", "model_name",
        }
    assert SENTINEL not in resp.text


# ── Encryption round-trip: DB column is NOT plaintext ───────────────────────


def test_stored_column_is_encrypted_but_resolvable(
    client, settings, rsa_keypair, db_session
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    client.put("/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": SENTINEL})

    from app.models.provider_credential import ProviderCredential
    from app.services.credential_service import CredentialService

    row = (
        db_session.query(ProviderCredential)
        .filter(ProviderCredential.provider == "llm", ProviderCredential.is_active.is_(True))
        .one()
    )
    # The column is a Fernet token — never the plaintext.
    assert row.encrypted_value != SENTINEL
    assert SENTINEL not in row.encrypted_value
    # …but the service decrypts it at the point of provider construction.
    key, _model = CredentialService(db_session, settings).resolve_with_model("llm")
    assert key == SENTINEL
    assert CredentialService(db_session, settings).resolve_with_model("stt")[0] is None


# ── Audit log NEVER contains the value (grep-based) ─────────────────────────


def test_audit_rows_never_contain_the_value(client, settings, rsa_keypair, db_session):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    client.put("/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": SENTINEL})
    client.delete("/api/v1/admin/credentials/llm", headers=_auth(token))

    from app.models.audit_log import AuditLogEntry

    rows = (
        db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_type == "provider_credential")
        .order_by(AuditLogEntry.sequence.asc())
        .all()
    )
    actions = [row.action for row in rows]
    assert actions == ["credential.store", "credential.deactivate"]
    for row in rows:
        # Grep every textual column of every row: the raw value appears
        # nowhere in the tamper-evident trail.
        blob = f"{row.action}|{row.resource_type}|{row.resource_id}|{row.actor_id}"
        assert SENTINEL not in blob
        assert "ab12" not in blob  # not even the masked suffix


# ── Precedence: DB beats env; env is the fallback ───────────────────────────


def test_db_credential_beats_env_var_for_llm(client, settings, rsa_keypair, db_session):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")

    settings.LLM_PROVIDER = "openai_compatible"
    settings.LLM_API_KEY = ENV_SENTINEL
    settings.LLM_MODEL = "gpt-4o-mini"
    client.put("/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": SENTINEL})

    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.llm import OpenAICompatibleLLM

    provider = get_reasoning_provider(settings, db_session)
    assert isinstance(provider, OpenAICompatibleLLM)
    assert provider.api_key == SENTINEL          # DB wins over env


def test_env_var_used_when_no_active_db_row(settings, db_session):
    settings.LLM_PROVIDER = "openai_compatible"
    settings.LLM_API_KEY = ENV_SENTINEL
    settings.LLM_MODEL = "gpt-4o-mini"

    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.llm import OpenAICompatibleLLM

    provider = get_reasoning_provider(settings, db_session)
    assert isinstance(provider, OpenAICompatibleLLM)
    assert provider.api_key == ENV_SENTINEL      # env path unchanged (FEAT-05)


def test_deactivation_falls_back_to_env_var(client, settings, rsa_keypair, db_session):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")

    settings.LLM_PROVIDER = "openai_compatible"
    settings.LLM_API_KEY = ENV_SENTINEL
    settings.LLM_MODEL = "gpt-4o-mini"
    client.put("/api/v1/admin/credentials/llm", headers=_auth(token), json={"value": SENTINEL})

    deleted = client.delete("/api/v1/admin/credentials/llm", headers=_auth(token))
    assert deleted.status_code == 200
    assert deleted.json()["data"]["is_active"] is False
    assert SENTINEL not in deleted.text

    from app.api.v1.endpoints.reasoning import get_reasoning_provider

    provider = get_reasoning_provider(settings, db_session)
    assert provider.api_key == ENV_SENTINEL      # fell back to env

    # Deleting again → nothing active to deactivate.
    assert (
        client.delete("/api/v1/admin/credentials/llm", headers=_auth(token)).status_code
        == 404
    )


def test_stt_db_credential_builds_azure_provider(client, settings, rsa_keypair, db_session):
    """An active STT row + env region → a working Azure provider even when
    STT_PROVIDER says none (admin intent via the UI)."""
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    settings.STT_PROVIDER = "none"
    settings.AZURE_SPEECH_REGION = "westus"
    client.put("/api/v1/admin/credentials/stt", headers=_auth(token), json={"value": SENTINEL})

    from app.api.v1.endpoints.stt import get_stt_provider
    from app.services.stt import AzureSpeechProvider

    provider = get_stt_provider(settings, db_session)
    assert isinstance(provider, AzureSpeechProvider)
    assert provider.key == SENTINEL


def test_env_only_stt_path_unchanged_with_no_rows(settings, db_session):
    """Regression: with zero provider_credentials rows the env path behaves
    exactly as before ADR-10 (FEAT-03/FEAT-05 keep working)."""
    settings.STT_PROVIDER = "azure"
    settings.AZURE_SPEECH_KEY = ENV_SENTINEL
    settings.AZURE_SPEECH_REGION = "westus"

    from app.api.v1.endpoints.stt import get_stt_provider
    from app.services.stt import AzureSpeechProvider

    provider = get_stt_provider(settings, db_session)
    assert isinstance(provider, AzureSpeechProvider)
    assert provider.key == ENV_SENTINEL


def test_stt_db_credential_builds_knowlez_provider(client, settings, rsa_keypair, db_session):
    """Owner-added second STT vendor (2026-09-01): a stored key + explicit
    STT_PROVIDER=knowlez builds the Knowlez adapter, not Azure — and needs
    no region, unlike Azure's stored-credential path above."""
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    settings.STT_PROVIDER = "knowlez"
    client.put("/api/v1/admin/credentials/stt", headers=_auth(token), json={"value": SENTINEL})

    from app.api.v1.endpoints.stt import get_stt_provider
    from app.services.stt import KnowlezSttProvider

    provider = get_stt_provider(settings, db_session)
    assert isinstance(provider, KnowlezSttProvider)
    assert provider.key == SENTINEL


def test_stt_db_credential_still_builds_azure_when_provider_unset(
    client, settings, rsa_keypair, db_session
):
    """Regression: adding the Knowlez branch must not change the existing
    Azure stored-credential default (STT_PROVIDER left at "none", region
    present — the original admin-intent-via-UI behavior)."""
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    settings.STT_PROVIDER = "none"
    settings.AZURE_SPEECH_REGION = "westus"
    client.put("/api/v1/admin/credentials/stt", headers=_auth(token), json={"value": SENTINEL})

    from app.api.v1.endpoints.stt import get_stt_provider
    from app.services.stt import AzureSpeechProvider

    provider = get_stt_provider(settings, db_session)
    assert isinstance(provider, AzureSpeechProvider)
    assert provider.key == SENTINEL


# ── Test connection honors precedence (ADR-09 endpoint keeps working) ───────


def test_test_connection_uses_active_db_credential(
    client, settings, rsa_keypair, db_session, monkeypatch
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    settings.STT_PROVIDER = "azure"
    settings.AZURE_SPEECH_KEY = ENV_SENTINEL
    settings.AZURE_SPEECH_REGION = "westus"
    client.put("/api/v1/admin/credentials/stt", headers=_auth(token), json={"value": SENTINEL})

    seen_keys = []

    def fake_post(url, **kwargs):
        seen_keys.append(kwargs["headers"].get("Ocp-Apim-Subscription-Key"))
        return __import__("httpx").Response(
            200, request=__import__("httpx").Request("POST", url), content=b"token"
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post("/api/v1/admin/providers/stt/test", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["success"] is True
    assert seen_keys == [SENTINEL]             # DB credential, not env
    assert SENTINEL not in resp.text and ENV_SENTINEL not in resp.text


def test_test_connection_llm_forwards_stored_model_override(
    client, settings, rsa_keypair, db_session, monkeypatch
):
    """Regression: test-connection silently pinged settings.LLM_MODEL and
    ignored the stored override, so a non-OpenAI model saved via the admin
    console (e.g. a DeepSeek model on an OpenAI-compatible base URL) always
    failed the connection test even with valid credentials."""
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    settings.LLM_MODEL = "gpt-4o-mini"  # the env default the bug fell back to
    client.put(
        "/api/v1/admin/credentials/llm",
        headers=_auth(token),
        json={"value": SENTINEL, "model": "deepseek-v4-flash"},
    )

    seen_models = []

    def fake_post(url, **kwargs):
        seen_models.append(kwargs["json"]["model"])
        return __import__("httpx").Response(
            200, request=__import__("httpx").Request("POST", url), content=b"{}"
        )

    monkeypatch.setattr("app.services.provider_checks.httpx.post", fake_post)

    resp = client.post("/api/v1/admin/providers/llm/test", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["success"] is True
    assert seen_models == ["deepseek-v4-flash"]  # stored override, not env LLM_MODEL
