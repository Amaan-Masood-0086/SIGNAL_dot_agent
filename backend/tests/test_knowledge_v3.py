"""Research-release integrity and safety semantics; no DB or paid provider."""
from __future__ import annotations

import csv
import datetime as dt
import json
from dataclasses import asdict

import pytest
from pydantic import ValidationError

from app.services.knowledge import DEFAULT_CSV_PATH, parse_knowledge_csv
from app.services.knowledge_v3 import (
    Bundle, DEFAULT_V3_DIR, Entry, Source, _json, advance_estimated_age,
    age_eligibility, group_confirmed_evidence, load_review_bundle,
)


@pytest.fixture
def bundle():
    return load_review_bundle()[0]


def test_entire_release_resolves_sources_and_every_legacy_row(bundle):
    assert len(bundle.rows) >= 80
    assert all(r.follow_up_en and r.follow_up_ur_latn for r in bundle.rows)
    assert all(r.clinical_grade is None for r in bundle.rows)
    assert bundle.runtime_enabled is False


@pytest.mark.parametrize("changes", [
    {"runtime_enabled": True}, {"release_status": "approved"},
    {"clinical_scoring_policy": "HIGH_if_two_signs"},
])
def test_research_schema_cannot_be_activated_by_a_metadata_toggle(bundle, changes):
    data = bundle.model_dump()
    data.update(changes)
    with pytest.raises(ValidationError):
        Bundle.model_validate(data)


@pytest.mark.parametrize("changes", [
    {"age_min_months": -1}, {"age_min_months": True},
    {"age_max_months_exclusive": 0}, {"age_max_months_exclusive": 217},
    {"threshold_months": 99}, {"clinical_grade": "HIGH"},
    {"review_status": "approved"}, {"follow_up_en": "   "},
    {"follow_up_ur_latn": ""}, {"source_ids": []},
    {"domain": "DLD"}, {"unexpected_override": "activate"},
])
def test_invalid_clinical_row_fails_closed(bundle, changes):
    data = bundle.rows[0].model_dump()
    data.update(changes)
    with pytest.raises(ValidationError):
        Entry.model_validate(data)


def test_duplicate_ids_are_rejected(bundle):
    data = bundle.model_dump()
    data["rows"].append(data["rows"][0])
    with pytest.raises(ValidationError, match="Duplicate citation"):
        Bundle.model_validate(data)


def test_threshold_does_not_disappear_one_month_later(bundle):
    row = next(r for r in bundle.rows if r.citation_ref == "V3-SL-M-024-1")
    assert age_eligibility(row, 23, 23) == "outside_age_scope"
    for month in (24, 25, 30, 60):
        assert age_eligibility(row, month, month) == "eligible_for_review"
    assert age_eligibility(row, 22, 28) == "age_uncertain"
    assert age_eligibility(row, 70, 74) == "age_uncertain"
    assert age_eligibility(row, 72, 72) == "outside_age_scope"


@pytest.mark.parametrize("age", [-1, float("nan"), float("inf"), True])
def test_invalid_preview_age_rejected(bundle, age):
    with pytest.raises(ValueError):
        age_eligibility(bundle.rows[0], age, age)


def test_age_18_is_transition_not_silent_pediatric_extension(bundle):
    assert all(age_eligibility(r, 216, 216) == "outside_age_scope" for r in bundle.rows)
    assert any(age_eligibility(r, 215, 215) == "eligible_for_review" for r in bundle.rows)


def test_urgent_routes_are_not_lost_for_estimated_age(bundle):
    row = next(r for r in bundle.rows if r.citation_ref == "V3-HEAR-010")
    assert row.age_basis == "chronological_age"
    assert age_eligibility(row, 20, 30) == "eligible_for_review"
    assert row.action == "immediate_medical"


def test_correlated_ome_rows_are_one_review_group_not_three_votes(bundle):
    groups = group_confirmed_evidence(bundle, ["V3-HEAR-005", "V3-HEAR-006", "V3-HEAR-007", "V3-HEAR-006"])
    assert groups == {"fluctuating_hearing": ["V3-HEAR-005", "V3-HEAR-006", "V3-HEAR-007"]}
    # This test does not assert MODERATE or resolve the clinical R14 dispute.
    assert "grade" not in groups


def test_fabricated_citation_cannot_enter_evidence_groups(bundle):
    with pytest.raises(ValueError, match="Unknown evidence"):
        group_confirmed_evidence(bundle, ["V3-FAKE-001"])


def test_estimated_age_advances_without_collapsing_interval():
    assert advance_estimated_age(24, 30, dt.date(2025, 1, 9), dt.date(2026, 1, 9)) == (36, 42)
    assert advance_estimated_age(24, 30, dt.date(2025, 1, 9), dt.date(2025, 2, 8)) == (24, 30)
    with pytest.raises(ValueError):
        advance_estimated_age(30, 24, dt.date(2025, 1, 9), dt.date(2026, 1, 9))
    with pytest.raises(ValueError):
        advance_estimated_age(24, 30, dt.date(2026, 1, 9), dt.date(2025, 1, 9))


def test_no_infant_attention_diagnostic_rules(bundle):
    infant_rows = [r for r in bundle.rows if r.domain == "Attention" and age_eligibility(r, 6, 6) == "eligible_for_review"]
    assert infant_rows and all(r.entry_kind == "context" for r in infant_rows)


def test_source_domains_cannot_be_spoofed():
    data = _json(DEFAULT_V3_DIR / "sources.json")[0]
    for url in ("http://www.cdc.gov/", "https://cdc.gov.attacker.invalid/", "https://cdc.gov@attacker.invalid/"):
        with pytest.raises(ValidationError):
            Source.model_validate({**data, "url": url})


def test_duplicate_json_keys_fail_instead_of_overriding_gate(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"runtime_enabled":false,"runtime_enabled":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        _json(path)


def test_legacy_baseline_remains_parseable():
    assert len(parse_knowledge_csv(DEFAULT_CSV_PATH)) == 94


@pytest.mark.parametrize("change", [
    {"domain": "Vision"}, {"age_min_months": -2},
    {"age_max_months": 217}, {"age_min_months": 9, "age_max_months": 3},
    {"severity": "HIGH"}, {"phase_scope": "approved"},
    {"age_max_months": 100}, {"cross_check_domain": "ADHD"},
    {"provenance": "x" * 121},
])
def test_legacy_importer_rejects_invalid_rows_before_any_db_write(tmp_path, change):
    row = asdict(parse_knowledge_csv(DEFAULT_CSV_PATH)[0])
    row.update(change)
    path = tmp_path / "bad.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError):
        parse_knowledge_csv(path)


def test_legacy_importer_rejects_duplicate_rows_and_v3_metadata(tmp_path):
    row = asdict(parse_knowledge_csv(DEFAULT_CSV_PATH)[0])
    for rows in ([row, row], [{**row, "review_status": "needs_clinical_review"}]):
        path = tmp_path / "invalid.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with pytest.raises(ValueError):
            parse_knowledge_csv(path)
