"""FEAT-07 — case memory & multi-session continuity.

Acceptance: two sessions for the same child, different dates — the second
session's agent context references the first session's flags.

Mechanics: before every reasoning step the pipeline loads the child's PRIOR
flags (all sessions except the current one) and injects a CASE MEMORY block
into the Risk Reasoning Agent's prompt; the result also carries
`prior_flags` so surfaces can show continuity. Never cross-child, never
cross-institution (RLS boundary unchanged).
"""

from __future__ import annotations

import datetime
import json
import uuid

import pytest

REFERENCE_DATE = datetime.date(2026, 8, 31)


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
def tenant(db_session):
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="FEAT-07 Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(staff)
    child = Child(
        institution_id=inst.id, name="Continuity Child",
        intake_date=datetime.date(2026, 7, 1),
        dob_confirmed=True, dob=datetime.date(2026, 1, 15),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return inst, staff, child


def _session(db_session, inst, staff, child):
    from app.models.session import Session as ConversationSession

    session = ConversationSession(
        institution_id=inst.id, child_id=child.id, staff_id=staff.id, mode="text"
    )
    db_session.add(session)
    db_session.flush()
    return session


class ScriptedProvider:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, agent, tier, system, user):
        self.calls.append({"agent": agent, "tier": tier, "system": system, "user": user})
        return self.responses.pop(0)


def _obs(signals):
    return json.dumps({"signals": signals, "safeguarding_pattern": False,
                       "key_items_missing": False})


def _reason(**kw):
    payload = {"concluded": True, "follow_up_question": None,
               "key_items_missing": False, "confirmed_red_flags": [],
               "missed_milestones": [], "met_milestones": [], "risk_modifiers": []}
    payload.update(kw)
    return json.dumps(payload)


def _run_flagged_turn(db_session, provider, session, child, staff, inst, text):
    from app.services.risk_pipeline import RiskPipeline

    return RiskPipeline(db_session, provider).run(
        session=session, child=child, caretaker_turns=[text],
        turn_number=1, staff_id=staff.id, institution_id=inst.id,
        reference_date=REFERENCE_DATE,
    )


def test_second_session_context_references_first_sessions_flag(
    db_session, tenant, loaded_kb
):
    inst, staff, child = tenant

    # Session 1 (earlier date): produces a Hearing flag.
    session_1 = _session(db_session, inst, staff, child)
    provider_1 = ScriptedProvider(
        _obs(["no response to sound"]),
        _reason(confirmed_red_flags=["HEAR-RF-003"]),
        "Please see a clinician soon.",
    )
    first = _run_flagged_turn(
        db_session, provider_1, session_1, child, staff, inst,
        "He doesn't react when I clap behind him",
    )
    assert first.outcome == "flagged"
    db_session.flush()

    # Session 2 (later): the reasoning context must reference session 1's flag.
    session_2 = _session(db_session, inst, staff, child)
    provider_2 = ScriptedProvider(
        _obs(["still no response"]),
        _reason(confirmed_red_flags=["HEAR-RF-003"]),
        "Still worth a clinician review.",
    )
    second = _run_flagged_turn(
        db_session, provider_2, session_2, child, staff, inst,
        "Still doesn't react to sounds",
    )
    assert second.outcome == "flagged"

    reasoning_call = next(
        c for c in provider_2.calls if c["agent"] == "risk_reasoning"
    )
    assert "CASE MEMORY" in reasoning_call["user"]
    assert "HEAR-RF-003" in reasoning_call["user"]

    # The result carries the prior flags for continuity surfaces.
    assert len(second.prior_flags) == 1
    assert second.prior_flags[0]["citations"] == ["HEAR-RF-003"]
    assert second.prior_flags[0]["grade"] == "high"
    assert second.prior_flags[0]["domain"] == "Hearing"


def test_first_session_has_no_case_memory(db_session, tenant, loaded_kb):
    inst, staff, child = tenant
    session = _session(db_session, inst, staff, child)
    provider = ScriptedProvider(
        _obs(["vague"]),
        _reason(key_items_missing=True),
    )
    result = _run_flagged_turn(
        db_session, provider, session, child, staff, inst, "not sure"
    )
    assert result.prior_flags == []
    reasoning_call = next(
        c for c in provider.calls if c["agent"] == "risk_reasoning"
    )
    assert "CASE MEMORY" not in reasoning_call["user"]


def test_case_memory_never_leaks_across_children(db_session, tenant, loaded_kb):
    """Another child's history must never appear in this child's context."""
    from app.models.child import Child

    inst, staff, child = tenant
    other_child = Child(
        institution_id=inst.id, name="Other Child",
        intake_date=datetime.date(2026, 7, 1),
        dob_confirmed=True, dob=datetime.date(2025, 6, 1),
        is_synthetic=True,
    )
    db_session.add(other_child)
    db_session.flush()

    # Flag on the OTHER child.
    other_session = _session(db_session, inst, staff, other_child)
    provider_other = ScriptedProvider(
        _obs(["regression"]),
        _reason(confirmed_red_flags=["SL-RF-008"]),
        "explanation",
    )
    _run_flagged_turn(
        db_session, provider_other, other_session, other_child, staff, inst,
        "lost words",
    )
    db_session.flush()

    # This child's new session must not see it.
    session = _session(db_session, inst, staff, child)
    provider = ScriptedProvider(
        _obs(["vague"]),
        _reason(key_items_missing=True),
    )
    result = _run_flagged_turn(
        db_session, provider, session, child, staff, inst, "something"
    )
    assert result.prior_flags == []
    reasoning_call = next(
        c for c in provider.calls if c["agent"] == "risk_reasoning"
    )
    assert "SL-RF-008" not in reasoning_call["user"]
