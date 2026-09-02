"""API-surface security headers (audit F7).

The frontend sets its own headers in next.config.ts / proxy.ts, but the
backend is independently reachable — curl, a future mobile client, a
misrouted link — and previously answered with no protective headers and no
cache directive on responses that carry child health data.

These tests pin the headers so a future middleware reorder cannot silently
drop them.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(rsa_keypair, db_session):
    from app.api.deps import get_db, get_tenant_db
    from app.core.config import Settings, get_settings
    from app.main import create_app

    private_pem, public_pem = rsa_keypair
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY=private_pem.decode(),
        JWT_PUBLIC_KEY=public_pem.decode(),
    )
    get_settings.cache_clear()
    app = create_app(settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


EXPECTED = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "private, no-store",
}


def test_health_carries_security_headers(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    for header, value in EXPECTED.items():
        assert resp.headers.get(header) == value, f"{header} missing or wrong"


def test_api_responses_are_never_cacheable(client):
    """Every API response may carry PHI — none of it is cacheable by anyone."""
    resp = client.get("/api/v1/children")  # 401: no token, still a response
    assert resp.headers.get("Cache-Control") == "private, no-store"


def test_error_responses_also_carry_headers(client):
    """Headers must survive the exception handlers, not just happy paths."""
    resp = client.get("/api/v1/children")
    assert resp.status_code == 401
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Cache-Control") == "private, no-store"


def test_server_banner_is_not_the_framework_default(client):
    """OWASP A02: do not advertise the server stack."""
    assert resp_server(client) == "SIGNAL"


def resp_server(client) -> str | None:
    return client.get("/health").headers.get("Server")


def test_api_csp_forbids_everything(client):
    """The API serves JSON and needs to load nothing at all."""
    csp = client.get("/health").headers.get("Content-Security-Policy", "")
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


# ── Login throttle (audit F2) ──────────────────────────────────────────────


def test_login_is_throttled_after_five_attempts(client):
    """Credential stuffing on one account is capped. Keyed by email, because
    every login arrives from the Next server's address — a per-IP limit here
    would throttle the whole user base together."""
    from app.api.v1.endpoints.auth import LOGIN_LIMITER

    LOGIN_LIMITER._windows.clear()
    body = {"email": "throttle-probe@signal.example", "password": "x"}

    for attempt in range(5):
        assert client.post("/api/v1/auth/token", json=body).status_code == 200, attempt

    blocked = client.post("/api/v1/auth/token", json=body)
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") == "300"


def test_login_throttle_is_per_account_not_global(client):
    """One account being throttled must not lock everyone else out."""
    from app.api.v1.endpoints.auth import LOGIN_LIMITER

    LOGIN_LIMITER._windows.clear()
    noisy = {"email": "noisy@signal.example", "password": "x"}
    for _ in range(6):
        client.post("/api/v1/auth/token", json=noisy)

    other = client.post(
        "/api/v1/auth/token",
        json={"email": "quiet@signal.example", "password": "x"},
    )
    assert other.status_code == 200


def test_throttled_login_is_not_reported_as_bad_credentials(client):
    """A 429 must stay a 429 all the way to the browser.

    Collapsing it into 401 tells the operator to re-check credentials that
    were never wrong — the same misleading-error class as the CSRF 403, and
    it wasted real debugging time before it was caught.
    """
    from app.api.v1.endpoints.auth import LOGIN_LIMITER

    LOGIN_LIMITER._windows.clear()
    body = {"email": "masquerade-probe@signal.example", "password": "x"}
    for _ in range(5):
        client.post("/api/v1/auth/token", json=body)

    blocked = client.post("/api/v1/auth/token", json=body)
    assert blocked.status_code == 429, "throttle must not be reported as 401"
    assert "credential" not in blocked.json()["detail"].lower()
    assert blocked.headers.get("Retry-After") == "300"
