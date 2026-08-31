"""FEAT-04 — knowledge-base ingestion + pipeline query interface.

All tests run against real PostgreSQL (conftest.py::pg_engine, Alembic head).
The CSV row count, phase-scope split, and any-age set are computed from the
real dataset, never hard-coded.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.milestone import Milestone
from app.services.knowledge import (
    PHASE_2_PREFIX,
    load_knowledge_base,
    parse_knowledge_csv,
    retrieve_in_scope_entries,
)

CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / ".ai"
    / "brain"
    / "knowledge-base-source"
    / "signal_knowledge_base_v2.csv"
)

ENTRIES = parse_knowledge_csv(CSV_PATH)
TOTAL_ROWS = len(ENTRIES)
PHASE2_REFS = {e.citation_ref for e in ENTRIES if e.phase_scope.startswith(PHASE_2_PREFIX)}
ANY_AGE_REFS = {
    e.citation_ref
    for e in ENTRIES
    if e.age_min_months == 0 and e.age_max_months == 72
    and not e.phase_scope.startswith(PHASE_2_PREFIX)
}


@pytest.fixture()
def loaded_db(db_session):
    """Session with the real knowledge base ingested (rolled back on teardown)."""
    load_knowledge_base(db_session, csv_path=CSV_PATH)
    return db_session


def _refs(rows) -> set[str]:
    return {row.citation_ref for row in rows}


# ── Row count + identity invariants ─────────────────────────────────────────


def test_loaded_row_count_matches_csv(loaded_db):
    rows = loaded_db.execute(select(Milestone)).scalars().all()
    assert len(rows) == TOTAL_ROWS
    assert _refs(rows) == {e.citation_ref for e in ENTRIES}


def test_csv_itself_has_unique_citation_refs():
    refs = [e.citation_ref for e in ENTRIES]
    assert len(refs) == len(set(refs)), "source CSV contains duplicate citation_refs"


def test_duplicate_citation_ref_is_rejected_by_database(loaded_db):
    """ADR-08: the unique index is a DB guarantee, not loader politeness."""
    original = loaded_db.execute(
        select(Milestone).where(Milestone.citation_ref == "SL-RF-009")
    ).scalar_one()
    duplicate = Milestone(
        citation_ref="SL-RF-009",
        entry_type="red_flag",
        domain="Speech_Language",
        age_min_months=24,
        age_max_months=24,
        description="duplicate",
        severity="HIGH",
        source="test",
        phase_scope="in scope",
        provenance="test",
    )
    nested = loaded_db.begin_nested()
    with pytest.raises(IntegrityError):
        loaded_db.add(duplicate)
        loaded_db.flush()
    nested.rollback()  # unwind only to the savepoint; outer load stays intact
    still_one = loaded_db.execute(
        select(Milestone).where(Milestone.citation_ref == "SL-RF-009")
    ).scalars().all()
    assert len(still_one) == 1 and still_one[0].id == original.id


def test_milestone_model_exposes_full_csv_column_set():
    cols = Milestone.__table__.columns
    for required in (
        "citation_ref", "entry_type", "domain", "age_min_months",
        "age_max_months", "description", "severity", "cross_check_domain",
        "suggested_follow_up_question", "source", "phase_scope", "provenance",
    ):
        assert required in cols, f"milestones.{required} missing (FEAT-04)"
    assert cols["citation_ref"].nullable is False
    assert cols["citation_ref"].unique is True
    assert cols["severity"].nullable is True


# ── Loader idempotency (ADR-08 upsert on citation_ref) ─────────────────────


def test_loader_second_run_inserts_nothing(db_session):
    first = load_knowledge_base(db_session, csv_path=CSV_PATH)
    assert first.inserted == TOTAL_ROWS and first.total == TOTAL_ROWS
    second = load_knowledge_base(db_session, csv_path=CSV_PATH)
    assert second.inserted == 0
    assert second.updated == TOTAL_ROWS
    assert second.total == TOTAL_ROWS
    count = len(db_session.execute(select(Milestone)).scalars().all())
    assert count == TOTAL_ROWS


def test_loader_reapplies_csv_content_on_rerun(db_session):
    """A content correction in the CSV wins on the next run (same UUID)."""
    load_knowledge_base(db_session, csv_path=CSV_PATH)
    row = db_session.execute(
        select(Milestone).where(Milestone.citation_ref == "HEAR-RF-014")
    ).scalar_one()
    original_id = row.id
    csv_description = row.description
    row.description = "locally corrupted text"
    db_session.flush()

    load_knowledge_base(db_session, csv_path=CSV_PATH)

    refreshed = db_session.execute(
        select(Milestone).where(Milestone.citation_ref == "HEAR-RF-014")
    ).scalar_one()
    assert refreshed.description == csv_description
    assert refreshed.id == original_id  # UUID identity is stable across upserts


# ── PHASE 2 rows: stored, but invisible to the pipeline ────────────────────


def test_phase2_rows_are_loaded_not_dropped(loaded_db):
    assert len(PHASE2_REFS) > 0, "dataset sanity: PHASE 2 rows must exist"
    rows = loaded_db.execute(
        select(Milestone).where(Milestone.phase_scope.startswith(PHASE_2_PREFIX))
    ).scalars().all()
    assert _refs(rows) == PHASE2_REFS


@pytest.mark.parametrize("age_months", [12, 60, 80, 100, 200])
def test_phase2_rows_excluded_from_every_pipeline_query(loaded_db, age_months):
    returned = _refs(retrieve_in_scope_entries(loaded_db, age_months))
    assert returned & PHASE2_REFS == set()


# ── ADR-05: both domains jointly, never isolated ───────────────────────────


@pytest.mark.parametrize("age_months", [3, 24, 60])
def test_query_returns_both_domains_for_single_domain_sounding_age(
    loaded_db, age_months
):
    """No matter how language-specific the age band sounds, Hearing must be
    in the context too — hearing is a live differential on every language
    observation (and vice versa)."""
    rows = retrieve_in_scope_entries(loaded_db, age_months)
    domains = {row.domain for row in rows}
    assert domains == {"Speech_Language", "Hearing"}


# ── "Any age" rows (0-72) return at every in-scope age ─────────────────────


@pytest.mark.parametrize("age_months", [1, 12, 40, 72])
def test_any_age_rows_return_at_every_in_scope_age(loaded_db, age_months):
    returned = _refs(retrieve_in_scope_entries(loaded_db, age_months))
    assert ANY_AGE_REFS <= returned
    assert len(ANY_AGE_REFS) == 7  # dataset sanity: 2 SL + 3 HEAR-RF + 2 HEAR-RISK


def test_age_range_matching_is_inclusive_and_exclusive(loaded_db):
    at_5 = _refs(retrieve_in_scope_entries(loaded_db, 5))
    assert "HEAR-M-005" in at_5      # 3-6 months band covers age 5
    assert "HEAR-M-002" not in at_5  # 0-3 months band ended before age 5
    assert "SL-RF-003" not in at_5   # 12-12 point band does not cover age 5

    at_12 = _refs(retrieve_in_scope_entries(loaded_db, 12))
    assert "SL-RF-003" in at_12      # point band 12-12 covers exactly 12
    assert "HEAR-RF-002" not in at_12  # 6-6 band ended before age 12
