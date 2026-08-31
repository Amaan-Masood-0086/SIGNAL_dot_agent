"""FEAT-06 — Adaptive Follow-Up Loop acceptance.

Backlog acceptance: "at least one follow-up question demonstrably changes
the final flag's confidence grade or domain, in a test conversation."

The loop MECHANICS (follow_up outcomes, discriminating questions from
suggested_follow_up_question, max_turns=5 cap) shipped with FEAT-05; this
module pins the acceptance bar against them:

- SAME opening + a protective answer → LOW_MONITOR; SAME opening + a
  concerning answer → HIGH. The follow-up is what separates the two.
- A forced conclusion on the opening alone files Speech_Language; once the
  discriminating follow-up is answered, the SAME opening files Hearing —
  the domain is decided after the joint check, not before (ADR-05).
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
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="FEAT-06 Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return inst, staff


def _child(db_session, inst, months):
    from app.models.child import Child

    total = REFERENCE_DATE.year * 12 + (REFERENCE_DATE.month - 1) - months
    child = Child(
        institution_id=inst.id, name="Loop Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=True,
        dob=datetime.date(total // 12, total % 12 + 1, 15),
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


def _conversation(db_session, inst, staff, child):
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

    def complete(self, *, agent, tier, system, user):
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


OPENING = "Something feels off with her speech, I can't explain it exactly"


def _run_two_turn(db_session, tenant, provider, response_text, *, months=60):
    from app.services.risk_pipeline import RiskPipeline

    inst, staff = tenant
    child = _child(db_session, inst, months)
    session = _conversation(db_session, inst, staff, child)
    pipeline = RiskPipeline(db_session, provider)

    first = pipeline.run(
        session=session, child=child, caretaker_turns=[OPENING],
        turn_number=1, staff_id=staff.id, institution_id=inst.id,
        reference_date=REFERENCE_DATE,
    )
    assert first.outcome == "follow_up"
    assert first.follow_up_question  # the loop asked something material

    second = pipeline.run(
        session=session, child=child,
        caretaker_turns=[OPENING, response_text],
        turn_number=2, staff_id=staff.id, institution_id=inst.id,
        reference_date=REFERENCE_DATE,
    )
    return first, second


def test_follow_up_answer_changes_the_grade(db_session, tenant, loaded_kb):
    """The SAME vague opening resolves to LOW_MONITOR with a protective
    answer and MODERATE with a concerning one — the follow-up demonstrably
    changes the final grade (FEAT-06 acceptance)."""
    protective = ScriptedProvider(
        _obs(["vague concern"]),
        _reason(concluded=False,
                follow_up_question="Does she talk as much as other 5-year-olds?"),
        _obs(["understands fine, talks less"]),
        _reason(missed_milestones=["SL-M-031"]),
        "Near the expected range; recheck in three months.",
    )
    _, protective_result = _run_two_turn(
        db_session, tenant, protective,
        "She understands everything, just a bit quiet",
    )

    concerning = ScriptedProvider(
        _obs(["vague concern"]),
        _reason(concluded=False,
                follow_up_question="Does she hear and understand you?"),
        _obs(["much less speech, mostly watches"]),
        _reason(confirmed_red_flags=["SL-RF-020"], missed_milestones=["SL-M-031"]),
        "Please have a clinician review this.",
    )
    _, concerning_result = _run_two_turn(
        db_session, tenant, concerning,
        "Much less than others, mostly just watches",
    )

    assert protective_result.grade == "LOW_MONITOR"
    assert concerning_result.grade == "MODERATE"
    assert protective_result.grade != concerning_result.grade


def test_follow_up_answer_changes_the_domain(db_session, tenant, loaded_kb):
    """Forced to conclude on the opening alone, the flag files under
    Speech_Language; once the discriminating follow-up is answered, the SAME
    opening files under Hearing — domain decided AFTER the joint check."""
    from app.services.risk_pipeline import MAX_TURNS, RiskPipeline

    inst, staff = tenant

    # Path A: no follow-up — forced conclusion at the cap reads the opening
    # as a borderline Speech_Language delay (the naive single-domain read).
    child_a = _child(db_session, inst, 36)
    session_a = _conversation(db_session, inst, staff, child_a)
    provider_a = ScriptedProvider(
        _obs(["doesn't talk much"]),
        _reason(missed_milestones=["SL-M-017"]),
        "explanation",
    )
    forced = RiskPipeline(db_session, provider_a).run(
        session=session_a, child=child_a, caretaker_turns=[OPENING],
        turn_number=MAX_TURNS, staff_id=staff.id, institution_id=inst.id,
        reference_date=REFERENCE_DATE,
    )
    assert forced.loop_exhausted is True
    assert forced.domain == "Speech_Language"
    assert forced.grade == "LOW_MONITOR"

    # Path B: the discriminating follow-up IS asked and answered.
    provider_b = ScriptedProvider(
        _obs(["doesn't talk much", "doesn't listen"]),
        _reason(concluded=False,
                follow_up_question=(
                    "Does he respond when you call him from behind, "
                    "where he can't see you?"
                )),
        _obs(["no reaction to sound from behind"]),
        _reason(confirmed_red_flags=["HEAR-RF-013", "HEAR-RF-008"]),
        "Hearing should be checked soon.",
    )
    first, final = _run_two_turn(
        db_session, tenant, provider_b,
        "No reaction at all to sounds behind him",
        months=36,
    )
    assert first.follow_up_question and "behind" in first.follow_up_question
    assert final.domain == "Hearing"
    assert final.grade == "HIGH"
    # The loop demonstrably changed the outcome: the forced no-follow-up
    # reading never reached this Hearing-high conclusion from the same turn.
    assert (forced.grade, forced.domain) != (final.grade, final.domain)
