# ADR-02: Estimated-Age Handling in the Data Model

**Status:** Accepted
**Date:** 2026-08-28
**Decided by:** Flagged by external technical reviewer (2026-08-28 working session), accepted into schema by NextaSol

## Context

Many children in Pakistani institutional care do not have a confirmed date of birth — intake often happens without documentation. Every milestone-based screening check in the product (DLD and Hearing domains alike) is age-dependent. If the system silently assumes a confirmed DOB when one doesn't exist, a flag's confidence is misleadingly overstated, which directly undermines the regulatory requirement that a clinician be able to independently review the basis for a flag (see ADR-03).

## Decision

The `children` table carries a dual representation, not a single `date_of_birth` field:

- `dob_confirmed` (boolean)
- `dob` (nullable date — populated only if `dob_confirmed = true`)
- `estimated_age_range` (populated only if `dob_confirmed = false`)
- `estimated_age_note` (free text — how the estimate was derived, e.g. "intake worker estimate")

**Business rule (enforced in `RiskReasoningAgent.grade_confidence()`):** if `dob_confirmed = false`, any milestone check that depends on age automatically has its confidence grade downgraded one tier, regardless of how strong the underlying signal is.

This is schema-level from the start of Scaffold, not a retrofit — the additional fields cost nothing to include now and are expensive to add after flags/referrals already reference a single-DOB assumption.

## Consequences

- **Positive:** No flag can silently overstate its own reliability due to an unverified age assumption. This directly protects the regulatory positioning (non-diagnostic, transparently-graded CDS tool) and protects institutions from acting on overconfident output.
- **Negative / accepted trade-off:** Slightly more complex intake UI (caretaker must indicate confirmed-vs-estimated at child registration) and slightly more complex confidence-grading logic in the Risk Reasoning Agent.
- **Dependency:** Ayesha/Sami's milestone dataset (PROJECT_BRIEF Open Item #3) should ideally specify age bands with enough granularity that a downgraded-confidence estimate is still useful, not just "insufficient information" by default — this should be raised with them explicitly when the dataset arrives.
