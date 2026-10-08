# ADR-11: pgvector for Semantic Retrieval — Additive, Off by Default

**Status:** Accepted (extends ADR-04; does not supersede it)
**Date:** 2026-10-06
**Decided by:** Project owner (Amaan), requested directly: "pgvector add kr do"

## Context

ADR-04 chose full-context injection for Phase 1: every in-scope knowledge-base row is
placed in the Risk Reasoning prompt, with no embeddings and no retrieval step. It named its
own trigger for revisiting: roughly 150–200 in-scope entries, at which point
embedding-based retrieval "as originally scoped in ADR-01" takes over. ADR-01 already
settled *which* store: pgvector inside Postgres, not a separate vector service.

The live knowledge base is 94 rows, so that trigger has not fired. The owner has asked for
pgvector anyway. This ADR records how to add it without weakening anything ADR-03, ADR-04,
ADR-05 or ADR-06 guarantee.

## Decision

1. **pgvector is installed and wired, but `RETRIEVAL_MODE=full_context` stays the default.**
   Nothing changes for a deployment that does not opt in. Grades, citations and the
   reasoning trail are identical in the default mode.
2. **Semantic mode (`RETRIEVAL_MODE=semantic`) narrows the prompt, never the grade.**
   `grade()` remains deterministic code (ADR-06). The model may still cite only rows that
   were injected, and the server still validates every citation against that set (ADR-03).
3. **Semantic mode must not lose safety-critical rows.** It always includes:
   - every in-window `red_flag` row with severity HIGH (age-independent warning signs must
     never depend on a similarity score), and
   - the top-K rows **per domain**, so Speech_Language and Hearing are always retrieved
     jointly (ADR-05) and never domain-isolated.
4. **It fails toward more context, never less.** If the embedding provider is unconfigured,
   times out, errors, returns a wrong-sized vector, or any in-window row has no embedding
   (or an embedding from a different model), retrieval falls back to the full in-scope set
   (ADR-04 behaviour). The fallback is logged, and the reason is never shown to the client.
5. **Storage:** `milestones.embedding vector(1024)` (nullable), plus `embedding_model` and
   `embedding_hash` so a changed description or a changed model is detected and re-embedded.
   No ANN index: at ~100 rows an exact scan is faster and exact; an HNSW index is added only
   when the row count makes it worthwhile. Embeddings are written by a privileged script
   (`scripts/embed_knowledge_base.py`); `signal_app` keeps SELECT-only on `milestones`.
6. **No new Python dependency.** The `vector` column type is a small in-repo SQLAlchemy type
   instead of the `pgvector` + `numpy` packages, keeping the supply-chain surface unchanged.
7. **Embedding provider is configuration, not code:** any OpenAI-compatible `/embeddings`
   endpoint (`EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`). 1024 dimensions
   matches multilingual models such as `bge-m3`, which matters for Urdu / Roman Urdu input.
   The key follows ADR-09 (environment only).

## Consequences

- **Positive:** the ADR-04 revisit path exists before it is needed; the knowledge base can grow
  (v3 review release, more domains) without prompt size growing with it.
- **Negative / accepted:** a new third party can receive caretaker observation text (the
  embedding endpoint). Like the LLM, it receives text only — never a name, ID or institution —
  but it is one more processor to name in any future consent/DPA work (see Known limitations).
  Semantic mode adds one network call per turn.
- **Risk:** similarity can under-match short or code-switched Urdu text — the exact
  retrieval-recall risk ADR-04 avoided. This is why semantic mode is opt-in, why HIGH
  red flags are unconditional, and why every failure falls back to full context.
- **Infra:** `docker-compose` now uses `pgvector/pgvector:pg16` on a **new volume**
  (`signal_pgdata_pgv`). The old alpine (musl) volume is left untouched rather than reopened
  by a Debian (glibc) server, because a collation change can silently corrupt text indexes.
  Re-run the README seed steps after switching. Production must provide the `vector`
  extension; migration 0015 creates it and fails loudly if it is unavailable.

## Revisit

Flip the default to `semantic` only after a recall evaluation on real Urdu / Roman Urdu
caretaker phrasing shows no missed in-scope row, and at the ADR-04 size threshold.
