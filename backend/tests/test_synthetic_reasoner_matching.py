"""The synthetic reasoner must not invent evidence (operator-reported).

A caretaker described a five-year-old who was eating well and sleeping through
the night — no developmental content whatsoever — and the keyless demo path
returned **MODERATE · Speech_Language**, citing SL-RF-020 ("Marked word-finding
or comprehension difficulty") and SL-M-031. A referral for a child whose
caretaker had just said they were fine.

Cause: one missing comma.

    "phrases": ("something feels off")     # a str, not a tuple

Python reads that as a plain string, so `any(phrase in text for phrase in
phrases)` iterates its CHARACTERS — the concept matched on "s", on "o", on a
space. It fired on essentially every input at every age.

Two separate harms, and the second is the one that reaches a clinician:

  * `if not matched:` — the branch that routes unrecognised input to
    INSUFFICIENT_INFORMATION, the correct safe outcome — became unreachable
    for any input containing a space.
  * At 60-72 months (the band those refs live in) the spurious entries survived
    the age filter and were graded for real. Below that band they were filtered
    out, which is why the curated scenarios stayed green and this went unseen.

These tests are written against the DATA, not one phrase, because the defect is
a shape error that any future concept could repeat.
"""

from __future__ import annotations

import json

import pytest

from app.services.knowledge import (
    GRADE_INSUFFICIENT_INFORMATION,
    GRADE_MODERATE,
)
from app.services.llm import AGENT_OBSERVATION, AGENT_RISK_REASONING
from app.services.synthetic_llm import _CONCEPTS, SyntheticRuleLLM


def _reasoning_prompt(age_months: int, *turns: str) -> str:
    """The user-prompt shape RiskReasoningAgent actually sends."""
    transcript = "\n".join(
        f"turn {i}: <caretaker_input>{turn}</caretaker_input>"
        for i, turn in enumerate(turns, start=1)
    )
    return f"age: {age_months} months\n{transcript}"


def _reason(age_months: int, *turns: str) -> dict:
    return json.loads(
        SyntheticRuleLLM().complete(
            agent=AGENT_RISK_REASONING,
            tier="strong",
            system="",
            user=_reasoning_prompt(age_months, *turns),
        )
    )


# ── the shape invariant ─────────────────────────────────────────────────────


@pytest.mark.parametrize("concept", _CONCEPTS, ids=lambda c: c["name"])
def test_every_concept_declares_phrases_as_a_tuple(concept):
    """A bare string here is a silent character-matcher, not a phrase list.

    This is the assertion that would have caught the original defect at the
    moment it was written, and it costs nothing to keep.
    """
    phrases = concept["phrases"]
    assert isinstance(phrases, tuple), (
        f"{concept['name']}: phrases is {type(phrases).__name__}, not a tuple "
        f"— a missing trailing comma makes this match single CHARACTERS"
    )
    assert all(isinstance(p, str) and len(p) > 1 for p in phrases), (
        f"{concept['name']}: every phrase must be a real phrase, never a "
        f"single character"
    )


# ── the behaviour those shapes are supposed to produce ──────────────────────


def test_unrelated_report_about_a_five_year_old_produces_no_evidence():
    """The exact operator report. No developmental content in, no flag out."""
    payload = _reason(
        63,
        "She is eating well and sleeps through the night.",
        "Yes she is fine, nothing unusual at all.",
    )
    assert payload["concluded"] is True
    assert payload["confirmed_red_flags"] == []
    assert payload["missed_milestones"] == []
    # Specifically the two refs that were being invented.
    assert "SL-RF-020" not in payload["confirmed_red_flags"]
    assert "SL-M-031" not in payload["missed_milestones"]


def test_unrecognised_input_reaches_the_insufficient_information_floor(db_session):
    """End to end: what the reasoner returns must GRADE to the safe outcome.

    The grade inputs are resolved from the reasoner's own output against the
    real knowledge base — not hardcoded — so this fails if the reasoner starts
    citing again. Hardcoding empty lists here would assert nothing.
    """
    from app.services.knowledge import KnowledgeEntry, grade, load_knowledge_base
    from app.models.milestone import Milestone
    from sqlalchemy import select

    load_knowledge_base(db_session)
    payload = _reason(
        63,
        "She is eating well and sleeps through the night.",
        "Yes she is fine, nothing unusual at all.",
    )

    def resolve(refs: list[str]) -> list[KnowledgeEntry]:
        if not refs:
            return []
        rows = db_session.execute(
            select(Milestone).where(Milestone.citation_ref.in_(refs))
        ).scalars().all()
        return [KnowledgeEntry.from_row(row) for row in rows]

    result = grade(
        confirmed_flags=resolve(payload["confirmed_red_flags"]),
        missed_milestones=resolve(payload["missed_milestones"]),
        risk_modifiers=resolve(payload["risk_modifiers"]),
        key_items_missing=payload["key_items_missing"],
    )
    assert result.grade == GRADE_INSUFFICIENT_INFORMATION
    assert result.grade != GRADE_MODERATE
    assert result.citation_refs == []


def test_the_first_turn_no_longer_invents_a_follow_up_question():
    """It asked a 24-month-old's caretaker whether the child 'talks as much as
    other children her age' and 'hears and understands you' — the five-year-old
    script, on a two-year-old, burning one of five turns."""
    payload = _reason(24, "She is eating well and sleeps through the night.")
    assert payload["follow_up_question"] is None
    assert payload["concluded"] is True


def test_observation_signals_stay_empty_for_a_report_with_no_signals():
    """The same defect polluted extraction: 'vague five year old' was appended
    to the signals of essentially every observation, at every age."""
    payload = json.loads(
        SyntheticRuleLLM().complete(
            agent=AGENT_OBSERVATION,
            tier="cheap",
            system="",
            user=(
                "age: 63 months\n"
                "<caretaker_input>\nShe is eating well and sleeps through "
                "the night.\n</caretaker_input>"
            ),
        )
    )
    assert "vague five year old" not in payload["signals"]
    assert payload["safeguarding_pattern"] is False


# ── the scenario the concept exists FOR must still work ─────────────────────


def test_the_real_vague_report_still_resolves(  # T8 in the acceptance dataset
):
    """Regression guard on the fix itself: tightening the match must not
    silence the case this concept was written for. T8 — "Something feels off
    with her, I can't explain it exactly" at five years — expects
    MODERATE / Speech_Language via SL-RF-020 + SL-M-031."""
    first = _reason(63, "Something feels off with her, I can't explain it exactly")
    assert first["concluded"] is False
    assert first["follow_up_question"], "the vague report must draw a follow-up"

    second = _reason(
        63,
        "Something feels off with her, I can't explain it exactly",
        "She talks less than the other children and mixes up her words.",
    )
    assert second["concluded"] is True
    assert "SL-RF-020" in second["confirmed_red_flags"]
    assert "SL-M-031" in second["missed_milestones"]
