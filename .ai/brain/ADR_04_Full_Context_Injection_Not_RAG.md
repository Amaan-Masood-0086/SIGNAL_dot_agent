# ADR-04: Full-Context Knowledge Injection Instead of Retrieval, for Phase 1

**Status:** Accepted
**Date:** 2026-08-29
**Decided by:** NextaSol (Akasha Azhar), autonomously per "tu dekh lay" delegation, prompted by a direct question about whether RAG/retrieval is actually necessary at Phase 1 scale

## Context

ADR-01 already ruled out a dedicated vector-DB service, reasoning that the knowledge base is small and curated rather than a millions-of-documents corpus, and that pgvector inside Postgres would be sufficient if retrieval were needed. The data-request materials sent to Ayesha/Sami (2026-08-29) target roughly 15–20 entries for a Phase 1-viable knowledge base (5–8 age bands × a few milestones/red-flags each, across 2 domains) — small enough to reconsider whether retrieval is needed at all, not just which retrieval backend to use.

"RAG" (Retrieval-Augmented Generation) is a technique for handling knowledge bases too large to fit in a model's context window on every call — it retrieves only the most relevant subset before generating. The SIGNAL knowledge base at Phase 1 scale (roughly 2,000–3,000 words total) fits comfortably inside any modern LLM's context window whole, with room to spare.

## Decision

For Phase 1, the Risk Reasoning Agent's prompt includes the **entire** `milestones` table content directly (full-context injection), not a retrieved subset. No embedding generation, no vector similarity search, no retrieval step.

- `milestones` remains a Postgres table (needed regardless, for admin/update and for the reasoning-trail citation to resolve real IDs) — but is queried in full, not via similarity search
- Each entry keeps a stable `id` so the reasoning-trail citation requirement (ADR-03) is unaffected — citation works identically whether the model saw one retrieved entry or the full table
- A size threshold is set as the trigger to revisit: if the knowledge base grows past roughly 150–200 entries (Track B, once more domains and age ranges are added), switch to embedding-based retrieval as originally scoped in ADR-01

## Consequences

- **Positive:** Removes an entire layer of engineering complexity from FEAT-04 — no embedding pipeline, no similarity search tuning, no retrieval-recall risk (a real risk with small/sparse datasets, where semantic search can under-match). Every model call sees the complete knowledge base, so there's no chance of a relevant milestone existing in the database but not being retrieved for a given observation.
- **Negative / accepted trade-off:** Slightly higher token cost per call than a tightly-retrieved subset would be — negligible at Phase 1's dataset size (a few thousand words is a small fraction of typical context windows and cost budgets already modeled in the source product document, Section 9).
- **Follow-up required:** Revisit at the size threshold above. This ADR does not change ADR-01's stack choice (Postgres remains correct either way) — it only changes whether FEAT-04 needs to build a retrieval step at all for Phase 1.
