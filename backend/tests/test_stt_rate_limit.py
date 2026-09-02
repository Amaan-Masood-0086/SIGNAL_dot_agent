"""Rate limiting on the per-turn capture surface (FEAT-03 hardening).

TRD §4 locks "30/min per staff member" on the turn-capture endpoint
(`/sessions/{id}/messages` in TRD terms — implemented as
`/sessions/{id}/observations`); the threat model's Cost-DoS row is the same
30/min per staff. `POST /stt/transcribe` forwards every call to a paid cloud
provider, so it carries the identical cap. RED first: while no limiter
exists, the 31st request returns 200/201, not 429.
"""

from fastapi.testclient import TestClient

from tests.conftest import db_session, pg_engine, rsa_keypair  # noqa: F401
from tests.test_sessions import (  # noqa: F401  (settings is a pytest fixture)
    _mint_token,
    _seed_child,
    _seed_institution,
    _seed_staff,
    settings,
)


class FakeProvider:
    language = "ur-PK"

    def transcribe(self, audio: bytes) -> str:
        return "fake transcript"


def _client(settings, db_session, *, fake_stt=False):
    from app.api.deps import get_db, get_tenant_db
    from app.main import create_app

    app = create_app(settings)
    # Endpoint DB session is the transaction-isolated test session.
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_db] = lambda: db_session
    if fake_stt:
        from app.api.v1.endpoints.stt import get_stt_provider

        app.dependency_overrides[get_stt_provider] = lambda: FakeProvider()
    return TestClient(app)


def _post_audio(client: TestClient, token: str):
    return client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files={"audio": ("turn.webm", b"RIFFdummyaudio", "audio/webm")},
    )


# ── /stt/transcribe ─────────────────────────────────────────────────────────


def test_transcribe_allows_30_per_minute_then_429(settings, rsa_keypair, db_session):
    client = _client(settings, db_session, fake_stt=True)
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)

    for attempt in range(30):
        response = _post_audio(client, token)
        assert response.status_code == 200, f"attempt {attempt + 1}: {response.text}"

    blocked = _post_audio(client, token)
    assert blocked.status_code == 429


def test_transcribe_rate_limit_is_per_staff(settings, rsa_keypair, db_session):
    client = _client(settings, db_session, fake_stt=True)
    inst = _seed_institution(db_session)
    token_a, staff_a = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_a)
    token_b, staff_b = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_b)

    for _ in range(30):
        assert _post_audio(client, token_a).status_code == 200
    assert _post_audio(client, token_a).status_code == 429

    # Staff B has an independent budget.
    assert _post_audio(client, token_b).status_code == 200


def test_transcribe_rate_limit_window_resets(settings, rsa_keypair, db_session):
    from app.api.v1.endpoints import stt as stt_endpoint

    client = _client(settings, db_session, fake_stt=True)
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)

    fake_now = [1000.0]
    limiter = stt_endpoint.TRANSCRIBE_LIMITER
    original_now = limiter._now
    limiter._now = lambda: fake_now[0]
    try:
        for _ in range(30):
            assert _post_audio(client, token).status_code == 200
        assert _post_audio(client, token).status_code == 429

        fake_now[0] += 61.0  # next window
        assert _post_audio(client, token).status_code == 200
    finally:
        limiter._now = original_now


def test_transcribe_size_cap_pins_90s_budget():
    """Pin the byte budget so it cannot silently drift.

    The 60 s duration cap lives client-side and is bypassable via direct
    API calls, so the server size cap is the real guard. It must bracket
    ~90 s of opus voice audio with headroom — typical browser opus voice
    is ~32-64 kbps (90 s => ~0.4-0.8 MB), so 1.5 MB leaves ample margin
    while staying far below any multi-minute abuse. Changing this number
    requires a deliberate decision, hence the pinned literal.
    """
    from app.api.v1.endpoints import stt as stt_endpoint

    assert stt_endpoint.MAX_AUDIO_BYTES == int(1.5 * 1024 * 1024)


def test_transcribe_oversized_audio_413_before_provider(settings, rsa_keypair, db_session):
    """Size guard fires before any provider call (DoS / cost bound)."""
    from app.api.v1.endpoints import stt as stt_endpoint

    calls = []

    class TripwireProvider:
        language = "ur-PK"

        def transcribe(self, audio: bytes) -> str:
            calls.append(len(audio))
            return "must never run"

    client = _client(settings, db_session)
    client.app.dependency_overrides[stt_endpoint.get_stt_provider] = (
        lambda: TripwireProvider()
    )
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)

    oversized = b"\x00" * (stt_endpoint.MAX_AUDIO_BYTES + 1)
    response = client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files={"audio": ("turn.webm", oversized, "audio/webm")},
    )
    assert response.status_code == 413
    assert calls == []  # provider never saw the oversized payload


# ── /sessions/{id}/observations (TRD's /messages) ───────────────────────────


def _open_session(client, settings, rsa_keypair, db_session):
    """Seed tenant + staff + child, open a session. Returns (session_id, token)."""
    inst = _seed_institution(db_session)
    token, staff_id = _mint_token(settings, rsa_keypair, institution_id=inst.id)
    _seed_staff(db_session, institution_id=inst.id, staff_id=staff_id)
    child = _seed_child(db_session, institution_id=inst.id)
    resp = client.post(
        "/api/v1/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"child_id": str(child.id), "mode": "text"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"], token


def test_observation_allows_30_per_minute_then_429(settings, rsa_keypair, db_session):
    client = _client(settings, db_session)
    session_id, token = _open_session(client, settings, rsa_keypair, db_session)
    url = f"/api/v1/sessions/{session_id}/observations"
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(30):
        resp = client.post(url, headers=headers, json={"raw_input": f"turn {attempt + 1}"})
        assert resp.status_code == 201, f"attempt {attempt + 1}: {resp.text}"

    blocked = client.post(url, headers=headers, json={"raw_input": "turn 31"})
    assert blocked.status_code == 429
