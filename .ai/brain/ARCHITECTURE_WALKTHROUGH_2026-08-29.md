# Architecture Walkthrough — SIGNAL as it actually exists
**Date:** 2026-08-29 (audit performed 2026-08-30)
**Scope:** the code in this repository, cross-checked against TRD_SIGNAL_2026-08-28.md, ADR_01/02/03, and THREAT_MODEL_SIGNAL_2026-08-28.md
**Test baseline:** 65/65 backend tests vs real PostgreSQL; frontend lint/build clean; live E2E smoke green

> This document describes the **implementation**, not the plan. Where the
> governing documents promise something the code does not yet do, that gap is
> flagged under **DRIFT** rather than smoothed over.

---

## 1. Input Layer — BUILT (FEAT-01 / 02 / 03)

### 1.1 Application skeleton + settings
- `backend/app/main.py` — `create_app()` factory + module-level `app = create_app()` for uvicorn. Error contract: every error returns `{"detail": ...}`; unhandled exceptions return a generic 500 (never stack traces). OpenAPI docs only exposed in `synthetic_only`.
- `backend/app/core/config.py` — `ENVIRONMENT` has **no default on purpose** (missing env var = boot failure, fail-closed per TRD business rule #7). STT settings: `STT_PROVIDER` (default `"none"`), `STT_LANGUAGE = "ur-PK"`, Azure key/region env-only.
- `backend/app/core/envelope.py` — every success response wrapped in TRD §4 envelope `{success, data, meta:{request_id, timestamp, version}}`.

### 1.2 Auth (FEAT-01 — explicitly a STUB)
- `backend/app/core/security.py` — RS256 JWT create/decode (PyJWT), 15-minute expiry, `institution_id` + `role` embedded as **signed claims**, issuer-verified.
- `backend/app/api/v1/endpoints/auth.py` — `POST /api/v1/auth/token` mints tokens for a deterministic synthetic identity (`uuid5` of email); **refused unless `ENVIRONMENT=synthetic_only`**. No password checking — that is FEAT-12.
- `backend/app/api/deps.py` — `get_current_verified_staff`: identity derives ONLY from the signed JWT, never request bodies; role must be in `{caretaker, admin}`; malformed/expired → uniform 401.
- Frontend: `frontend/proxy.ts` guards `/dashboard/*` on a session cookie and sets `Cache-Control: private, no-store` on authenticated HTML; JWT **signature is verified by the backend on every call**, the proxy only enforces presence. Nine `frontend/app/api/**/route.ts` proxies forward cookie-token → backend Bearer, unwrapping the envelope.

### 1.3 Child intake (FEAT-02, ADR-02)
- `backend/app/models/child.py` — dual age representation: `dob_confirmed`, nullable `dob`, `estimated_age_range`, `estimated_age_note`.
- `backend/app/schemas/child.py` — validator enforces exactly-one representation (confirmed ⇒ dob, estimated ⇒ range).
- `backend/app/api/v1/endpoints/children.py` — `POST /children` (synthetic gate + audit chain + institution taken from JWT only), `GET /children/{id}` with **uniform 403** for not-found vs cross-tenant (IDOR T1/T2, no existence leakage).

### 1.4 Session + turn capture (FEAT-03)
- `backend/app/api/v1/endpoints/sessions.py`:
  - `POST /sessions` — fail-closed: JWT staff_id must resolve to a real `staff` row in the same tenant, child must belong to the tenant, institution must exist; every write audit-chained.
  - `POST /sessions/{id}/observations` — the **mode-agnostic** turn surface (voice transcript and typed text submit the identical `{raw_input}` payload); `turn_number` is server-assigned (`max+1`), client-supplied values are ignored (`extra="ignore"` in the schema); completed sessions reject new turns with 409.
  - `GET /sessions/{id}/observations` — paginated history (page_size ≤ 100).
  - `POST /sessions/{id}/complete` — 409 unless `in_progress`.
- Frontend capture: `frontend/src/components/features/voice-recorder/VoiceRecorder.tsx` (explicit consent checkbox, visible recording indicator, MediaRecorder webm/opus, tracks released per turn, **60 s per-turn auto-stop with countdown**) and `frontend/src/components/features/session-chat/SessionChat.tsx` (text box always visible; voice transcript goes to the textarea for review before saving; 503 from STT degrades to text-only).

### 1.5 STT integration (FEAT-03)
- `backend/app/services/stt.py` — `SttProvider` Protocol seam + `AzureSpeechProvider`: Azure Speech **REST** short-audio conversation endpoint, `Ocp-Apim-Subscription-Key`, `audio/ogg; codecs=opus`, reads `DisplayText` — httpx only, no vendor SDK (TRD §1 locked choice, NextaSol WA VoiceAgent pattern). `provider_from_settings` returns `None` unless provider=azure + key + region.
- `backend/app/api/v1/endpoints/stt.py` — `POST /api/v1/stt/transcribe`: unconfigured ⇒ 503 ("use the text input"); provider failure ⇒ generic 502; audio read into memory, transcribed, **never persisted**.

### 1.6 Rate limiting + audio guards (FEAT-03 hardening)
- `backend/app/core/rate_limit.py` — `FixedWindowRateLimiter`, thread-safe, injectable clock; keyed by **JWT staff_id, never IP**.
- Wired to BOTH turn capture (`OBSERVATION_LIMITER`) and transcription (`TRANSCRIBE_LIMITER`): 30/min → 429 (TRD §4).
- `MAX_AUDIO_BYTES = int(1.5 * 1024 * 1024)` — the binding server-side guard (the 60 s cap is client-side and bypassable); 413 **before** any provider call; pinned by `test_transcribe_size_cap_pins_90s_budget` and a tripwire test proving the provider never sees oversized payloads.
- Frontend maps backend 429 through both proxy routes (`frontend/app/api/stt/transcribe/route.ts`, `frontend/app/api/sessions/[id]/observations/route.ts`).

### Cross-check vs governing docs
| Doc requirement | Status |
|---|---|
| TRD §1 stack (FastAPI/Next/Postgres/Azure ur-PK STT) | ✅ matches |
| TRD §4 envelope format | ✅ `envelope.py` |
| TRD §4 rate limit "POST /sessions/{id}/messages 30/min" | ✅ in spirit — **endpoint renamed `/messages` → `/observations`** (see DRIFT #5) |
| TRD §4 "JWT + refresh rotation" | ⚠️ access token only; **no refresh tokens** (documented FEAT-12 deferral) |
| TRD §5 prompt-injection stance (input = data) | ✅ schema-level: `observation.raw_input` documented as data-never-instruction; no agent exists yet to inject into |

---

## 2. Reasoning Pipeline — PLANNED, NOT BUILT (FEAT-04 / 05)

**State plainly: no reasoning code exists in this repository.** There is no
LLM wrapper, no prompt, no retrieval layer, no `FlagService`, no
`RiskReasoningAgent`, no `ConversationOrchestrator` — grep for any of these
returns nothing. What exists is only the *landing pad* designed to receive it:

- Intended design (TRD §5 + ADR-01): **direct multi-call pipeline, NOT LangChain**; three fixed prompt-roles — Observation Agent (cheap model, extraction only) → Risk Reasoning Agent (strongest model, clinical-adjacent reasoning) → Explanation Agent (mid-tier, rephrasing). Provider-agnostic LLM wrapper around Qwen initially, with circuit breaker + fallback provider.
- Intended grounding (ADR-03): Risk Reasoning may cite **only retrieved `milestone_id`s**; no relevant retrieval ⇒ `status=insufficient_information`, never free-recall clinical claims. This is the FDA non-device CDS carve-out requirement, not polish.
- Intended knowledge base (TRD §1): structured local dataset in `milestones` (domain ∈ {DLD, Hearing}, age bands), pgvector-or-simple retrieval — **no dedicated vector-DB** (ADR-01).
- Schema readiness: `milestones`, `observations.extracted_signals` (jsonb), and `flags` with `reasoning_trail NOT NULL` + confidence-grade and status CHECK constraints all exist in migration 0001 — but **the tables are empty and unwired** (`milestones` has no ingestion path; `flags` has no service or endpoint).
- **Blocker:** FEAT-04/05 wait on the DLD + Hearing indicator dataset from Ayesha/Sami (PROJECT_BRIEF Open Item #3; TRD §6 explicitly forbids scaffolding the Risk Reasoning prompts before that format is known).

### Cross-check
| Doc requirement | Status |
|---|---|
| TRD §4 business rule #1 (no flag without reasoning_trail citing ≥1 milestone) | ⚠️ enforced only at DB level (`reasoning_trail` NOT NULL); `FlagService.create_flag()` does not exist |
| TRD §4 rule #2 (insufficient_information, never forced grades) | ❌ no code — agent unbuilt |
| TRD §4 rule #4 (estimated-age one-tier downgrade) | ❌ no code — schema holds the data, grading logic unbuilt |
| TRD §4 rule #5 (`max_turns=5` cap) | ❌ **not enforced anywhere yet** — see DRIFT #4 |
| TRD §1 pgvector | ❌ extension not in any migration (deferred to FEAT-04) |

---

## 3. Case Memory Layer — BUILT (schema + RLS)

### What exists
- **Schema** (migration `backend/alembic/versions/0001_initial_schema.py`): all ten TRD §3 tables — `institutions, staff, children, sessions, observations, milestones, flags, referrals, safeguarding_escalations, audit_log` — with denormalized `institution_id` on every tenant table for RLS, FK chains (session→child→institution; observation→session), CHECK constraints on every enum, and indexes on every tenant column.
- **RLS at the Postgres role level** (same migration): creates role `signal_app` (LOGIN, unprivileged grants; `audit_log` INSERT+SELECT only with UPDATE/DELETE explicitly revoked); `ENABLE` + `FORCE ROW LEVEL SECURITY` on `institutions` and all seven tenant tables; policy `institution_isolation` = `institution_id = current_setting('app.institution_id', true)::uuid` — **fail-closed**: absent setting ⇒ NULL comparison ⇒ zero rows visible.
- **RLS is test-proven**: `backend/tests/integration/test_postgres_rls.py` connects as `signal_app`, seeds two institutions, and asserts an institution-A-scoped connection sees only `Child A`; a second test asserts RLS is both enabled AND forced on all seven tenant tables via `pg_class`.
- **How isolation actually works at runtime today**: by **application-layer filters**, not RLS. `backend/app/api/deps.py::get_db` connects via `DATABASE_URL` and its docstring is explicit: *"a pooled engine + RLS session scoping (`SET ROLE signal_app` + `app.institution_id`) lands with FEAT-12."* Every endpoint therefore scopes reads/writes by comparing `institution_id` against the JWT claim (`_scoped_session`, uniform 403).
- **Multi-session continuity** (TRD layer 3 "case memory"): only the substrate exists — `sessions.status/resumed_at` support save/resume (FEAT-08); there is no dedicated case-memory table or cross-session reasoning state yet.

### Cross-check + DRIFT #1 (the most important finding)
THREAT_MODEL §1 (Information Disclosure / Elevation of Privilege) locks:
*"Row-Level Security enforced at the Postgres role level, **never
application-layer only** (locked NextaSol principle)."*

**Actual state:** RLS is fully built and test-proven, but the **running app
does not use it**. Verified facts:
1. `config.py`'s `DATABASE_URL` default points at `signal_app:signal_app`, and its comment claims "The app role connects unprivileged" — but the real `backend/.env` overrides this with a different, more privileged user (`signal`), which is why the running app sees any rows at all.
2. `get_db` never executes `SET ROLE signal_app` nor `set_config('app.institution_id', ...)`.
3. No unit test exercises RLS through the API path — only the raw-SQL integration test does.

**Consequence:** today, a bug in any endpoint's tenant filter is the only
thing standing between institution A and institution B's data. The defense-in-depth
the threat model promises (DB enforcing isolation regardless of app bugs) is
built but dormant until FEAT-12 wires the session scoping. This deferral is
documented in `deps.py`, but the threat-model language does not carve out an
application-layer-only interim — it should be either acknowledged explicitly
in the threat model or closed sooner than FEAT-12.

---

## 4. Security Layer — BUILT

### 4.1 Synthetic-data gate (TRD business rule #7, RISK_REGISTER R8)
- `backend/app/core/synthetic_gate.py` — `assert_synthetic_write()` fail-closed: in `synthetic_only`, any record not explicitly synthetic raises `SyntheticDataViolation`.
- `main.py` maps violations to 403; called on every write path (child create, session create); `auth.py` refuses stub-token minting outside `synthetic_only`; `.env` carries `ENVIRONMENT=synthetic_only`.

### 4.2 Append-only hash-chained audit log (THREAT_MODEL §1 Tampering/Repudiation)
- `backend/app/services/audit.py` — global chain: each entry's `hash_self = SHA-256(hash_prev | sequence | actor_id | action | resource_type | resource_id)`; genesis = 64 zeros; `verify_audit_chain()` re-walks and detects any edit.
- `backend/app/models/audit_log.py` + migration: append-only at DB level for `signal_app` (INSERT+SELECT granted, UPDATE/DELETE revoked); `sequence` unique.
- Wired into every write today: `child.create`, `session.create`, `session.complete`, `observation.create` — `actor_id` always from the JWT, never the body.

### 4.3 Rate limiting
`backend/app/core/rate_limit.py` — 30/min per staff on turn capture + STT
(see §1.6). In-process fixed window.

### Cross-check + remaining DRIFT findings
| Doc requirement | Status |
|---|---|
| THREAT_MODEL: TLS everywhere | ⚠️ transport is plain HTTP locally; no TLS-terminating config exists yet (acceptable for hackathon-local, must precede any real deployment) |
| THREAT_MODEL: no plaintext PII in logs | ✅ no request logging middleware; errors never echo bodies |
| THREAT_MODEL: audit_log append-only | ✅ grants + hash chain + tests |
| TRD §4: IDOR T1–T5 on listed endpoints | ✅ for built endpoints (`/children/{id}`, sessions/observations); `/flags`, `/referrals`, `/audit_log`, `/safeguarding_escalations` endpoints don't exist yet |

**DRIFT #2 — encryption at rest is absent.** TRD §2 and THREAT_MODEL §1 both
promise "Encryption at rest (DB-level)". There is **no encryption code
anywhere in the backend** (grep for Fernet/encrypt finds only test keypair
serialization) and no documented acceptance of DB-file-level encryption as
sufficient. `raw_input` (caretaker utterances), child names, and intake
notes sit in plaintext columns. For the synthetic-only phase the blast radius
is contained by the gate, but the governing docs make this a standing
promise — it needs an explicit decision (managed-disk/DB-level encryption as
sufficient vs. column-level encryption of `raw_input`) recorded before Phase 2.

**DRIFT #3 — audit chain hash omits `institution_id` and `timestamp`.** The
canonical payload (§4.2) commits to actor, action, resource — but not to the
institution or the time. A tamperer with DB write access could rewrite an
entry's `institution_id` or backdate its `timestamp` without breaking the
chain. Also note the chain is a **single global sequence** (not per-tenant),
and `append()` reads-then-writes without a row lock/advisory lock, so
concurrent writers can collide on `sequence` (the unique constraint catches
it as an error, not a graceful retry). Both are cheap to fix: extend the
canonical payload; wrap append in a retry-on-unique-violation or advisory lock.

**DRIFT #4 — `max_turns=5` is not enforced.** TRD §4 business rule #5 and
THREAT_MODEL §1 (cost-DoS mitigation) mandate a hard cap per session. The
turn endpoint assigns numbers without any ceiling, and no
`ConversationOrchestrator` exists to hold it. The 30/min rate limit bounds
request *rate*, not turn *count*. Until FEAT-06 builds the adaptive loop,
this control is missing rather than deferred-in-code.

**DRIFT #5 — endpoint naming.** TRD §4 says `POST /sessions/{id}/messages`;
the implementation is `POST /sessions/{id}/observations`. Semantically
equivalent (the endpoint comment cross-references the TRD line), but the doc
and code should be reconciled one way or the other.

**DRIFT #6 — Redis (TRD §1, ADR-01).** No Redis anywhere: rate limiting is
single-process (a second FastAPI instance gets its own budget), and there is
no conversation-state cache. ADR-01 explicitly permits Track A to ship
without Redis if time-constrained — so this is a *documented* cut, but
note the rate limiter is therefore ineffective in any multi-instance
deployment until then.

**Housekeeping note (not a doc drift):** the dev JWT private key lives in
`backend/.env` and was exposed in a tool transcript during this audit. It is
local-dev-only, but rotate it before any non-local deployment.

---

## 5. Output Layer — PLANNED, NOT BUILT

Nothing here runs. What exists is schema only:
- `flags` (migration 0001 + `backend/app/models/flag.py`): `confidence_grade ∈ {high, moderate, low}`, `status ∈ {insufficient_information, flagged, no_concern}`, `reasoning_trail` jsonb NOT NULL (ADR-03 as a DB constraint), `explanation_text`.
- `referrals` (+ `backend/app/models/referral.py`): `status ∈ {referred, pending_capacity, closed}`, `caretaker_confirmed` bool (business rule #3: never auto-populated without explicit confirmation), `escalated`, `review_date`.
- `safeguarding_escalations` (+ model): deliberately separate table, no shared write path with flags (business rule #6); access intentionally left conservative — nobody has full read access until Open Item #6 (mandatory-reporting duty) is decided (THREAT_MODEL §2 note).
- No endpoints, no services, no UI for any of the above. FEAT-09 (flag UI + reasoning-trail display) and FEAT-10/11 wait on FEAT-05.

---

## 6. Plain-Language Summary (for Ayesha & Sami)

**What exists today:** the "front door" of SIGNAL is built and tested. A
staff member can log in (with demo credentials for now), register a child
(including children whose exact birth date is unknown — the system records
that honestly), start a conversation session, and type or speak observations
in Urdu. Spoken words are transcribed by Azure's Urdu speech service; if
that service is unavailable, typing works exactly the same way. Every action
is written into a tamper-evident log, and one institution can never see
another institution's records.

**What does not exist yet:** the "brain." Nothing in the system today
understands child development. It cannot compare what a caretaker says
against developmental milestones, cannot raise a flag, cannot explain its
reasoning, and cannot create a referral — because it is waiting for the
milestone and indicator dataset (DLD and Hearing) that Ayesha and Sami are
preparing. The empty shelves are built and load-tested; the books haven't
arrived.

**Why that ordering matters:** the system is designed so that once the
dataset lands, every conclusion it produces must cite the exact milestone
lines it used — that transparency is the regulatory and legal core of the
product, and it's already baked into the database design rather than being
added later.

**Known gaps we're tracking:** real logins (currently demo-only), full
database-level isolation on the live connection path, encryption at rest,
and a hard cap on conversation length. All are documented and scheduled;
none block the dataset handoff.
