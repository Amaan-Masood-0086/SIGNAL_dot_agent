"""FEAT-05 dataset contract — signal_test_conversations_v2.csv vs FEAT-04 layer.

The Risk Reasoning Agent's evaluation dataset (13 conversations, Ayesha
originals + validation additions) can be audited BEFORE FEAT-05 exists:

- every expected citation_ref must exist in the ingested knowledge base
  (ADR-03/08: no dangling citations — same rule as flags.reasoning_trail)
- each ref's domain/severity must match what the conversation expects
- refs expected to be confirmable at the child's age must actually be
  returned by retrieve_in_scope_entries at that age (except known
  protective-indicator gaps, documented per-case below)
- the out-of-phase conversation (T13, 9 yr) must get an empty retrieval
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from app.services.knowledge import (
    PHASE_2_PREFIX,
    load_knowledge_base,
    parse_knowledge_csv,
    retrieve_in_scope_entries,
)

SOURCE_DIR = (
    Path(__file__).resolve().parents[2]
    / ".ai"
    / "brain"
    / "knowledge-base-source"
)
CSV_PATH = SOURCE_DIR / "signal_knowledge_base_v2.csv"
CONVO_PATH = SOURCE_DIR / "signal_test_conversations_v2.csv"

_REF_RE = re.compile(r"((?:SL|HEAR)-(?:M|RF|RISK)-\d+)")


def _age_months(age: str) -> int:
    """'8 mo' -> 8, '3 yr' -> 36."""
    value, unit = age.split()
    value = int(value)
    return value if unit == "mo" else value * 12


def _load_conversations() -> list[dict]:
    with open(CONVO_PATH, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


CONVERSATIONS = _load_conversations()
ENTRIES = {e.citation_ref: e for e in parse_knowledge_csv(CSV_PATH)}


@pytest.fixture(scope="module")
def loaded_db_module(pg_engine):
    """Module-scoped loaded DB: this file only reads, never writes."""
    from sqlalchemy.orm import Session

    with Session(pg_engine) as db:
        load_knowledge_base(db, csv_path=CSV_PATH)
        yield db


def test_dataset_has_the_expected_shape():
    assert len(CONVERSATIONS) == 13
    ids = [row["id"] for row in CONVERSATIONS]
    assert ids == [f"T{n}" for n in range(1, 14)]
    # cross-domain binding cases (ADR-05 / TEST_PLAN §3a) are present
    t5 = next(row for row in CONVERSATIONS if row["id"] == "T5")
    assert t5["expected_domain"] == "Hearing"  # resolves to Hearing, not SL
    t10 = next(row for row in CONVERSATIONS if row["id"] == "T10")
    assert t10["expected_grade"] == "safeguarding_escalation"


@pytest.mark.parametrize(
    "row", CONVERSATIONS, ids=[row["id"] for row in CONVERSATIONS]
)
def test_every_expected_citation_exists_in_knowledge_base(row):
    """No dangling citation — every ref the dataset expects must resolve to
    a real ingested row (the same integrity rule as flags.reasoning_trail)."""
    refs = _REF_RE.findall(row["expected_citations"]) if _REF_RE.search(
        row["expected_citations"]
    ) else []
    if row["expected_grade"] in ("safeguarding_escalation",) or row["id"] == "T9":
        assert refs == []  # routes out of developmental grading / nothing confirmable
        return
    assert refs, f"{row['id']}: expected_citations column unparseable"
    for ref in refs:
        assert ref in ENTRIES, f"{row['id']}: {ref} not in knowledge base"


@pytest.mark.parametrize(
    "row", CONVERSATIONS, ids=[row["id"] for row in CONVERSATIONS]
)
def test_cited_domains_match_expected_domain(row):
    if row["expected_domain"] == "—" or not _REF_RE.search(row["expected_citations"]):
        return
    for ref in _REF_RE.findall(row["expected_citations"]):
        entry = ENTRIES[ref]
        assert entry.domain == row["expected_domain"], (
            f"{row['id']}: {ref} is {entry.domain}, conversation expects "
            f"{row['expected_domain']}"
        )


def test_always_high_cases_cite_high_severity_flags():
    """T4, T5, T11, T12 expect HIGH via at least one HIGH-severity red flag
    (grade = max(highest single-flag severity, ...) makes HIGH automatic)."""
    for convo_id in ("T1", "T4", "T5", "T11", "T12"):
        row = next(r for r in CONVERSATIONS if r["id"] == convo_id)
        refs = _REF_RE.findall(row["expected_citations"])
        severities = [ENTRIES[ref].severity for ref in refs]
        assert "HIGH" in severities, f"{convo_id}: no HIGH flag among {refs}"


def test_moderate_cases_have_no_high_flag():
    """T6/T8 expect MODERATE — no HIGH-severity flag may be among the cites.
    NOTE: T6's three MODERATE flags still grade HIGH under ADR-06's literal
    count rule — that is the R14 known divergence, pinned by the T6 tests
    at the bottom of this file. Do not 'fix' either side until sign-off."""
    for convo_id in ("T6", "T8"):
        row = next(r for r in CONVERSATIONS if r["id"] == convo_id)
        refs = _REF_RE.findall(row["expected_citations"])
        severities = [ENTRIES[ref].severity for ref in refs]
        assert "HIGH" not in severities, f"{convo_id}: HIGH flag among {refs}"


# Met-milestone / protective-indicator citations whose age band lies BELOW
# the child's age — they are cited as "already passed" evidence (T2/T7 at
# 30 mo cite the 18-24 band), so they are intentionally outside the
# age-band retrieval. FEAT-05 design note: the agent's prompt context is
# the whole in-scope table (ADR-04 full-context injection), so these refs
# remain citable even though the age-band query does not return them.
MET_OUT_OF_BAND = {
    "T2": {"SL-M-017"},
    "T7": {"SL-M-017", "SL-M-018"},
}


@pytest.mark.parametrize(
    "row", CONVERSATIONS, ids=[row["id"] for row in CONVERSATIONS]
)
def test_cited_refs_are_retrievable_at_child_age(loaded_db_module, row):
    if row["expected_domain"] == "—" or not _REF_RE.search(row["expected_citations"]):
        return
    age = _age_months(row["age"])
    returned = {e.citation_ref for e in retrieve_in_scope_entries(loaded_db_module, age)}
    exempt = MET_OUT_OF_BAND.get(row["id"], set())
    for ref in _REF_RE.findall(row["expected_citations"]):
        if ref in exempt:
            continue
        if ENTRIES[ref].phase_scope.startswith(PHASE_2_PREFIX):
            # T13: PHASE 2 refs are expected to be EXCLUDED at a Phase 1 age
            assert ref not in returned
        else:
            assert ref in returned, (
                f"{row['id']}: {ref} not returned at age {age} — band "
                f"{ENTRIES[ref].age_min_months}-{ENTRIES[ref].age_max_months}"
            )


def test_out_of_phase_conversation_gets_empty_phase1_retrieval(loaded_db_module):
    """T13 (9 yr = 108 mo) is marked OUT OF PHASE 1 SCOPE: at that age the
    in-scope retrieval must be empty (all 0-72 bands and bands up to 72 are
    out of range; the PHASE 2 rows are never returned)."""
    row = next(r for r in CONVERSATIONS if r["id"] == "T13")
    assert retrieve_in_scope_entries(loaded_db_module, _age_months(row["age"])) == []


# ── T6 OME pattern: documented known divergence (R14) ───────────────────────
# T6 confirms three MODERATE-severity Hearing red flags (HEAR-RF-009/010/016).
# ADR-06's literal count rule (≥2 MODERATE in the same domain → HIGH) grades
# it HIGH; the delivered dataset expects MODERATE, backed by
# signal_grading_rules_v2.csv's OME note. This divergence is tracked in
# ADR-06 "Open Sub-Question — Found During FEAT-05 Dataset Audit (2026-08-31)"
# and RISK_REGISTER R14. Per both: do NOT implement a carve-out or OME
# exception speculatively — grade() keeps the literal rule; the expected
# value for T6 awaits Ayesha/Sami clinical sign-off.

T6_REFS = ("HEAR-RF-009", "HEAR-RF-010", "HEAR-RF-016")


def test_t6_grades_high_under_adr06_literal_count_rule():
    """PINS the currently-mandated behavior: three confirmed MODERATE flags
    in one domain grade HIGH per ADR-06's literal rule. Must stay green."""
    from app.services.knowledge import GRADE_HIGH, grade

    result = grade(confirmed_flags=[ENTRIES[ref] for ref in T6_REFS])
    assert result.grade == GRADE_HIGH
    assert set(result.citation_refs) >= set(T6_REFS)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "KNOWN DIVERGENCE (R14): dataset T6 expects MODERATE, but ADR-06's "
        "literal count rule computes HIGH. See ADR_06 'Open Sub-Question' "
        "(2026-08-31) and RISK_REGISTER R14 — resolution awaits Ayesha/Sami "
        "clinical sign-off; no speculative fix allowed. If this test starts "
        "passing, the divergence was resolved: update expectations and "
        "remove this marker."
    ),
)
def test_t6_dataset_expectation_moderate_is_a_documented_divergence():
    from app.services.knowledge import GRADE_MODERATE, grade

    result = grade(confirmed_flags=[ENTRIES[ref] for ref in T6_REFS])
    assert result.grade == GRADE_MODERATE
