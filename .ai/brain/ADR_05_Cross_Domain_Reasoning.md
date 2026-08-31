# ADR-05: Risk Reasoning Agent Must Check Speech_Language and Hearing Jointly, Not Domain-Isolated

**Status:** Accepted
**Date:** 2026-08-30
**Superseded terminology note (2026-08-31):** this ADR was written before ADR-07 renamed the "DLD" domain to "Speech_Language". Every occurrence of "DLD" below should be read as "Speech_Language" — confirmed non-conflicting with the FEAT-04 implementation, which correctly uses Speech_Language throughout. Text left otherwise unchanged to preserve the original reasoning trail.
**Decided by:** Requirement surfaced directly in Ayesha's delivered knowledge base (`SIGNAL_DLD_Hearing_KnowledgeBase.docx`, Section 6 and "Notes for the Developer"); locked in by NextaSol

## Context

The knowledge base document Ayesha delivered states explicitly: *"Delayed or absent speech development is described as the single most important clue to possible hearing loss... meaning DLD-domain and Hearing-domain questions should always be cross-checked against each other by the Risk Reasoning Agent, not treated as fully separate tracks."*

Her own test conversations prove this is not optional: **conversations 5 and 7 in the delivered test set only resolve correctly if the agent checks both domain tables together.** In conversation 5 (3-year-old, limited talking + not listening), the correct read — hearing concern, not pure speech delay — only emerges by cross-referencing "doesn't react to sound" against the DLD table's speech-delay pattern. A domain-isolated agent that ran a DLD-only pass would misattribute this to language delay alone and miss the higher-priority hearing explanation.

This was not part of the original pipeline design assumption. The `flags` schema (TRD §3) has a single `domain` field per flag, and FEAT-05's original scope described Observation → Risk Reasoning → Explanation without specifying whether reasoning happens per-domain or jointly.

## Decision

The Risk Reasoning Agent's retrieval and reasoning step queries **both** the DLD and Hearing tables for every observation, every time — never a single-domain pass. Concretely:

1. Given an observation (e.g., "limited speech"), retrieve relevant rows from both domain tables, not just the domain the caretaker's initial framing suggests
2. Follow-up questions are selected to actively **discriminate** between a DLD explanation and a Hearing explanation when both are plausible (Ayesha's own example: *"does she respond when you call her name from behind, where she can't see you?"* — this single question separates a hearing response from general language delay)
3. The final output may produce a flag on one domain, both domains, or route to `insufficient_information` — but the reasoning process that gets there is never domain-isolated
4. `flags.domain` remains a single value per flag row (a flag is still filed under one domain), but which domain gets flagged is decided only after the joint check — not by which table was consulted first

## Consequences

- **Positive:** Matches how symptom overlap actually works clinically (per the domain expert's own framing) — a domain-isolated agent would systematically misattribute hearing-driven speech delay to DLD, which is exactly the kind of error that undermines clinical credibility (Section 5, source product document — "why can't Gabify just sell to orphanages" argument depends on SIGNAL's reasoning being genuinely sound, not just plausible-sounding).
- **Negative / accepted trade-off:** Slightly more retrieval/context per Risk Reasoning Agent call (both tables instead of one) — negligible given ADR-04's full-context-injection approach already loads the whole knowledge base regardless.
- **Test requirement added:** `TEST_PLAN_SIGNAL.md` must include Ayesha's conversations 5 and 7 (or equivalent cross-domain cases) as explicit test cases — a passing test suite that only exercises single-domain conversations would not catch a regression to domain-isolated reasoning.
