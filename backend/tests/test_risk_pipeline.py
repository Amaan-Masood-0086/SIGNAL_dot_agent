"""FEAT-05 pipeline orchestration — Observation → Risk Reasoning → Explanation.

Pins the ticket's risk-reasoning contract end-to-end at the service level
(endpoint-level E2E lives in test_feat05_pipeline_e2e.py):
- single joint retrieval call, BOTH domains always (ADR-05)
- estimated age → YOUNGER bound + age_uncertain surfaced (ADR-02)
- safeguarding pattern routes OUT with zero flags (FEAT-11 owns the write)
- grade() output untouched; INSUFFICIENT_INFORMATION writes no flag row
- domain decided AFTER the joint check (Hearing live differential)
- adaptive loop hard-stops at max_turns=5 with a forced conclusion
- every LLM call lands exactly one usage_log row (RBAC-ticket seam)
"""

from __future__ import annotations

import datetime
import json
import uuid

import pytest


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
    # Keep the shared session DB clean for the FEAT-04 loader tests.
    session.execute(delete(Milestone))
    session.commit()
    session.close()


@pytest.fixture()
def tenant(db_session):
    from app.models.institution import Institution
    from app.models.staff import Staff

    inst = Institution(name="Pipeline Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused",
        role="caretaker",
        is_synthetic=True,
    )
    db_session.add(staff)
    db_session.flush()
    return {"institution": inst, "staff": staff}


def _child(db_session, tenant, *, dob_confirmed=True, dob=None, age_range=None):
    from app.models.child import Child

    child = Child(
        institution_id=tenant["institution"].id,
        name="Pipeline Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=dob_confirmed,
        dob=dob if dob_confirmed else None,
        estimated_age_range=None if dob_confirmed else age_range,
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    return child


def _conversation(db_session, tenant, child):
    from app.models.session import Session as ConversationSession

    session = ConversationSession(
        institution_id=tenant["institution"].id,
        child_id=child.id,
        staff_id=tenant["staff"].id,
        mode="text",
    )
    db_session.add(session)
    db_session.flush()
    return session


def _obs_json(signals, *, safeguarding=False, key_missing=False):
    return json.dumps({
        "signals": signals,
        "safeguarding_pattern": safeguarding,
        "key_items_missing": key_missing,
    })


def _reason_json(**overrides):
    payload = {
        "concluded": True,
        "follow_up_question": None,
        "key_items_missing": False,
        "confirmed_red_flags": [],
        "missed_milestones": [],
        "met_milestones": [],
        "risk_modifiers": [],
    }
    payload.update(overrides)
    return json.dumps(payload)


class ScriptedProvider:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, agent, tier, system, user):
        self.calls.append({"agent": agent, "tier": tier, "system": system, "user": user})
        return self.responses.pop(0)


REFERENCE_DATE = datetime.date(2026, 8, 31)


def _pipeline(db_session, provider):
    from app.services.risk_pipeline import RiskPipeline

    return RiskPipeline(db_session, provider)


def _run(db_session, tenant, provider, *, child, turns, turn=None):
    session = _conversation(db_session, tenant, child)
    return _pipeline(db_session, provider).run(
        session=session,
        child=child,
        caretaker_turns=turns,
        turn_number=turn if turn is not None else len(turns),
        staff_id=tenant["staff"].id,
        institution_id=tenant["institution"].id,
        reference_date=REFERENCE_DATE,
    )


# ── Age resolution (ADR-02) ──────────────────────────────────────────────────


def test_confirmed_dob_evaluates_at_exact_age(db_session, tenant, loaded_kb):
    # 30 months before 2026-08-31 → dob 2024-02-28.
    child = _child(db_session, tenant, dob=datetime.date(2024, 2, 28))
    provider = ScriptedProvider(
        _obs_json(["limited speech"]),
        _reason_json(confirmed_red_flags=[], missed_milestones=["SL-M-017"]),
        "near the expected range; recheck in three months",
    )
    result = _run(db_session, tenant, provider, child=child, turns=["she barely talks"])

    assert result.age_uncertain is False
    reasoning_call = next(c for c in provider.calls if c["agent"] == "risk_reasoning")
    assert "age: 30 months" in reasoning_call["user"]


def test_estimated_age_evaluates_at_younger_bound_and_surfaces_uncertainty(
    db_session, tenant, loaded_kb
):
    child = _child(db_session, tenant, dob_confirmed=False, age_range="24-36 months")
    provider = ScriptedProvider(
        _obs_json(["limited speech"]),
        _reason_json(),
    )
    result = _run(db_session, tenant, provider, child=child, turns=["she barely talks"])

    assert result.age_uncertain is True
    reasoning_call = next(c for c in provider.calls if c["agent"] == "risk_reasoning")
    assert "dob_confirmed=false" in reasoning_call["user"]
    assert "24 months" in reasoning_call["user"]  # YOUNGER bound drives evaluation


# ── Safeguarding boundary (T10 semantics) ────────────────────────────────────


def test_safeguarding_pattern_routes_out_with_zero_flags(db_session, tenant, loaded_kb):
    child = _child(db_session, tenant, dob=datetime.date(2022, 8, 1))
    provider = ScriptedProvider(
        _obs_json(["flinches when adults move suddenly"], safeguarding=True),
    )
    result = _run(
        db_session, tenant, provider, child=child,
        turns=["She's very withdrawn and flinches when anyone moves suddenly"],
    )

    from app.models.flag import Flag

    assert result.outcome == "safeguarding_escalation"
    assert result.grade is None
    assert db_session.query(Flag).count() == 0
    # The reasoning/explanation agents are never invoked on the safeguarding
    # path; the escalation row is written by the SEPARATE safeguarding
    # service (FEAT-11) — no shared code path with flags.
    assert [c["agent"] for c in provider.calls] == ["observation"]
    from app.models.safeguarding_escalation import SafeguardingEscalation

    assert db_session.query(SafeguardingEscalation).count() == 1


# ── Grounded grading + flag persistence ─────────────────────────────────────


def test_high_hearing_flag_persisted_with_real_trail(db_session, tenant, loaded_kb):
    child = _child(db_session, tenant, dob=datetime.date(2026, 1, 1))  # 8 mo
    provider = ScriptedProvider(
        _obs_json(["no response to loud sounds"]),
        _reason_json(confirmed_red_flags=["HEAR-RF-003"]),
        "He may not be hearing sounds the way other children do. Please see a doctor soon.",
    )
    result = _run(
        db_session, tenant, provider, child=child,
        turns=["He doesn't turn around even when I clap loudly behind him"],
    )

    from app.models.flag import Flag

    assert result.outcome == "flagged"
    assert result.grade == "HIGH"
    assert result.domain == "Hearing"
    assert result.citation_refs == ["HEAR-RF-003"]

    flags = db_session.query(Flag).all()
    assert len(flags) == 1
    flag = flags[0]
    assert flag.confidence_grade == "high"
    assert flag.domain == "Hearing"
    assert flag.status == "flagged"
    assert flag.reasoning_trail[0]["citation_ref"] == "HEAR-RF-003"
    assert flag.explanation_text


def test_insufficient_information_writes_no_flag_row(db_session, tenant, loaded_kb):
    child = _child(db_session, tenant, dob=datetime.date(2024, 8, 1))
    provider = ScriptedProvider(
        _obs_json(["vague concern"], key_missing=True),
        _reason_json(key_items_missing=True),
    )
    result = _run(
        db_session, tenant, provider, child=child,
        turns=["I think something might be off but I only met him this week"],
    )

    from app.models.flag import Flag

    assert result.outcome == "insufficient_information"
    assert result.grade == "INSUFFICIENT_INFORMATION"
    assert db_session.query(Flag).count() == 0
    # No explanation LLM call — the fixed safe wording is deterministic.
    assert "explanation" not in {c["agent"] for c in provider.calls}


def test_domain_decided_after_joint_check_resolves_to_hearing(
    db_session, tenant, loaded_kb
):
    """CD-1 core: the opening sounds like speech delay, but the joint check
    confirms Hearing red flags — the flag is filed under Hearing (ADR-05)."""
    child = _child(db_session, tenant, dob=datetime.date(2023, 8, 15))  # ~37 mo
    provider = ScriptedProvider(
        _obs_json(["doesn't talk much", "doesn't listen when called"]),
        _reason_json(confirmed_red_flags=["HEAR-RF-013", "HEAR-RF-011", "HEAR-RF-008"]),
        "plain explanation",
    )
    result = _run(
        db_session, tenant, provider, child=child,
        turns=["Doesn't talk much and doesn't seem to listen when I call him"],
    )
    assert result.domain == "Hearing"
    assert result.grade == "HIGH"


def test_met_milestones_ride_the_trail_as_protective_evidence(
    db_session, tenant, loaded_kb
):
    """T3 pattern: borderline norm below average (SL-M-015) plus protective
    met milestones → LOW_MONITOR floor, protective refs cited alongside."""
    child = _child(db_session, tenant, dob=datetime.date(2025, 2, 15))  # 18 mo
    provider = ScriptedProvider(
        _obs_json(["only about 5 words"]),
        _reason_json(
            missed_milestones=["SL-M-015"],
            met_milestones=["SL-M-012", "SL-M-014"],
        ),
        "near the expected range; recheck in three months",
    )
    result = _run(
        db_session, tenant, provider, child=child,
        turns=["He only says about 5 words, is that bad?"],
    )
    assert result.grade == "LOW_MONITOR"
    assert result.domain == "Speech_Language"
    assert set(result.citation_refs) >= {"SL-M-015", "SL-M-012", "SL-M-014"}

    from app.models.flag import Flag

    trail_refs = {e["citation_ref"] for e in db_session.query(Flag).one().reasoning_trail}
    assert trail_refs >= {"SL-M-015", "SL-M-012", "SL-M-014"}


def test_grounding_violation_propagates(db_session, tenant, loaded_kb):
    """A hallucinated citation is never rationalized away — it fails the run."""
    from app.services.pipeline_agents import GroundingError

    child = _child(db_session, tenant, dob=datetime.date(2026, 1, 1))
    provider = ScriptedProvider(
        _obs_json(["some concern"]),
        _reason_json(confirmed_red_flags=["HEAR-RF-777"]),
    )
    with pytest.raises(GroundingError):
        _run(db_session, tenant, provider, child=child, turns=["something seems off"])


# ── Adaptive loop cap (max_turns=5) ─────────────────────────────────────────


def test_loop_hard_stops_at_five_turns_with_forced_conclusion(
    db_session, tenant, loaded_kb
):
    child = _child(db_session, tenant, dob=datetime.date(2024, 8, 1))
    session = _conversation(db_session, tenant, child)
    # Interleaved exactly as the pipeline consumes: observation, then
    # reasoning, per turn.
    responses = []
    for i in range(4):
        responses.append(_obs_json(["vague"]))
        responses.append(
            _reason_json(concluded=False, follow_up_question=f"q{i}")
        )
    responses.append(_obs_json(["still vague"]))
    responses.append(
        _reason_json(concluded=False, follow_up_question="another question")
    )
    pipeline = _pipeline(db_session, ScriptedProvider(*responses))

    turns = []
    for turn in range(1, 6):
        turns.append(f"caretaker answer {turn}")
        result = pipeline.run(
            session=session,
            child=child,
            caretaker_turns=list(turns),
            turn_number=turn,
            staff_id=tenant["staff"].id,
            institution_id=tenant["institution"].id,
            reference_date=REFERENCE_DATE,
        )
        if turn < 5:
            assert result.outcome == "follow_up"
            assert result.follow_up_question == f"q{turn - 1}"
        else:
            # Forced conclusion at turn 5 — never another follow-up.
            assert result.outcome != "follow_up"
            assert result.loop_exhausted is True

    # The forced-conclusion prompt said so explicitly.
    last_reasoning = [c for c in pipeline.provider.calls if c["agent"] == "risk_reasoning"][-1]
    assert "must conclude" in last_reasoning["user"].lower()


def test_sixth_turn_is_refused_after_cap(db_session, tenant, loaded_kb):
    from app.services.risk_pipeline import LoopCapExceeded

    child = _child(db_session, tenant, dob=datetime.date(2024, 8, 1))
    session = _conversation(db_session, tenant, child)
    pipeline = _pipeline(db_session, ScriptedProvider())
    with pytest.raises(LoopCapExceeded):
        pipeline.run(
            session=session,
            child=child,
            caretaker_turns=["one"] * 6,
            turn_number=6,
            staff_id=tenant["staff"].id,
            institution_id=tenant["institution"].id,
            reference_date=REFERENCE_DATE,
        )


# ── Usage ledger: one row per LLM call (RBAC-ticket seam) ───────────────────


def test_every_llm_call_records_exactly_one_usage_row(db_session, tenant, loaded_kb):
    child = _child(db_session, tenant, dob=datetime.date(2026, 1, 1))
    provider = ScriptedProvider(
        _obs_json(["no response to loud sounds"]),
        _reason_json(confirmed_red_flags=["HEAR-RF-003"]),
        "plain explanation",
    )
    _run(
        db_session, tenant, provider, child=child,
        turns=["He doesn't turn around when I clap"],
    )

    from app.models.usage_log import UsageLog

    rows = db_session.query(UsageLog).all()
    assert len(rows) == 3  # observation + risk_reasoning + explanation — no more
    assert [row.provider for row in rows] == ["llm", "llm", "llm"]
    assert sorted(row.call_type for row in rows) == sorted(
        ["observation", "risk_reasoning", "explanation"]
    )
    for row in rows:
        assert row.staff_id == tenant["staff"].id
        assert row.institution_id == tenant["institution"].id


def test_follow_up_turn_records_no_explanation_usage(db_session, tenant, loaded_kb):
    child = _child(db_session, tenant, dob=datetime.date(2024, 8, 1))
    provider = ScriptedProvider(
        _obs_json(["vague"]),
        _reason_json(concluded=False, follow_up_question="does he react to sound?"),
    )
    result = _run(db_session, tenant, provider, child=child, turns=["something feels off"])
    assert result.outcome == "follow_up"

    from app.models.usage_log import UsageLog

    types = {row.call_type for row in db_session.query(UsageLog).all()}
    assert types == {"observation", "risk_reasoning"}


def test_usage_rows_carry_llm_cost_when_provider_reports_it(db_session, tenant, loaded_kb):
    """The cost model is best-effort but must reach the ledger when the
    provider exposes last_call_cost (adapter contract)."""
    from decimal import Decimal

    child = _child(db_session, tenant, dob=datetime.date(2026, 1, 1))
    provider = ScriptedProvider(
        _obs_json(["no response to loud sounds"]),
        _reason_json(confirmed_red_flags=["HEAR-RF-003"]),
        "plain explanation",
    )
    provider.last_call_cost = Decimal("0.000321")
    _run(
        db_session, tenant, provider, child=child,
        turns=["He doesn't turn around when I clap"],
    )

    from app.models.usage_log import UsageLog

    rows = db_session.query(UsageLog).all()
    assert len(rows) == 3
    assert all(row.estimated_cost == Decimal("0.000321") for row in rows)
