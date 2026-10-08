"""Validate and inspect the v3 research KB. Deliberately no database writes.

The legacy grading engine cannot interpret evidence groups, action urgency,
review status or the expanded domains. This module is a review tool, not a
second medical grading engine. Its age and evidence helpers are testable
building blocks for a future clinically reviewed integration.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_V3_DIR = ROOT / "knowledge_base" / "v3"
Domain = Literal[
    "Speech_Language", "Hearing", "Vision", "Motor", "Social_Communication",
    "Attention", "Attachment", "Safety", "Safeguarding", "Context",
]
DEVELOPMENTAL_DOMAINS = {
    "Speech_Language", "Hearing", "Vision", "Motor", "Social_Communication",
    "Attention", "Attachment",
}


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Source(StrictRecord):
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str
    locator: str = Field(min_length=1)
    limitations: str = Field(min_length=1)
    accessed_on: dt.date
    verification: Literal["primary_web_evidence", "primary_search_excerpt"]

    @model_validator(mode="after")
    def primary_https_source(self):
        parsed = urlparse(self.url)
        allowed = {"cdc.gov", "asha.org", "nidcd.nih.gov", "nice.org.uk",
                   "healthychildren.org", "aapos.org", "nhs.uk", "who.int", "aacap.org"}
        host = parsed.hostname or ""
        if (parsed.scheme != "https" or parsed.username or parsed.password
                or not any(host == d or host.endswith("." + d) for d in allowed)):
            raise ValueError("Source must link to an allowlisted primary HTTPS publisher")
        return self


class Entry(StrictRecord):
    citation_ref: str = Field(pattern=r"^V3-[A-Z]+-(?:M-)?[0-9]+(?:-[0-9]+)?$")
    domain: Domain
    entry_kind: Literal["milestone", "concern", "context", "urgent", "safeguarding", "professional_test"]
    age_min_months: StrictInt = Field(ge=0, lt=216)
    age_max_months_exclusive: StrictInt = Field(gt=0, le=216)
    age_semantics: Literal["by_age", "age_band", "any_age"]
    threshold_months: StrictInt | None
    age_basis: Literal["developmental_age", "chronological_age"]
    observation: str = Field(min_length=1)
    follow_up_en: str = Field(min_length=1)
    follow_up_ur_latn: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    evidence_group: str = Field(pattern=r"^[a-z][a-z_]+$")
    cross_check_domains: list[Domain]
    action: Literal[
        "professional_review", "developmental_review", "audiology_review",
        "speech_language_review", "eye_review", "motor_review", "relationship_review",
        "immediate_medical", "urgent_medical", "prompt_medical", "context_only",
        "safeguarding_pathway", "mental_health_review",
    ]
    interpretation_notes: str = Field(min_length=1)
    clinical_grade: None
    review_status: Literal["needs_clinical_review"]
    reviewer: None
    reviewed_on: None
    translation_status: Literal["draft_ur_latn"]
    legacy_refs: list[str]

    @model_validator(mode="after")
    def coherent_semantics(self):
        if self.age_min_months >= self.age_max_months_exclusive:
            raise ValueError("Empty or reversed age interval")
        if self.entry_kind == "milestone":
            if (self.age_semantics != "by_age" or self.threshold_months != self.age_min_months
                    or self.age_basis != "developmental_age"):
                raise ValueError("Milestone must persist from its explicit developmental threshold")
        elif self.threshold_months is not None or self.age_semantics == "by_age":
            raise ValueError("Only milestones carry normative thresholds")
        if self.age_semantics == "any_age" and (self.age_min_months, self.age_max_months_exclusive) != (0, 216):
            raise ValueError("Any-age means the full product age interval")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("Duplicate source ids")
        if len(self.cross_check_domains) != len(set(self.cross_check_domains)) or self.domain in self.cross_check_domains:
            raise ValueError("Cross checks must be distinct companion domains")
        if self.domain == "Attention" and self.age_min_months < 60 and self.entry_kind != "context":
            raise ValueError("No infant/preschool attention diagnostic threshold in this release")
        if self.entry_kind == "safeguarding" and (self.domain != "Safeguarding" or self.action != "safeguarding_pathway"):
            raise ValueError("Safeguarding must remain outside developmental grading")
        if self.entry_kind == "urgent" and (self.age_basis != "chronological_age" or self.action not in {
            "immediate_medical", "urgent_medical", "prompt_medical"
        }):
            raise ValueError("Urgent routes cannot be downgraded by corrected developmental age")
        return self


class AgeScope(StrictRecord):
    min_months: Literal[0]
    max_months_exclusive: Literal[216]


class Bundle(StrictRecord):
    schema_version: Literal["3.0"]
    release_id: str = Field(min_length=1)
    created_on: dt.date
    release_status: Literal["research_draft"]
    runtime_enabled: Literal[False]
    age_scope: AgeScope
    clinical_scoring_policy: Literal["not_validated_no_automatic_grade"]
    rows: list[Entry] = Field(min_length=1)

    @model_validator(mode="after")
    def no_duplicate_ids_or_silent_activation(self):
        refs = [r.citation_ref for r in self.rows]
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate citation_ref")
        if not DEVELOPMENTAL_DOMAINS <= {r.domain for r in self.rows}:
            raise ValueError("Missing a planned developmental domain")
        return self


class LegacyMapping(StrictRecord):
    legacy_ref: str
    disposition: Literal["reframed", "merged", "retired_numeric_cutoff", "needs_specific_review"]
    candidate_refs: list[str]
    reason: str = Field(min_length=1)
    automatic_replacement: Literal[False]


def _json(path: Path):
    # Duplicate JSON keys must not override review_status or source metadata.
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_pairs)


def load_review_bundle(directory: Path = DEFAULT_V3_DIR) -> tuple[Bundle, list[Source]]:
    bundle = Bundle.model_validate(_json(directory / "knowledge_base.json"))
    sources = [Source.model_validate(s) for s in _json(directory / "sources.json")]
    source_ids = {s.source_id for s in sources}
    if len(sources) != len(source_ids):
        raise ValueError("Duplicate source id")
    for row in bundle.rows:
        if not set(row.source_ids) <= source_ids:
            raise ValueError(f"{row.citation_ref}: unresolved source")
    mapping = [LegacyMapping.model_validate(m) for m in _json(directory / "legacy_mapping.json")]
    with (ROOT / ".ai/brain/knowledge-base-source/signal_knowledge_base_v2.csv").open(encoding="utf-8-sig", newline="") as f:
        old_refs = {r["citation_ref"] for r in csv.DictReader(f)}
    mapped_refs = [m.legacy_ref for m in mapping]
    if len(mapped_refs) != len(set(mapped_refs)) or set(mapped_refs) != old_refs:
        raise ValueError("Every legacy row must have exactly one migration decision")
    new_refs = {r.citation_ref for r in bundle.rows}
    for item in mapping:
        if not set(item.candidate_refs) <= new_refs:
            raise ValueError(f"{item.legacy_ref}: unresolved migration target")
    for row in bundle.rows:
        expected = {m.legacy_ref for m in mapping if row.citation_ref in m.candidate_refs}
        if set(row.legacy_refs) != expected:
            raise ValueError(f"{row.citation_ref}: migration reverse links disagree")
    return bundle, sources


def age_eligibility(entry: Entry, lower_months: float, upper_months: float) -> str:
    """Review eligibility, NOT whether a skill is absent or a concern confirmed.

    Supply documented developmental age for milestone rows and chronological
    age for urgent/context rows. Unknown/prematurity input is never guessed.
    An interval straddling either boundary must not be silently rounded.
    """
    import math
    if (isinstance(lower_months, bool) or isinstance(upper_months, bool)
            or not math.isfinite(lower_months) or not math.isfinite(upper_months)
            or not 0 <= lower_months <= upper_months):
        raise ValueError("Age must be a finite ordered non-negative interval")
    start, end = entry.age_min_months, entry.age_max_months_exclusive
    if upper_months < start or lower_months >= end:
        return "outside_age_scope"
    if lower_months < start or upper_months >= end:
        return "age_uncertain"
    return "eligible_for_review"


def advance_estimated_age(lower: int, upper: int, recorded_on: dt.date, as_of: dt.date) -> tuple[int, int]:
    """Advance both estimate bounds by completed calendar months.

    Keeps the interval, never invents a midpoint. This helper does not change
    existing child records or the current v2 risk pipeline.
    """
    if type(lower) is not int or type(upper) is not int or not 0 <= lower <= upper:
        raise ValueError("Estimated age needs ordered non-negative integer bounds")
    if as_of < recorded_on:
        raise ValueError("Cannot evaluate before the estimate reference date")
    elapsed = (as_of.year - recorded_on.year) * 12 + as_of.month - recorded_on.month
    elapsed -= int(as_of.day < recorded_on.day)
    return lower + elapsed, upper + elapsed


def group_confirmed_evidence(bundle: Bundle, confirmed_refs: list[str]) -> dict[str, list[str]]:
    """Group explicitly confirmed observations, not a clinical severity rule.

    Duplicate citations cannot multiply evidence. OME-like signs share a
    group; grouping is review metadata and does NOT assert clinical independence.
    Urgent/safeguarding routes must be handled separately by a future consumer.
    """
    by_ref = {r.citation_ref: r for r in bundle.rows}
    if not set(confirmed_refs) <= by_ref.keys():
        raise ValueError("Unknown evidence citation")
    result: dict[str, list[str]] = {}
    for ref in sorted(set(confirmed_refs)):
        row = by_ref[ref]
        result.setdefault(row.evidence_group, []).append(ref)
    return result


def summary(bundle: Bundle, sources: list[Source]) -> dict:
    return {
        "release": bundle.release_id, "rows": len(bundle.rows), "sources": len(sources),
        "domains": dict(sorted(Counter(r.domain for r in bundle.rows).items())),
        "runtime_enabled": False, "clinical_status": "REQUIRES CLINICAL REVIEW — NOT A VALIDATED SCREEN",
    }
