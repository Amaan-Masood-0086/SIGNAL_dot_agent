"""A reasoning trail must still say what it said (audit finding F11).

The knowledge base is ingested with an upsert keyed on `citation_ref`, so a
milestone's wording can change in place. The flag read path used to resolve
descriptions live, which meant reopening a six-month-old flag showed today's
wording — not the wording the grade was actually made on.

For a product whose regulatory and liability argument is "the basis is
documented and reviewable", a basis that can be silently rewritten is the
one thing that cannot be allowed. These tests pin the snapshot.
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


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _mint(settings, rsa_keypair, *, institution_id, staff_id, role="caretaker"):
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


def _scenario(db_session):
    """One institution, one child, one session, one milestone, one flag."""
    from app.models.child import Child
    from app.models.session import Session as ConversationSession
    from app.models.flag import Flag
    from app.models.institution import Institution
    from app.models.milestone import Milestone
    from app.models.staff import Staff

    inst = Institution(name=f"Trail {uuid.uuid4().hex[:6]}", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()

    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    child = Child(
        id=uuid.uuid4(), institution_id=inst.id, name="Trail Child",
        intake_date=datetime.date(2026, 8, 1), dob_confirmed=True,
        dob=datetime.date(2024, 1, 1), is_synthetic=True,
    )
    db_session.add_all([staff, child])
    db_session.flush()

    ref = f"SL-M-TRAIL-{uuid.uuid4().hex[:6]}"
    milestone = Milestone(
        citation_ref=ref, domain="Speech_Language", entry_type="milestone",
        age_min_months=12, age_max_months=24,
        description="ORIGINAL wording at the time of the grade",
        source="Original Source 2019", severity=None,
        phase_scope="PHASE 1 (0-6)", provenance="test fixture",
    )
    db_session.add(milestone)

    convo = ConversationSession(
        id=uuid.uuid4(), institution_id=inst.id, child_id=child.id,
        staff_id=staff.id, status="completed", mode="text",
    )
    db_session.add(convo)
    db_session.flush()

    flag = Flag(
        id=uuid.uuid4(), institution_id=inst.id, session_id=convo.id,
        child_id=child.id, domain="Speech_Language", confidence_grade="moderate",
        status="flagged", explanation_text="…",
        reasoning_trail=[
            {
                "citation_ref": ref,
                "basis": "ORIGINAL wording at the time of the grade",
                "source": "Original Source 2019",
            }
        ],
    )
    db_session.add(flag)
    db_session.flush()
    return inst, staff, child, milestone, flag


def test_trail_shows_the_wording_the_grade_was_made_on(
    client, settings, rsa_keypair, db_session
):
    """The knowledge base changes; the flag does not."""
    inst, staff, _, milestone, flag = _scenario(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    # The knowledge base is revised after the flag was written.
    milestone.description = "REVISED wording, edited months later"
    milestone.source = "Revised Source 2026"
    db_session.flush()

    resp = client.get(f"/api/v1/flags/{flag.id}", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    entry = resp.json()["data"]["reasoning_trail"][0]

    assert entry["description"] == "ORIGINAL wording at the time of the grade"
    assert entry["source"] == "Original Source 2019"
    assert "REVISED" not in resp.text


def test_drift_is_surfaced_not_hidden(client, settings, rsa_keypair, db_session):
    """Showing the original is right; concealing that it moved on is not."""
    inst, staff, _, milestone, flag = _scenario(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    milestone.description = "REVISED wording, edited months later"
    db_session.flush()

    entry = client.get(f"/api/v1/flags/{flag.id}", headers=_auth(token)).json()[
        "data"
    ]["reasoning_trail"][0]
    assert entry["kb_drifted"] is True


def test_no_drift_flag_when_the_knowledge_base_is_unchanged(
    client, settings, rsa_keypair, db_session
):
    inst, staff, _, _, flag = _scenario(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    entry = client.get(f"/api/v1/flags/{flag.id}", headers=_auth(token)).json()[
        "data"
    ]["reasoning_trail"][0]
    assert entry["kb_drifted"] is False
    assert entry["description"] == "ORIGINAL wording at the time of the grade"


def test_pre_snapshot_flags_still_resolve(client, settings, rsa_keypair, db_session):
    """Backward compatibility: flags written before snapshots existed carry
    no basis, and must still render from the live row rather than blank."""
    inst, staff, _, milestone, flag = _scenario(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    flag.reasoning_trail = [{"citation_ref": milestone.citation_ref}]
    db_session.flush()

    entry = client.get(f"/api/v1/flags/{flag.id}", headers=_auth(token)).json()[
        "data"
    ]["reasoning_trail"][0]
    assert entry["description"] == milestone.description
    assert entry["kb_drifted"] is False
