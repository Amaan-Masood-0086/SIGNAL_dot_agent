# v3.0.0-review.1 — 2026-09-09

## Delivered

- 88 source-grounded research entries for the seven planned developmental domains, plus separate context/safety/safeguarding entries.
- 41 primary-publisher references, precise URLs, section locators, access dates and applicability limitations. For two NICE pages direct access returned 403; indexed primary-source excerpts are explicitly identified.
- English and draft Roman-Urdu follow-up prompts on every entry.
- Distinct age thresholds and descriptive age bands; explicit product boundary at the 18th birthday.
- Evidence-group metadata, review-only grouping and age-estimate advancement helpers.
- Draft-only schemas, source checks, duplicate detection and complete legacy-mapping validation.
- Legacy v2 importer now rejects duplicate IDs, invalid/reversed ages, incompatible domains/severities, unexpected schema fields, unsupported phase values, malformed CSV rows and column-length overflow before database writes.
- 64 focused tests passed, including legacy deterministic grading.

## Legacy content treatment

All 94 old IDs have a decision record. These are review mappings, not automatic replacements:

| Treatment | Old IDs |
|---|---:|
| Related observations merged for review | 55 |
| Reframed with explicit scope/interpretation | 23 |
| Numeric-cutoff interpretation retired in v3 | 6 |
| Specific content review still needed | 10 |

The 10 specific-review IDs are `HEAR-M-011`, `HEAR-M-013`, `HEAR-RF-011`, `HEAR-RF-012`, `SL-M-003`, `SL-M-010`, `SL-M-025`, `SL-M-030`, `SL-RF-014`, `SL-RF-020`. Where no equivalent sourced row was curated, the mapping is deliberately empty. Related candidates must not be mistaken for literal replacements.

## Earlier flaws: what changed and what remains

| Issue | This release | Live application status |
|---|---|---|
| Exact-month expiry of threshold items | Explicit persistent `by_age` semantics and tests | v2 retrieval unchanged |
| Estimated age never advances | Tested date-based review helper | Current child model/pipeline integration pending |
| Vocabulary means treated as cutoffs | Six old numeric-cutoff interpretations excluded/reframed | Original v2 preserved |
| Concern automatically interpreted as HIGH | Separate concern/evidence/action fields; no v3 grade | Existing v2 rules unchanged |
| Correlated hearing findings/R14 | Common group and deduplication; no fabricated severity decision | Clinical decision and scoring integration pending |
| Missing follow-up questions | Every v3 row has questions in two text forms | v2 prompts/data unchanged |
| Sparse broad 6–18 rows | School-age/adolescent functional contexts | Expanded domains not enabled in DB/API |
| Weak ingestion validation | Runtime v2 importer hardened and tested | Applies when importer next runs |
| Source traceability | Registry and per-row citations | v3 research package only |

## Not claimed as complete

- No clinical approval, diagnostic validation, local norm study or translation validation.
- No live database import, production activation, seven-domain API expansion or web UI integration.
- No resolution of R14; no promise that the selected evidence groups are statistically independent.
- No full PostgreSQL suite or live-provider evaluation in this update.
- No claim of exhaustive medical/emergency coverage or a sourced normative milestone for every month.

## Next release gates

Clinical and translation review → resolve the 10 specific-review items and R14 → implement version-aware runtime support → expert-labelled synthetic evaluation → approved subset activation → supervised pilot under agreed consent/safeguarding rules.
