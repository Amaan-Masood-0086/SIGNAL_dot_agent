"""FEAT-11 — safeguarding-escalation pathway (Phase 1 stub depth).

Acceptance: an abuse/neglect-pattern test input produces a
`safeguarding_escalations` row and explicitly does NOT produce a `flags`
row. The write path is a SEPARATE service + table from flags (sdlc-security
rule 14: no shared code path, ever). Downstream mandatory-reporting stays
out of scope (PROJECT_BRIEF Open Item #6) — this ticket delivers routing +
separation + the row write only.
"""

from __future__ import annotations

import datetime
import json
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def loaded_kb(pg_engine):
    from sqlalchemy import delete
    from sqlalchemy.orm import Session

    from app.models.milestone import Milestone
    from app.services.knowledge import load_knowledge_base

    session = Session(bind=pg_engine, expire_on_commit=False)
    load_knowledge_base(session)
    session.commit()
    yield session
    session.execute(delete(Milestone))
    session.commit()
    session.close()


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
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


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


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _tenant(db_session):
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.session import Session as ConversationSession
    from app.models.staff import Staff

    inst = Institution(name="FEAT-11 Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(staff)
    child = Child(
        institution_id=inst.id, name="Safeguarding Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True, dob=datetime.date(2022, 8, 1),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    session = ConversationSession(
        institution_id=inst.id, child_id=child.id, staff_id=staff.id, mode="text"
    )
    db_session.add(session)
    db_session.flush()
    return inst, staff, child, session


class ScriptedProvider:
    def __init__(self, *responses):
        self.responses = list(responses)

    def complete(self, *, agent, tier, system, user):
        return self.responses.pop(0)


SAFEGUARDING_INPUT = (
    "She's very withdrawn and flinches when anyone moves suddenly near her"
)


def test_safeguarding_input_writes_escalation_row_and_no_flag(
    db_session, loaded_kb
):
    """TEST_PLAN §2 safeguarding separation — at the pipeline level."""
    from app.models.flag import Flag
    from app.models.safeguarding_escalation import SafeguardingEscalation
    from app.services.risk_pipeline import RiskPipeline

    inst, staff, child, session = _tenant(db_session)
    provider = ScriptedProvider(
        json.dumps({
            "signals": ["flinches at sudden movement", "withdrawn"],
            "safeguarding_pattern": True,
            "key_items_missing": False,
        }),
    )
    result = RiskPipeline(db_session, provider).run(
        session=session, child=child, caretaker_turns=[SAFEGUARDING_INPUT],
        turn_number=1, staff_id=staff.id, institution_id=inst.id,
        reference_date=datetime.date(2026, 8, 31),
    )

    assert result.outcome == "safeguarding_escalation"
    escalations = db_session.query(SafeguardingEscalation).all()
    assert len(escalations) == 1
    escalation = escalations[0]
    assert escalation.child_id == child.id
    assert escalation.session_id == session.id
    assert escalation.institution_id == inst.id
    assert escalation.status == "open"
    assert escalation.signal_description  # what was observed is recorded
    # The developmental table stays EMPTY — separation is the whole point.
    assert db_session.query(Flag).count() == 0


def test_developmental_path_writes_flag_and_no_escalation(
    db_session, loaded_kb
):
    from app.models.flag import Flag
    from app.models.safeguarding_escalation import SafeguardingEscalation
    from app.services.risk_pipeline import RiskPipeline

    inst, staff, child, session = _tenant(db_session)
    provider = ScriptedProvider(
        json.dumps({
            "signals": ["no response to sound"],
            "safeguarding_pattern": False,
            "key_items_missing": False,
        }),
        json.dumps({
            "concluded": True, "follow_up_question": None,
            "key_items_missing": False,
            "confirmed_red_flags": ["HEAR-RF-016"],
            "missed_milestones": [], "met_milestones": [], "risk_modifiers": [],
        }),
        "Please see a clinician.",
    )
    result = RiskPipeline(db_session, provider).run(
        session=session, child=child,
        caretaker_turns=["He doesn't react to loud sounds"],
        turn_number=1, staff_id=staff.id, institution_id=inst.id,
        reference_date=datetime.date(2026, 8, 31),
    )

    assert result.outcome == "flagged"
    assert db_session.query(Flag).count() == 1
    assert db_session.query(SafeguardingEscalation).count() == 0


def test_safeguarding_endpoint_flow_writes_row_and_audits(
    client, settings, rsa_keypair, db_session, loaded_kb
):
    """End-to-end through POST /sessions/{id}/reason."""
    from app.models.audit_log import AuditLogEntry
    from app.models.flag import Flag
    from app.models.safeguarding_escalation import SafeguardingEscalation
    from app.api.v1.endpoints.reasoning import get_reasoning_provider

    inst, staff, child, session = _tenant(db_session)
    token = _mint(settings, rsa_keypair, institution_id=inst.id, staff_id=staff.id)

    provider = ScriptedProvider(
        json.dumps({
            "signals": ["flinches at sudden movement"],
            "safeguarding_pattern": True,
            "key_items_missing": False,
        }),
    )
    client.app.dependency_overrides[get_reasoning_provider] = lambda: provider

    resp = client.post(
        f"/api/v1/sessions/{session.id}/reason",
        headers=_auth(token),
        json={"raw_input": SAFEGUARDING_INPUT},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "safeguarding_escalation"

    assert db_session.query(SafeguardingEscalation).count() == 1
    assert db_session.query(Flag).count() == 0
    actions = {
        e.action
        for e in db_session.query(AuditLogEntry)
        .filter(AuditLogEntry.resource_type.in_(["reasoning", "safeguarding_escalation"]))
        .all()
    }
    assert "reasoning.run" in actions
    assert "safeguarding.escalate" in actions


def test_safeguarding_service_has_no_flag_write_path():
    """Structural separation (sdlc-security rule 14): the safeguarding
    service exposes no flag-creation capability — the two tables never share
    a writer."""
    from app.services.safeguarding_service import SafeguardingService

    assert not hasattr(SafeguardingService, "create_flag")
    assert hasattr(SafeguardingService, "escalate")
