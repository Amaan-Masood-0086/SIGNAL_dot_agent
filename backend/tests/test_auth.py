"""JWT auth stub — TRD §4: institution_id + role embedded as signed claims.

FEAT-01 delivers the stub only: token mint/verify with RS256, the verified-
staff dependency, and the synthetic-environment guard on the stub endpoint.
Account lockout/blacklisting are FEAT-12 scope, not here.
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
    # The stub token endpoint consults staff rows (RBAC bootstrap seam) —
    # point it at the transaction-isolated test session, never the dev DB.
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_token_stub_mints_signed_claims(client, settings):
    resp = client.post(
        "/api/v1/auth/token",
        json={"email": "synthetic-staff@signal.example", "password": "synthetic"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    token = body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"

    # Claims must round-trip through the public key — proves RS256 signature.
    from app.core import security

    claims = security.decode_access_token(token, settings=settings)
    assert claims["institution_id"] is not None
    assert claims["role"] in {"caretaker", "admin"}
    assert claims["sub"]  # staff id


def test_token_request_validation_422(client):
    """Every endpoint MUST have Pydantic validation — malformed body → 422."""
    resp = client.post("/api/v1/auth/token", json={"email": "not-an-email"})
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_me_endpoint_returns_claims_from_jwt(client):
    token = client.post(
        "/api/v1/auth/token",
        json={"email": "synthetic-staff@signal.example", "password": "synthetic"},
    ).json()["data"]["access_token"]
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["role"] in {"caretaker", "admin"}
    assert "institution_id" in data


def test_missing_token_401(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "detail" in resp.json()  # error format contract


def test_tampered_token_401(client, rsa_keypair, settings):
    """A token signed by a different key must never verify."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa as rsa_mod

    from app.core import security

    other_key = rsa_mod.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    forged = security.create_access_token(
        staff_id=str(uuid.uuid4()),
        institution_id=str(uuid.uuid4()),
        role="admin",
        private_key_pem=other_pem,
        expires_minutes=15,
        settings=settings,
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_expired_token_401(client, rsa_keypair, settings):
    private_pem, _ = rsa_keypair
    from app.core import security

    expired = security.create_access_token(
        staff_id=str(uuid.uuid4()),
        institution_id=str(uuid.uuid4()),
        role="caretaker",
        private_key_pem=private_pem,
        expires_minutes=-1,
        settings=settings,
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_token_stub_refused_outside_synthetic_environment(rsa_keypair):
    """The stub login endpoint exists for synthetic dev only — 403 elsewhere."""
    private_pem, public_pem = rsa_keypair
    from app.core.config import Settings
    from app.main import create_app

    settings = Settings(
        _env_file=None,
        ENVIRONMENT="staging",
        JWT_PRIVATE_KEY=private_pem.decode(),
        JWT_PUBLIC_KEY=public_pem.decode(),
    )
    app = create_app(settings)
    with TestClient(app) as non_synthetic_client:
        resp = non_synthetic_client.post(
            "/api/v1/auth/token",
            json={"email": "synthetic-staff@signal.example", "password": "x"},
        )
    assert resp.status_code == 403
