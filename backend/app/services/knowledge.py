"""FEAT-04 knowledge-base layer: CSV ingestion, pipeline retrieval, grading.

- Retrieval is plain SQL over the whole in-scope age window — NO embeddings,
  NO vector search; the full relevant context is injected into the Risk
  Reasoning Agent prompt (ADR-04).
- Every query returns BOTH domains jointly (ADR-05): hearing is a live
  differential on every language observation and vice versa, so no query
  surface ever filters to a single domain.
- Grading is a deterministic function (ADR-06), never prompt text the LLM
  interprets: same inputs -> same grade, with the citation_refs that
  produced it enumerated.
- Rows with phase_scope "PHASE 2 (6+)" are stored but excluded from every
  pipeline query.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.milestone import Milestone

# Default CSV location (repo root); tests and the ingest script pass an
# explicit path.
DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[3]
    / ".ai"
    / "brain"
    / "knowledge-base-source"
    / "signal_knowledge_base_v2.csv"
)

PHASE_2_PREFIX = "PHASE"  # phase_scope values starting with this are out of scope
SEVERITY_HIGH = "HIGH"
SEVERITY_MODERATE = "MODERATE"


@dataclass(frozen=True)
class KnowledgeEntry:
    """In-memory mirror of one milestones row (loader output / grading input)."""

    citation_ref: str
    entry_type: str
    domain: str
    age_min_months: int
    age_max_months: int
    description: str
    severity: str | None
    cross_check_domain: str | None
    suggested_follow_up_question: str | None
    source: str
    phase_scope: str
    provenance: str

    @classmethod
    def from_row(cls, row: Milestone) -> "KnowledgeEntry":
        return cls(
            citation_ref=row.citation_ref,
            entry_type=row.entry_type,
            domain=row.domain,
            age_min_months=row.age_min_months,
            age_max_months=row.age_max_months,
            description=row.description,
            severity=row.severity,
            cross_check_domain=row.cross_check_domain,
            suggested_follow_up_question=row.suggested_follow_up_question,
            source=row.source,
            phase_scope=row.phase_scope,
            provenance=row.provenance,
        )


def _none_if_blank(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def parse_knowledge_csv(csv_path: str | Path) -> list[KnowledgeEntry]:
    """Parse the knowledge-base CSV into validated entries.

    Empty CSV cells become NULL (severity, cross_check_domain,
    suggested_follow_up_question). Malformed rows raise ValueError — the
    loader refuses a partially-ingested knowledge base.
    """
    entries: list[KnowledgeEntry] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for line_number, row in enumerate(csv.DictReader(handle), start=2):
            citation_ref = _none_if_blank(row.get("citation_ref"))
            if citation_ref is None:
                raise ValueError(f"Row {line_number}: missing citation_ref")
            try:
                age_min = int(row["age_min_months"])
                age_max = int(row["age_max_months"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Row {line_number} ({citation_ref}): invalid age range"
                ) from exc
            severity = _none_if_blank(row.get("severity"))
            entry_type = _none_if_blank(row.get("entry_type"))
            domain = _none_if_blank(row.get("domain"))
            description = _none_if_blank(row.get("description"))
            source = _none_if_blank(row.get("source"))
            phase_scope = _none_if_blank(row.get("phase_scope"))
            provenance = _none_if_blank(row.get("provenance"))
            missing = [
                name
                for name, value in (
                    ("entry_type", entry_type),
                    ("domain", domain),
                    ("description", description),
                    ("source", source),
                    ("phase_scope", phase_scope),
                    ("provenance", provenance),
                )
                if value is None
            ]
            if missing:
                raise ValueError(
                    f"Row {line_number} ({citation_ref}): missing {', '.join(missing)}"
                )
            if entry_type != "milestone" and severity is None:
                raise ValueError(
                    f"Row {line_number} ({citation_ref}): "
                    f"{entry_type} rows require a severity"
                )
            entries.append(
                KnowledgeEntry(
                    citation_ref=citation_ref,
                    entry_type=entry_type,
                    domain=domain,
                    age_min_months=age_min,
                    age_max_months=age_max,
                    description=description,
                    severity=severity,
                    cross_check_domain=_none_if_blank(row.get("cross_check_domain")),
                    suggested_follow_up_question=_none_if_blank(
                        row.get("suggested_follow_up_question")
                    ),
                    source=source,
                    phase_scope=phase_scope,
                    provenance=provenance,
                )
            )
    if not entries:
        raise ValueError(f"{csv_path}: knowledge-base CSV is empty")
    return entries


@dataclass(frozen=True)
class LoadResult:
    inserted: int
    updated: int
    total: int


def load_knowledge_base(
    db: Session, csv_path: str | Path = DEFAULT_CSV_PATH
) -> LoadResult:
    """Idempotently ingest the CSV, upserting on citation_ref (ADR-08).

    Running twice never duplicates rows — the second run reports the same
    total with zero inserts. Content corrections update in place; the UUID
    primary key of an existing row never changes.
    """
    entries = parse_knowledge_csv(csv_path)
    inserted = 0
    updated = 0
    for entry in entries:
        existing = db.execute(
            select(Milestone).where(Milestone.citation_ref == entry.citation_ref)
        ).scalar_one_or_none()
        values = {
            "entry_type": entry.entry_type,
            "domain": entry.domain,
            "age_min_months": entry.age_min_months,
            "age_max_months": entry.age_max_months,
            "description": entry.description,
            "severity": entry.severity,
            "cross_check_domain": entry.cross_check_domain,
            "suggested_follow_up_question": entry.suggested_follow_up_question,
            "source": entry.source,
            "phase_scope": entry.phase_scope,
            "provenance": entry.provenance,
        }
        if existing is None:
            db.add(Milestone(citation_ref=entry.citation_ref, **values))
            inserted += 1
        else:
            for column, value in values.items():
                setattr(existing, column, value)
            updated += 1
    db.flush()
    total = db.execute(select(Milestone)).scalars().all()
    return LoadResult(inserted=inserted, updated=updated, total=len(total))


def retrieve_in_scope_entries(db: Session, age_months: int) -> list[Milestone]:
    """ALL in-scope knowledge-base entries for a child's age — BOTH domains
    jointly (ADR-05), never domain-isolated.

    - PHASE 2 rows are stored but never returned (FEAT-04 rule 5).
    - "Any age" rows (age range 0-72) satisfy the range test at every
      in-scope age, so they always come back.
    - Deterministic ordering so the injected prompt context is stable.
    """
    if age_months < 0:
        raise ValueError("age_months must be >= 0")
    statement = (
        select(Milestone)
        .where(~Milestone.phase_scope.startswith(PHASE_2_PREFIX))
        .where(Milestone.age_min_months <= age_months)
        .where(Milestone.age_max_months >= age_months)
        .order_by(Milestone.domain, Milestone.citation_ref)
    )
    return list(db.execute(statement).scalars().all())


# ── ADR-06 deterministic grading ────────────────────────────────────────────

GRADE_HIGH = "HIGH"
GRADE_MODERATE = "MODERATE"
GRADE_LOW_MONITOR = "LOW_MONITOR"
GRADE_INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"

ENTRY_TYPE_RED_FLAG = "red_flag"
ENTRY_TYPE_MILESTONE = "milestone"
ENTRY_TYPE_RISK_MODIFIER = "risk_modifier"


@dataclass(frozen=True)
class GradeResult:
    """A grade plus the exact citation_refs that produced it (ADR-06 sub-rule 3).

    `age_uncertain` surfaces ADR-06 sub-rule 4: whenever age is estimated the
    uncertainty must be shown in the output, even when the grade itself is
    unchanged (age-independent red flags).
    """

    grade: str
    citation_refs: list[str]
    age_uncertain: bool = False


def _citation_refs(*groups: Iterable[KnowledgeEntry]) -> list[str]:
    refs: list[str] = []
    for group in groups:
        for entry in group:
            if entry.citation_ref not in refs:
                refs.append(entry.citation_ref)
    return refs


def grade(
    confirmed_flags: Sequence[KnowledgeEntry] = (),
    missed_milestones: Sequence[KnowledgeEntry] = (),
    *,
    risk_modifiers: Sequence[KnowledgeEntry] = (),
    age_is_estimated: bool = False,
    key_items_missing: bool = False,
) -> GradeResult:
    """ADR-06 four-state grading, implemented as a pure, testable function.

    Rule: grade = max(highest single-flag severity, count-based rule).
    Red flags outweigh missed milestones (a red flag should never be present;
    a missed milestone is merely not-yet-present and carries normal
    variation). Risk modifiers raise, never lower (ADR-06 sub-rule 7): they
    are cited for transparency but cannot reduce a grade, and a bare
    modifier never lifts a borderline delay on its own.

    There is no "no concern" outcome: the floor for the weakest confirmed
    evidence is LOW_MONITOR ("LOW — monitor & recheck", sub-rule 1). Under
    estimated age a borderline delay grades DOWN to this floor (sub-rule 4);
    age-independent red flags (regression, caretaker hearing concern, ...)
    grade unchanged regardless of age uncertainty. Missing key information is
    INSUFFICIENT_INFORMATION, never LOW (sub-rule 2).
    """
    red_flags = [e for e in confirmed_flags if e.entry_type == ENTRY_TYPE_RED_FLAG]

    # Sub-rules 2 + insufficient-evidence: missing discriminating items, or
    # no confirmed evidence at all, cannot be graded.
    if key_items_missing:
        return GradeResult(
            grade=GRADE_INSUFFICIENT_INFORMATION,
            citation_refs=_citation_refs(red_flags, missed_milestones, risk_modifiers),
            age_uncertain=age_is_estimated,
        )
    if not red_flags and not missed_milestones:
        return GradeResult(
            grade=GRADE_INSUFFICIENT_INFORMATION,
            citation_refs=_citation_refs(risk_modifiers),
            age_uncertain=age_is_estimated,
        )

    high_flags = [e for e in red_flags if e.severity == SEVERITY_HIGH]
    moderate_flags = [e for e in red_flags if e.severity == SEVERITY_MODERATE]

    # Rule 1a: any ONE confirmed HIGH-severity red flag → HIGH (unchanged
    # under estimated age — these flags are age-independent).
    if high_flags:
        return GradeResult(
            grade=GRADE_HIGH,
            citation_refs=_citation_refs(high_flags, moderate_flags, risk_modifiers),
            age_uncertain=age_is_estimated,
        )

    # Rule 1b: ≥2 MODERATE red flags within the same domain → HIGH.
    moderate_by_domain: dict[str, list[KnowledgeEntry]] = {}
    for entry in moderate_flags:
        moderate_by_domain.setdefault(entry.domain, []).append(entry)
    for domain_flags in moderate_by_domain.values():
        if len(domain_flags) >= 2:
            return GradeResult(
                grade=GRADE_HIGH,
                citation_refs=_citation_refs(domain_flags, risk_modifiers),
                age_uncertain=age_is_estimated,
            )

    # Rule 2: one MODERATE red flag (red flags outweigh missed milestones),
    # or a missed milestone PLUS a confirmed supporting observation —
    # "milestone missed at threshold plus one supporting observation"
    # (ADR-06). A bare modifier is NOT a supporting observation: modifiers
    # raise, never lower, and alone they never lift a borderline delay.
    if moderate_flags:
        return GradeResult(
            grade=GRADE_MODERATE,
            citation_refs=_citation_refs(moderate_flags, missed_milestones, risk_modifiers),
            age_uncertain=age_is_estimated,
        )
    supporting_flags = [
        e for e in confirmed_flags if e.entry_type != ENTRY_TYPE_RED_FLAG
    ]
    if missed_milestones and supporting_flags:
        return GradeResult(
            grade=GRADE_MODERATE,
            citation_refs=_citation_refs(missed_milestones, supporting_flags, risk_modifiers),
            age_uncertain=age_is_estimated,
        )

    # Only evidence is missed milestone(s) — a borderline delay, possibly
    # with protective indicators / risk modifiers cited alongside. The floor
    # is LOW_MONITOR ("LOW — monitor & recheck"): never "no concern", never
    # a discharge (ADR-06 sub-rule 1). Under estimated age a borderline
    # delay grades DOWN to this floor (sub-rule 4); the floor cannot go
    # lower, so the grade holds. Modifiers never lower (sub-rule 7) and a
    # bare modifier never raises a borderline delay either.
    return GradeResult(
        grade=GRADE_LOW_MONITOR,
        citation_refs=_citation_refs(missed_milestones, risk_modifiers),
        age_uncertain=age_is_estimated,
    )
