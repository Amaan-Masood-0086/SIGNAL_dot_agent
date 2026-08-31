# ADR-03: Mandatory Reasoning-Trail Citation & RAG-Only Grounding

**Status:** Accepted
**Date:** 2026-08-28
**Decided by:** Flagged by external technical reviewer (2026-08-28 working session), formalized by NextaSol

## Context

Source document §11 positions SIGNAL to target the US FDA's non-device Clinical Decision Support carve-out (21st Century Cures Act §520(o)(1)(E)). One of that carve-out's criteria is that a professional must be able to independently review the basis for the system's recommendation. An opaque confidence score with no cited basis is functionally a regulated-device risk score, not a transparent CDS aid — this is a regulatory requirement, not a UX nicety.

Separately, LLMs are prone to generating plausible-sounding but ungrounded clinical claims when reasoning freely. In a health-adjacent domain, this is the single largest technical risk to the product's credibility (identified in stress-test conversation, 2026-08-28).

## Decision

1. Every row in `flags` MUST populate `reasoning_trail` (jsonb) with references to one or more specific `milestone_id`s from the RAG-retrieved knowledge base. A flag with an empty or missing reasoning trail is rejected at the service layer (`FlagService.create_flag()`), not just flagged for review.
2. The Risk Reasoning Agent's prompt is constrained to **cite retrieved context only** — it is explicitly instructed not to generate clinical claims from free recall. If retrieval returns no relevant milestone for a given observation, the agent must route to `status=insufficient_information` (feature #6) rather than reason without grounding.
3. This applies to both domains (DLD and Hearing) equally, and to any domain added in later phases.

## Consequences

- **Positive:** Directly supports the regulatory carve-out target; makes the product's clinical claims independently auditable by a real clinician, which is the entire "routes to a clinician, doesn't diagnose" positioning; reduces hallucination risk by design rather than by post-hoc review.
- **Negative / accepted trade-off:** Constrains prompt design — the Risk Reasoning Agent cannot "helpfully" fill gaps in the knowledge base with general LLM knowledge, even when it might be correct. This is intentional: an ungrounded-but-correct claim is indistinguishable from an ungrounded-and-wrong one without a citation, and the product's credibility depends on the distinction being auditable, not just usually accurate.
- **Dependency:** Quality of this entire mechanism is bounded by the completeness of Ayesha/Sami's knowledge base (PROJECT_BRIEF Open Item #3) — a thin knowledge base will produce a high rate of `insufficient_information` results, which is the correct failure mode (safe) but should be communicated to them as a reason the dataset needs real coverage, not just a few example entries.
