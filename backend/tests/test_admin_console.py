"""Admin console extensions (2026-09-01 owner request):

- LLM model name is settable through the credential surface (non-secret,
  plaintext, displayable) and takes precedence over the env LLM_MODEL.
- GET /admin/children — cross-institution oversight roster (admin-only;
  caretaker-facing surfaces stay institution-scoped).
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from fastapi.testclient import TestClient

SENTINEL = "sk-live-MODELTEST-ab12"


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
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-env-OLD-xy99",
        LLM_MODEL="gpt-4o-mini",
    )


@pytest.fixture()
def client(settings, db_session):
    from app.api.deps import get_db
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app(settings)
    app.dependency_overrides[get_db] = lambda: db_session
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

    inst = Institution(name=f"Console {uuid.uuid4().hex[:6]}", is_synthetic=True)
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


def test_model_name_stored_displayed_and_wins_over_env(
    client, settings, rsa_keypair, db_session
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")

    resp = client.put(
        "/api/v1/admin/credentials/llm",
        headers=_auth(token),
        json={"value": SENTINEL, "model": "gpt-4o-2026"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["model_name"] == "gpt-4o-2026"
    assert data["masked_suffix"] == "ab12"
    # Write-only contract still holds: the key itself never echoes.
    assert SENTINEL not in resp.text

    # Provider resolution: stored key AND stored model beat env.
    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.llm import OpenAICompatibleLLM

    provider = get_reasoning_provider(settings, db_session)
    assert isinstance(provider, OpenAICompatibleLLM)
    assert provider.api_key == SENTINEL
    assert provider.model == "gpt-4o-2026"


def test_model_falls_back_to_env_when_not_stored(
    client, settings, rsa_keypair, db_session
):
    inst, admin = _staff(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin")
    client.put(
        "/api/v1/admin/credentials/llm",
        headers=_auth(token),
        json={"value": SENTINEL},  # no model
    )

    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.llm import OpenAICompatibleLLM

    provider = get_reasoning_provider(settings, db_session)
    assert isinstance(provider, OpenAICompatibleLLM)
    assert provider.model == "gpt-4o-mini"  # env LLM_MODEL


def test_admin_children_cross_institution_roster(
    client, settings, rsa_keypair, db_session
):
    """The admin sees children from OTHER institutions; caretakers never do."""
    from app.models.child import Child

    inst, admin = _staff(db_session, role="admin")
    other_inst, caretaker = _staff(db_session, role="caretaker")
    child = Child(
        institution_id=other_inst.id, name="Roster Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=False, estimated_age_range="24-36 months",
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()

    admin_token = _mint(
        settings, rsa_keypair, institution_id=inst.id, staff_id=admin.id, role="admin"
    )
    resp = client.get("/api/v1/admin/children", headers=_auth(admin_token))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["total"] >= 1
    row = next(item for item in data["items"] if item["name"] == "Roster Child")
    assert row["institution_id"] == str(other_inst.id)
    assert row["institution_name"] == other_inst.name
    assert row["estimated_age_range"] == "24-36 months"

    # Caretaker is locked out of the oversight roster.
    caretaker_token = _mint(
        settings, rsa_keypair,
        institution_id=other_inst.id, staff_id=caretaker.id, role="caretaker",
    )
    assert (
        client.get("/api/v1/admin/children", headers=_auth(caretaker_token)).status_code
        == 403
    )
