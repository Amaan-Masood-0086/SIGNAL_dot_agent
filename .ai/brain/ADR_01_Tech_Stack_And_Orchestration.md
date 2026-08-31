# ADR-01: Tech Stack, Orchestration Pattern, and Scale Posture

**Status:** Accepted
**Date:** 2026-08-28
**Decided by:** NextaSol (Akasha Azhar, AI CTO), autonomously per "tu dekh lay" delegation, 2026-08-28

## Context

Source document (SIGNAL_Product_Document_v2) specified approach-level tech guidance (Postgres, RAG, LangChain-or-direct-pipeline) but no coding-language-level stack. A stress-test was run against "large-scale audience" concerns before locking the decision.

## Decision

1. **Backend:** Python + FastAPI (framework default for "rapid MVP, data APIs, ML")
2. **Frontend:** Next.js (App Router) + TypeScript — matches NextaSol's existing WA VoiceAgent stack, no new pattern to learn
3. **Database:** PostgreSQL — **not** a dedicated vector-DB service. The RAG knowledge base (WHO milestones + DLD/Hearing indicators) is a small, curated, slow-growing dataset (hundreds to low thousands of entries), not a millions-of-documents corpus. Dedicated vector-DB infrastructure (Pinecone/Weaviate) is unjustified overhead at this scale; pgvector inside Postgres is sufficient. Real growth is in **case-memory** (per-child records), which is plain relational data and scales via standard Postgres partitioning.
4. **Orchestration:** Direct multi-call pipeline, **not** LangChain. Only 3 fixed prompt-roles exist (Observation → Risk Reasoning → Explanation). LangChain's abstraction overhead and version churn are a net negative at this scale of complexity — a direct pipeline is more observable, more debuggable, and (contrary to intuition) the better choice at scale, not a compromise for speed.
5. **Cache/session state:** Redis — added during the stress-test as a genuine gap. Needed for (a) adaptive follow-up conversation state, avoiding a per-turn Postgres round-trip, and (b) potential LLM-response caching for repeated milestone lookups.
6. **LLM:** Provider-agnostic wrapper around Qwen (hackathon credits) initially. Never hard-lock to one vendor — model tiering (cheap model for extraction, strongest model for reasoning) and a fallback provider are architectural requirements, not optional polish.

## Consequences

- **Positive:** Stack reuses NextaSol's proven patterns (WA VoiceAgent's Urdu STT + Next.js + Postgres/RLS), reducing real risk versus theoretical risk. Direct-pipeline orchestration keeps the reasoning chain auditable — which matters given the regulatory reasoning-trail requirement (ADR-03).
- **Negative / accepted trade-off:** No dedicated vector-DB means retrieval quality depends on disciplined pgvector indexing as the knowledge base grows; revisit only if the corpus grows into the hundreds of thousands of entries (not expected at this product's addressable scale — see PROJECT_BRIEF §6).
- **Follow-up required:** Redis and model-tiering are architectural targets for Track B (real Phase 1); the 6-day hackathon build (Track A) may ship without them if time-constrained — this is a documented, deliberate scope cut, not a silent omission.
