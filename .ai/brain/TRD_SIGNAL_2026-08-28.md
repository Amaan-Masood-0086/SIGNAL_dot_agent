# Technical Requirements Document — SIGNAL
**Filename convention:** `TRD_[ProjectName]_[Date].md`
**Date:** 2026-08-28
**Companion to:** PROJECT_BRIEF_SIGNAL_2026-08-28.md
**Skills applied:** ai-software-factory-complete-sdlc-framework, ai-software-factory-upgrades, ai-agent-architecture

---

## 1. Tech Stack (locked, deterministic — do not deviate without a new ADR)

| Layer | Choice | Rule applied |
|---|---|---|
| Backend | Python + FastAPI | Framework default: "Rapid MVP, data APIs, ML" |
| Frontend | Next.js (App Router) + TypeScript | Simple chat-style UI, no SEO-critical need but consistent with NextaSol's WA VoiceAgent stack |
| Database | PostgreSQL | Framework default; Row-Level Security enforced at DB role level (locked NextaSol principle) |
| Cache / session state | Redis | Framework default for cache/rate-limiting; also needed for adaptive-loop conversation state (see ADR_01) |
| LLM orchestration | Direct multi-call pipeline (NOT LangChain) | 3 fixed roles only — see ADR_01 |
| Speech-to-text | Cloud Urdu STT (Azure Speech, ur-PK) | NextaSol already has a proven Urdu STT pipeline from WA VoiceAgent — reuse, don't rebuild |
| LLM | Provider-agnostic wrapper; Qwen (hackathon credits) as initial provider | See ADR_01 — never hard-lock to one vendor |
| Knowledge base / RAG | Structured local dataset (WHO milestones + DLD/Hearing indicators), pgvector or simple retrieval — NOT a dedicated vector-DB service | Corpus is small/curated, not millions of docs — see ADR_01 |
| CI/CD | GitHub Actions | Framework default |

## 2. System Architecture — 4 Layers + Cross-Cutting Security

```
┌─────────────────────────────────────────────────────────┐
│  INPUT LAYER                                             │
│  Voice (Urdu/English, STT) | Text fallback                │
│  → all input treated as DATA, never as model instruction  │
└───────────────────────┬───────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  REASONING PIPELINE (grounded via RAG)                    │
│  Observation Agent → Risk Reasoning Agent → Explanation    │
│  Agent — 3 distinct prompt-roles, direct multi-call        │
└───────────────────────┬───────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  CASE MEMORY LAYER                                         │
│  PostgreSQL — per-child record, session history,           │
│  multi-session continuity, RLS at DB role level             │
└───────────────────────┬───────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  OUTPUT LAYER                                               │
│  Confidence-graded flag + reasoning trail | Referral        │
│  record (loop-closing) | Safeguarding escalation (separate) │
└─────────────────────────────────────────────────────────┘

   ══════════ SECURITY (wraps all layers) ══════════
   Encryption at rest/transit · RBAC · Append-only,
   hash-chained audit log · Rate limiting · Synthetic-
   data-only env gate
```

## 3. Data Model (summary — full DDL generated at Scaffold phase)

| Table | Key fields | Notes |
|---|---|---|
| `institutions` | id, name | Tenant boundary for RLS |
| `staff` | id, institution_id, role, auth fields | role ∈ {caretaker, admin} |
| `children` | id, institution_id, name, intake_date, **dob_confirmed (bool)**, dob (nullable), **estimated_age_range**, estimated_age_note, *archived_at (nullable)*, *archived_reason (nullable)* | See ADR_02. Archive columns added in migration 0006 — see §4a; archive is reversible and no DELETE grant exists on this table |
| `sessions` | id, child_id, staff_id, status {in_progress, completed, abandoned}, mode {voice, text}, started_at, resumed_at | Supports save/resume (feature #8) |
| `observations` | id, session_id, turn_number, raw_input, extracted_signals (jsonb) | Observation Agent output — extraction only |
| `milestones` | id, domain {DLD, Hearing}, age_band_min_months, age_band_max_months, description, source | Knowledge base, RAG-retrieved, populated from Ayesha/Sami's data (Open Item #3) |
| `flags` | id, session_id, child_id, domain, confidence_grade, **reasoning_trail (jsonb → cites milestone_ids)**, explanation_text, status {insufficient_information, flagged, no_concern} | See ADR_03 — reasoning_trail is mandatory, not optional |
| `referrals` | id, flag_id, status {referred, pending_capacity, closed}, responsible_person, review_date, escalated (bool) | Loop-closing record (feature #9) |
| `safeguarding_escalations` | id, session_id, child_id, signal_description, status | **Deliberately separate table from `flags`** (feature #10) |
| `audit_log` | id, actor_id, action, resource_type, resource_id, timestamp, hash_prev, hash_self | Append-only, hash-chained — tamper-evident (see THREAT_MODEL) |

`is_synthetic` boolean flag propagates from `institutions` down — enforced at the application layer via a hard env gate (`ENVIRONMENT=synthetic_only`) for the entire Phase 1 build.

## 4. 🤖 AI Coding Agent Instructions
<!-- BINDING for Qoder, Claude Code, or any other IDE building this project -->
<!-- Non-negotiable — implement exactly -->

### IDOR-Sensitive Endpoints (T1–T5 tests mandatory on every row)

| Endpoint | Owner Field | Check |
|---|---|---|
| `GET /children/{id}` | institution_id | `child.institution_id !== staff.institution_id` → 403 |
| `GET /children/{id}/sessions` | institution_id (via child) | same |
| `POST /sessions/{id}/messages` | institution_id (via session→child) | same |
| `GET /flags/{id}` | institution_id (via flag→child) | same |
| `PATCH /referrals/{id}` | institution_id (via referral→flag→child) | same |
| `GET /audit_log` | admin-role only | `staff.role !== 'admin'` → 403, regardless of institution |
| `POST /safeguarding_escalations` | institution_id (via session) | same; additionally never exposed to non-admin roles on read |

### Security Controls (Mandatory)
- Auth: JWT — short-lived access token + refresh rotation; `institution_id` and `role` embedded as claims
- Rate limits: `POST /sessions/{id}/messages` — 30/min per staff member
- Validation: Pydantic schemas on every FastAPI route
- File uploads: N/A in Phase 1 (no photo input)

### Business Rules (Never Bypass in Code)
1. No `flag` record may be created without a non-empty `reasoning_trail` citing ≥1 `milestone_id` → enforce in `FlagService.create_flag()`
2. If confidence falls below the "insufficient information" threshold, the system MUST emit `status=insufficient_information`, never force a graded flag → enforce in `RiskReasoningAgent.evaluate()`
3. A `referral` record can never auto-populate without an explicit caretaker confirmation step → enforce in `ReferralService.create_referral()`
4. If `dob_confirmed=False`, confidence grade is automatically downgraded one tier on any age-dependent milestone check → enforce in `RiskReasoningAgent.grade_confidence()`
5. Adaptive follow-up loop is hard-capped at `max_turns=5` per session → enforce in `ConversationOrchestrator`
6. `safeguarding_escalations` are NEVER written to or merged with the `flags` table → enforce via separate service class, separate table, no shared write path
7. All data created outside `ENVIRONMENT=synthetic_only` gate is rejected at the application layer, not just the UI

### Response Format
```json
{ "success": bool, "data": {}, "meta": { "request_id": "uuid", "timestamp": "ISO", "version": "v1" } }
```

### Tests Required
- IDOR T1–T5 for every endpoint listed above
- One test per business rule confirming it cannot be bypassed
- Coverage ≥ 80%

## 4a. Addendum — 2026-09-04 (surface added after the deep-code audit)

Contracts introduced or changed since §4 was written. Kept as an addendum so
the original spec stays readable as the Phase-1 baseline.

### Two database paths (audit F1)

The schema builds row-level security and the tests prove the policies work,
but the running app connected as a superuser carrying `BYPASSRLS`, so every
table-level guarantee was inert and tenant isolation rested entirely on each
handler remembering its `WHERE institution_id`. There are now two paths:

| Setting | Role | Used by |
|---|---|---|
| `DATABASE_URL` | privileged | migrations, `/auth/token` (finds a staff row by email before any institution is known), admin cross-institution reads |
| `TENANT_DATABASE_URL` | `signal_app` — no superuser, no BYPASSRLS, no DELETE | every caretaker-facing endpoint |

The tenant session sets `app.institution_id` **transaction-locally**. Not a
detail: with a pooled connection a session-level setting would survive into
whichever request borrowed that connection next — the exact cross-tenant
leak this layer exists to prevent. Proven from the hostile direction in
`tests/integration/test_tenant_session_rls.py`: queries run with **no**
application filter and the database still refuses another institution's rows.

### Read access is audited (audit F3)

All fifteen original audited actions were writes, so "who opened this child's
record" was unanswerable. Added: `child.read`, `flag.read`, `flag.list`,
`admin.children_list`. Detail views log per record; list views log per query
(a roster read is one act of access, and a row per child would bury the chain
it exists to make readable).

**Denied reads are deliberately NOT logged.** A 403 never confirms the record
exists; writing an audit row keyed to an id the caller may not own would leak
precisely what the uniform 403 hides.

### Child archive (migration 0006)

There was previously no way to take a child off the roster at all.

| Endpoint | Contract |
|---|---|
| `POST /children/{id}/archive` | Body `{reason}` — mandatory, min length enforced. 409 if already archived |
| `POST /children/{id}/restore` | 409 if not archived |
| `GET /children?status=active\|archived\|all` | Allowlisted; default `active`. Archived rows sort newest-first |

Archive, never delete: a mistaken registration and a child who has left both
leave the roster, but only one carries a retention question, and children's
health records carry long statutory retention. No `DELETE` grant exists on
`children` for the app role — pinned by test.

### Reasoning request gains a reply language

`POST /sessions/{id}/reason` accepts `response_language: "auto" | "ur" | "en"`
(default `auto`, which mirrors whatever the caretaker wrote).

A **closed enum, never free text.** Caretaker input stays fenced as DATA and
is never treated as instructions, so "reply in Urdu" typed into the box must
not steer the model; a structured field is how the preference gets in without
reopening that door. Only text a caretaker READS is affected — signals,
grades and citation_refs stay English as the clinical record.

### Reasoning trail is a snapshot, not a live lookup (audit F11)

The knowledge base upserts on `citation_ref`, and the read path resolved
descriptions live — so a six-month-old flag displayed today's wording rather
than the wording its grade was made on. The trail now carries `basis` and
`source` captured at write time, the read path prefers the snapshot, and
`kb_drifted` tells the reader when the reference has since changed.

### Provider timeout and output budget

- `LLM_TIMEOUT_SECONDS` (default 90) is a setting. A hardcoded 60s was
  observed killing turns outright.
- `max_tokens` caps were tried and **reverted**. `deepseek-v4-flash` spends
  its budget on internal reasoning, so a 400-token ceiling left nothing for
  the reply and the model returned an empty string — the whole turn lost. A
  cap is a guess about a specific model's reasoning overhead, and guessing
  low destroys the turn rather than shortening it. `MAX_TOKENS_BY_TIER` stays
  in place but empty, with the reason recorded at the definition.

### Admin usage is split per provider

STT and the LLM are different vendors with separate invoices, so one merged
figure reconciled against neither. `GET /admin/usage` now returns
`by_provider`. Provider test-connection calls are ledgered too — each LLM one
is a real billed call the cost page was omitting; their cost is recorded NULL
rather than invented.

## 5. 🤖 AI/Agent Architecture Section (per ai-agent-architecture skill — BINDING for Phase 5 BUILD)

### Feature Type & Stack
Hybrid: RAG assistant (grounded knowledge base) + voice agent (Urdu STT) + light multi-agent orchestration (3 fixed prompt-roles, not autonomous tool-calling).

### Scaling Plan
- Stateless FastAPI instances behind a load balancer
- Redis for session/conversation-state caching (avoids per-turn Postgres round-trips)
- Model tiering: Observation Agent (cheap/fast model — extraction only) vs. Risk Reasoning Agent (strongest available model — the actual clinical-adjacent reasoning) vs. Explanation Agent (mid-tier — rephrasing, not reasoning)
- Circuit breaker + fallback provider on the LLM wrapper (do not depend on a single vendor's uptime)

### Tool Allowlist (if agentic)
None in Phase 1 — the pipeline does not call external tools; it calls the LLM against retrieved knowledge-base context only. No autonomous tool-use surface to allowlist yet.

### LLM-Specific Risks Addressed
- **Prompt injection**: transcribed caretaker speech is treated strictly as data; the Observation Agent's system prompt explicitly instructs it never to treat user input as commands
- **Hallucination on clinical claims**: Risk Reasoning Agent is restricted to citing retrieved `milestone_id`s only — no free-recall generation of clinical facts (see ADR_03)
- **Cost DoS**: `max_turns=5` hard cap + rate limiting (Section 4)
- **Overreliance**: referral record requires explicit caretaker confirmation before persisting (business rule #3)

## 6. Open Dependencies

RAG grounding, milestone table population, and test-conversation coverage all depend on Open Items #3–#4 in PROJECT_BRIEF (Ayesha/Sami's data). **Do not scaffold the Risk Reasoning Agent's prompt logic until the milestone dataset format is known** — schema above is designed to accept it once delivered, but exact prompt-grounding strategy is deferred.
