"""FEAT-04 — ADR-06 deterministic grading (pure function, no DB needed).

The grading rules live in app/services/knowledge.py::grade and must be
reproducible: same inputs -> same grade, with the exact citation_refs that
produced it (ADR-06 sub-rule 3). These tests pin every row of the ADR-06
table plus the binding sub-rules.
"""

from __future__ import annotations

import pytest

from app.services.knowledge import (
    GRADE_HIGH,
    GRADE_INSUFFICIENT_INFORMATION,
    GRADE_LOW_MONITOR,
    GRADE_MODERATE,
    KnowledgeEntry,
    grade,
)


def _entry(
    citation_ref: str,
    entry_type: str = "red_flag",
    domain: str = "Speech_Language",
    severity: str | None = "MODERATE",
) -> KnowledgeEntry:
    return KnowledgeEntry(
        citation_ref=citation_ref,
        entry_type=entry_type,
        domain=domain,
        age_min_months=0,
        age_max_months=72,
        description=f"synthetic entry {citation_ref}",
        severity=severity,
        cross_check_domain=None,
        suggested_follow_up_question=None,
        source="FEAT-04 grading test fixture",
        phase_scope="in scope (any age)",
        provenance="test fixture",
    )


def _flag(ref: str, severity: str = "MODERATE", domain: str = "Speech_Language"):
    return _entry(ref, entry_type="red_flag", domain=domain, severity=severity)


def _milestone(ref: str, domain: str = "Speech_Language"):
    return _entry(ref, entry_type="milestone", domain=domain, severity=None)


def _modifier(ref: str, domain: str = "Hearing"):
    return _entry(ref, entry_type="risk_modifier", domain=domain, severity="MODIFIER")


# ── HIGH triggers (ADR-06 table row 1) ──────────────────────────────────────


def test_one_high_flag_grades_high():
    result = grade(confirmed_flags=[_flag("SL-RF-021", severity="HIGH")])
    assert result.grade == GRADE_HIGH
    assert "SL-RF-021" in result.citation_refs


def test_two_moderate_flags_in_one_domain_grade_high():
    result = grade(
        confirmed_flags=[
            _flag("SL-RF-009", severity="MODERATE"),
            _flag("SL-RF-011", severity="MODERATE"),
        ]
    )
    assert result.grade == GRADE_HIGH
    assert set(result.citation_refs) >= {"SL-RF-009", "SL-RF-011"}


def test_two_moderate_flags_across_domains_do_not_grade_high():
    """Count-based rule is per-domain: one SL + one HEAR MODERATE is not
    '≥2 within the same domain', so the single-flag rule (MODERATE) holds."""
    result = grade(
        confirmed_flags=[
            _flag("SL-RF-009", severity="MODERATE"),
            _flag("HEAR-RF-005", severity="MODERATE", domain="Hearing"),
        ]
    )
    assert result.grade == GRADE_MODERATE


# ── MODERATE triggers (ADR-06 table row 2) ──────────────────────────────────


def test_one_moderate_flag_grades_moderate():
    result = grade(confirmed_flags=[_flag("HEAR-RF-005", severity="MODERATE", domain="Hearing")])
    assert result.grade == GRADE_MODERATE
    assert "HEAR-RF-005" in result.citation_refs


def test_missed_milestone_plus_supporting_observation_grades_moderate():
    """'Milestone missed at threshold plus one supporting observation' —
    red flags outweigh missed milestones, but a missed milestone is lifted
    to MODERATE when a second observation corroborates it."""
    result = grade(
        confirmed_flags=[_milestone("SL-M-021")],  # supporting observation
        missed_milestones=[_milestone("SL-M-019")],
    )
    assert result.grade == GRADE_MODERATE
    assert set(result.citation_refs) >= {"SL-M-019", "SL-M-021"}


# ── LOW_MONITOR trigger (ADR-06 table row 3, sub-rule 1) ────────────────────


def test_borderline_miss_with_protective_indicators_grades_low_monitor():
    result = grade(
        missed_milestones=[_milestone("SL-M-019")],
        risk_modifiers=[_modifier("SL-PROTECT-001", domain="Speech_Language")],
    )
    assert result.grade == GRADE_LOW_MONITOR
    assert "SL-M-019" in result.citation_refs
    assert "SL-PROTECT-001" in result.citation_refs


def test_bare_borderline_delay_never_discharges():
    """Sub-rule 1: no 'no concern' outcome — the floor is monitor & recheck."""
    result = grade(missed_milestones=[_milestone("SL-M-019")])
    assert result.grade == GRADE_LOW_MONITOR


# ── INSUFFICIENT_INFORMATION (sub-rule 2) ───────────────────────────────────


def test_missing_key_items_grades_insufficient_information():
    """Sub-rule 2: missing information is its own state, never LOW — even
    when some evidence exists."""
    result = grade(
        confirmed_flags=[_flag("HEAR-RF-005", severity="MODERATE", domain="Hearing")],
        key_items_missing=True,
    )
    assert result.grade == GRADE_INSUFFICIENT_INFORMATION
    assert "HEAR-RF-005" in result.citation_refs


def test_no_confirmed_evidence_grades_insufficient_information():
    result = grade()
    assert result.grade == GRADE_INSUFFICIENT_INFORMATION


def test_only_a_risk_modifier_grades_insufficient_information():
    """A bare modifier is not gradable evidence on its own."""
    result = grade(risk_modifiers=[_modifier("HEAR-RISK-01")])
    assert result.grade == GRADE_INSUFFICIENT_INFORMATION
    assert "HEAR-RISK-01" in result.citation_refs


# ── Risk modifiers raise, never lower (sub-rule 7) ──────────────────────────


def test_modifier_never_lowers_a_flag_grade():
    without = grade(confirmed_flags=[_flag("SL-RF-009", severity="MODERATE")])
    result = grade(
        confirmed_flags=[_flag("SL-RF-009", severity="MODERATE")],
        risk_modifiers=[_modifier("HEAR-RISK-01")],
    )
    assert result.grade == GRADE_MODERATE
    assert "HEAR-RISK-01" in result.citation_refs


def test_passed_newborn_screening_modifier_does_not_lower_hearing_concern():
    """Sub-rule 6: HEAR-RISK-02 explicitly forbids downgrading on the basis
    of a passed newborn screen — a HIGH hearing concern stays HIGH."""
    result = grade(
        confirmed_flags=[_flag("HEAR-RF-014", severity="HIGH", domain="Hearing")],
        risk_modifiers=[_modifier("HEAR-RISK-02")],
    )
    assert result.grade == GRADE_HIGH


# ── Estimated age (sub-rule 4, extends ADR-02) ──────────────────────────────


def test_estimated_age_borderline_delay_grades_down_to_monitor():
    result = grade(
        missed_milestones=[_milestone("SL-M-019")],
        age_is_estimated=True,
    )
    assert result.grade == GRADE_LOW_MONITOR
    assert result.age_uncertain is True


def test_estimated_age_regression_flag_grades_unchanged():
    """SL-RF-021 (loss of acquired skills) is age-independent — HIGH holds
    under estimated age, and the age uncertainty is still surfaced."""
    result = grade(
        confirmed_flags=[_flag("SL-RF-021", severity="HIGH")],
        age_is_estimated=True,
    )
    assert result.grade == GRADE_HIGH
    assert result.age_uncertain is True


def test_estimated_age_caretaker_hearing_concern_grades_unchanged():
    """HEAR-RF-014 (any caretaker hearing concern) is age-independent."""
    result = grade(
        confirmed_flags=[_flag("HEAR-RF-014", severity="HIGH", domain="Hearing")],
        age_is_estimated=True,
    )
    assert result.grade == GRADE_HIGH
    assert result.age_uncertain is True


# ── Auditability + determinism (sub-rule 3) ─────────────────────────────────


@pytest.mark.parametrize(
    "kwargs",
    [
        {"confirmed_flags": [_flag("SL-RF-021", severity="HIGH")]},
        {
            "confirmed_flags": [
                _flag("SL-RF-009"),
                _flag("SL-RF-011"),
            ]
        },
        {"confirmed_flags": [_flag("HEAR-RF-005", domain="Hearing")]},
        {"missed_milestones": [_milestone("SL-M-019")]},
        {"key_items_missing": True},
        {},
        {"missed_milestones": [_milestone("SL-M-019")], "age_is_estimated": True},
    ],
    ids=[
        "high-flag",
        "two-moderate-same-domain",
        "one-moderate",
        "borderline-miss",
        "key-items-missing",
        "no-evidence",
        "estimated-age-borderline",
    ],
)
def test_every_grade_carries_non_empty_citation_refs(kwargs):
    """Sub-rule 3: every grade produced from ANY evidence enumerates the
    citation_refs behind it (the only exemption is the literally-zero-
    evidence case, where no refs exist to cite)."""
    result = grade(**kwargs)
    has_evidence = kwargs.get("confirmed_flags") or kwargs.get("missed_milestones")
    if has_evidence or kwargs.get("key_items_missing") and has_evidence:
        assert result.citation_refs, f"{result.grade} returned without citation_refs"


def test_grading_is_deterministic():
    flags = [_flag("SL-RF-009"), _flag("SL-RF-011")]
    missed = [_milestone("SL-M-019")]
    modifiers = [_modifier("HEAR-RISK-01")]
    first = grade(flags, missed, risk_modifiers=modifiers, age_is_estimated=True)
    second = grade(flags, missed, risk_modifiers=modifiers, age_is_estimated=True)
    assert first == second
