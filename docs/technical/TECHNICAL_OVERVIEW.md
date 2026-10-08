# SIGNAL: technical architecture

*For the technical analysis round. Every number and claim here was checked against the repository (code, lock files, CI and ADRs).*

---

## 1. What the system is, in technical terms

SIGNAL is a **multi-tenant web application** with a **deterministic clinical core** and a **small, fenced AI layer**.

- A caretaker submits free-text (or speech converted to text) observations about a child.
- A three-step LLM pipeline turns the text into structured signals, matches them against a curated knowledge base, and writes a short explanation.
- The **grade** (HIGH, MODERATE, LOW-monitor, INSUFFICIENT) is **not produced by the model**. It is computed by a pure Python function from written rules.
- Every result is stored with its evidence in a tamper-evident, tenant-isolated database.

The core design decision: **use the LLM for language, use code for the decision, use the database to enforce isolation.**

---

## 2. Technology stack

| Layer | Technology | Version | Why this choice |
|---|---|---|---|
| Backend language | Python | 3.12 (CI) | Strong typing with Pydantic, mature ecosystem |
| Web framework | FastAPI + Uvicorn | 0.141.1 / 0.52.4 | Typed request/response contracts, dependency injection for auth |
| ORM / migrations | SQLAlchemy 2 + Alembic | 2.0.52 / 1.19.1 | Explicit schema history; migrations create roles and RLS |
| Database | PostgreSQL | 16 | Row-level security is a hard requirement |
| DB driver | psycopg 3 | 3.3.4 | Native Postgres features, transaction-local settings |
| Validation | Pydantic + pydantic-settings | 2.13.5 / 2.15.0 | Whitelist schemas; settings that fail at boot |
| Auth tokens | PyJWT (RS256) + cryptography | 2.13.0 / 50.0.1 | Asymmetric signing; Fernet for credential encryption |
| Frontend | Next.js (App Router), React | 16.3.3 / 19.2.8 | Server-side proxy keeps tokens away from browser JS |
| Language / styling | TypeScript 5, Tailwind CSS 4 | | Type-safe UI, token-based design system |
| Forms / data | react-hook-form, zod 4, TanStack Query 5 | | Client validation mirrors the server contract |
| Tests | pytest, Vitest, Playwright | 9.1.1 / 3 / 1.63 | Real Postgres for backend tests |
| LLM | Any OpenAI-compatible endpoint | | Provider-agnostic; tested with DeepSeek |
| Speech to text | Azure Speech or Knowlez (adapter) | | Voice is optional, text always works |
| Infra | Docker Compose (database only), GitHub Actions | | Reproducible local DB and CI gates |

**Deliberately not used:** LangChain or any agent framework (the pipeline is plain, testable function calls), a vector database (the knowledge base is 94 rows, see section 7), Redis (rate limiting is in-process for now), SQLite (never a fallback, because RLS is Postgres-only).

---

## 3. System architecture

```
 Browser (React 19)
     |   same-origin calls only
     v
 Next.js server  ---------------------------------------------+
   - proxy.ts: auth gate + per-request CSP nonce               |
   - /api/* route handlers: thin proxies, Zod-validate         |
   - session JWT lives in an HttpOnly cookie                   |
     |                                                         |
     |  HTTP + Bearer (server to server)                       |
     v                                                         |
 FastAPI backend                                               |
   - auth + role dependency on every route                     |
   - Origin (CSRF) check on state-changing routes              |
   - security headers, request id, rate limits                 |
   - services: pipeline, knowledge, flags, referrals, audit    |
     |                         |                  |            |
     v                         v                  v            |
 PostgreSQL 16            LLM provider        STT provider     |
  - RLS per institution    (OpenAI-compatible)  (Azure/Knowlez)|
  - hash-chained audit log                                     |
  - two DB roles                                               |
```

**Why a proxy layer in Next.js?** The browser never holds a token it can read. The JWT sits in an HttpOnly, SameSite=Lax cookie. Next.js route handlers attach it server-to-server, so XSS cannot steal it, and the backend is not directly reachable from page scripts.

---

## 4. The screening pipeline (the core of the product)

One caretaker turn runs through these steps in `risk_pipeline.py`:

```
 caretaker text
      |
 1. Observation agent (LLM)      extract OBSERVABLE signals only
      |                          safeguarding pattern? -> leave pipeline, separate pathway
      v
 2. Retrieval (SQL)              all in-scope knowledge rows for the child's age,
      |                          BOTH domains together (speech + hearing)
      v
 2b. Case memory                 this child's earlier flags (same child only)
      |
 3. Risk Reasoning agent (LLM)   may cite ONLY retrieved rows; may ask ONE follow-up
      |                          hard stop at 5 caretaker turns
      v
 4. grade()  (pure Python)       deterministic rules (ADR-06)
      |
 5. Explanation agent (LLM)      plain-language text in the caretaker's language,
      |                          validated server-side (no diagnostic label)
      v
 6. Persist                      flag + reasoning trail snapshot + audit entry + usage row
```

### 4.1 Age handling (ADR-02)
A child is stored with **either** a confirmed date of birth **or** an estimated range (lower and upper months plus a reference date). Never both.

- Confirmed DOB: exact age in months.
- Estimated range: evaluation uses the **younger bound**, and `age_uncertain` is carried through every result.
- Under uncertain age, a borderline delay is graded **down** to the LOW-monitor floor. Age-independent red flags (regression, caretaker hearing concern) are **not** lowered.

### 4.2 Retrieval (ADR-04, ADR-05)
Retrieval is a plain SQL query: entries whose age window covers the child's age, excluding Phase-2 rows, for **both** domains at once. Hearing loss and language delay look the same from outside, so the domains are never queried in isolation. The whole in-scope set is injected into the prompt ("full-context injection"), which removes the retrieval-recall risk that embeddings introduce on a small dataset.

### 4.3 Grounding and citation validation (ADR-03)
The reasoning agent returns `citation_ref` values (for example `HEAR-RF-008`). The server resolves each one against exactly the set it injected. A reference outside that set is rejected, so a clinical claim recalled from model memory cannot reach the record.

### 4.4 Deterministic grade (ADR-06)
`grade()` is a pure function, so the same evidence always gives the same grade.

| Condition | Result |
|---|---|
| Key information missing, or no confirmed evidence at all | INSUFFICIENT_INFORMATION |
| Any one HIGH-severity red flag | HIGH |
| Two or more MODERATE red flags in the same domain | HIGH |
| One MODERATE red flag, or a missed milestone plus a supporting observation | MODERATE |
| Only a missed milestone (borderline delay) | LOW_MONITOR (the floor) |

Risk modifiers can raise a grade but never lower it. There is no "no concern" outcome by design.

### 4.5 Safeguarding route
If the observation agent detects an abuse or neglect pattern, the turn leaves the developmental pipeline. A separate service writes an escalation row, and **no developmental flag is produced**.

### 4.6 Prompt-safety measures
- Caretaker text is fenced as data, and the system prompt forbids following instructions inside it.
- The LLM receives age context and observation text only, never a name, ID or institution.
- Responses use strict JSON contracts. A malformed reply raises a contract error that is logged server-side with the raw prefix, while the client sees a generic message.
- Reply language follows the caretaker (Urdu, Roman Urdu or English). Signals, grades and citation refs stay in English as the clinical record.

### 4.7 Resilience
- Circuit breaker with an optional fallback provider.
- Retry for transient provider errors.
- Configurable timeout (default 90 seconds).
- Voice degrades to typing and never blocks a screening.

---

## 5. Data model

Core tables:

| Table | Purpose | Notes |
|---|---|---|
| `institutions` | Tenants | Root of isolation |
| `staff` | Users | Role is `caretaker` or `admin`; password hash column |
| `children` | The subjects | Dual age model; archive fields; optional assigned caretaker |
| `sessions` | One screening sitting | Status, mode (voice or text), resume stamp |
| `observations` | Each turn | Raw input plus extracted signals |
| `flags` | The result | Domain, grade, explanation, **reasoning trail**, knowledge-base revision |
| `referrals` | Follow-up | Responsible person, review date, escalation, outcome |
| `safeguarding_escalations` | Separate pathway | Written with zero flags |
| `milestones` | Knowledge base | 94 rows, global, **not** tenant-scoped, app role is SELECT-only |
| `audit_log` | Tamper-evident record | Hash-chained, append-only |
| `usage_log` | Cost ledger | Per call, per provider |
| `provider_credentials` | LLM and STT keys | Fernet-encrypted, write-only API |

The `knowledge_releases`, `knowledge_revisions` and `knowledge_review_notes` tables hold the dormant v3 review release. They have no effect on live scoring.

**Identifiers:** UUIDs for every public ID, never sequential integers. The knowledge base also has a human-readable `citation_ref` (ADR-08), which reasoning trails cite instead of the UUID.

**Reasoning trail snapshot:** a flag stores the exact wording of every cited row *at the time of grading*. If the knowledge base is edited later, old flags are not silently rewritten, and the read path reports `kb_drifted`.

---

## 6. Security architecture

### 6.1 Tenant isolation lives in the database
Two connection paths:

| Path | Role | Used for |
|---|---|---|
| `DATABASE_URL` | privileged | migrations, login lookup, admin cross-institution reads |
| `TENANT_DATABASE_URL` | `signal_app`, unprivileged | all tenant requests |

Tenant requests set `app.institution_id` as a **transaction-local** setting, taken from the verified JWT. RLS is enabled **and forced** on every tenant table. `signal_app` has no superuser, no `BYPASSRLS` and no `DELETE` grant. A session-level setting would leak across pooled connections, which is why the setting is transaction-local.

This is verified from the attacker's side: `test_tenant_session_rls.py` runs queries with **no application-level filter** and asserts the database still returns nothing from another institution.

### 6.2 Authentication and authorization
- RS256 JWT in an HttpOnly, SameSite=Lax cookie, never in localStorage.
- Role is checked against the **database row** (active and admin), not only the token claim.
- Uniform `403` for both "does not exist" and "belongs to another institution", so existence never leaks (IDOR defence).
- Login throttling is keyed by **email**, because every login arrives from the Next.js server and a per-IP key would throttle all users together.

### 6.3 Audit trail
Hash-chained and append-only. It records **reads as well as writes** (`child.read`, `flag.read`, list queries), so "who opened this child's record" is answerable. Denied reads are deliberately not logged, because a row keyed to an unowned ID would leak what the uniform 403 hides. An integrity endpoint verifies the chain and reports the first position where tampering occurred.

### 6.4 Web hardening
- Per-request **CSP nonce** (`proxy.ts`), no `unsafe-inline` for scripts. Pages that need a nonce are forced dynamic.
- Origin check on every state-changing route, explicit allowlist, never a wildcard.
- Security headers on every response, `private, no-store` on data, `Server` and `X-Powered-By` banners removed.
- Provider credentials: Fernet-encrypted at rest, write-only API (only the last four characters are ever shown).

### 6.5 Supply chain and CI
`.github/workflows/ci.yml` runs on every PR: pytest, **bandit**, **pip-audit**, `tsc`, ESLint, Vitest, production build, **npm audit** (high), and **gitleaks**. Dependencies are pinned and locked.

---

## 7. Why we made these architecture decisions

| Decision | Alternative rejected | Reason |
|---|---|---|
| Deterministic `grade()` (ADR-06) | LLM decides the grade | Reproducible, auditable, no model drift |
| Full-context injection (ADR-04) | RAG with embeddings | 94 rows fit in one prompt; no recall risk on a small, sparse dataset |
| Joint speech and hearing retrieval (ADR-05) | Separate domain queries | The two conditions present identically |
| Dual age model (ADR-02) | Require a DOB | Most children have no confirmed DOB |
| Citation validation (ADR-03) | Trust model citations | Blocks claims recalled from model memory |
| No diagnostic labels (ADR-07) | Name conditions | Screening aid, not a diagnosis |
| RLS with a non-superuser app role | `WHERE institution_id` in each handler | A forgotten filter cannot leak data |
| Direct API calls | LangChain-style framework | Fewer layers, easier to test and audit |

### Optional extension: pgvector (ADR-11)
A semantic-retrieval path using pgvector exists on a separate branch. It is **off by default** (`RETRIEVAL_MODE=full_context`). When enabled, it always keeps every HIGH red flag and the nearest rows of *each* domain, and it falls back to full context on any embedding failure. It is a path for scaling past about 150 to 200 knowledge rows, not part of the current default behaviour.

---

## 8. Verification

| Suite | Result (published figures) |
|---|---|
| Backend | 498 tests: 496 passed, 1 skipped, 1 expected failure |
| Frontend | 25 passed |
| Total | **523** |

- All backend tests run against **real PostgreSQL**, with the schema applied only through Alembic.
- The skipped test is a deployed-tenant-URL guard.
- The expected failure (`T6`, the "R14 divergence") is intentional: the clinical dataset expects MODERATE while ADR-06's counting rule gives HIGH. It is blocked pending clinical sign-off rather than patched.
- IDOR tests T1 to T5 exist for resource endpoints.

---

## 9. Known limitations

- **Password verification is not implemented.** Any password is accepted, gated to `ENVIRONMENT=synthetic_only`. This is the main reason the build must not be exposed publicly.
- No consent model and no retention or erasure policy yet (legal decisions come first).
- Access is institution-scoped, not relationship-based.
- Rate limiting is in-process, so it needs Redis for multi-instance deployment.
- "Any caretaker concern" is a HIGH red flag at any age, which is almost always true in a tool opened only when someone is worried.
- LLM latency is about 45 seconds per call on the tested provider; prompt size and output length were ruled out by measurement.
- Phase 1 runs on synthetic data only and is not cleared for clinical use.

---

## 10. API surface (summary)

| Area | Examples |
|---|---|
| Auth | `POST /auth/token`, `GET /auth/me` |
| Children | `GET/POST /children`, `GET /children/{id}`, archive and restore |
| Sessions | `POST /sessions`, `POST /sessions/{id}/observations`, `POST /sessions/{id}/reason`, `/resume`, `/complete`, `GET /sessions/{id}/result` |
| Flags | `GET /flags/{id}`, `GET /children/{id}/flags`, `GET /sessions/{id}/flags` |
| Referrals | `POST /flags/{id}/referral`, `GET/PATCH /referrals/{id}` |
| Speech | `POST /stt/transcribe` |
| Admin | institutions, staff (role, active), child assignment, providers (`PUT/DELETE/test`), usage, audit and integrity |
| Knowledge review | release preview, compare, rollback, review notes (admin only) |

All routes live under `/api/v1/`, return a uniform envelope with a `request_id`, and enforce role and ownership checks.

---

**Team:** Sami (lead) · Ayesha · Amaan
**Repository:** https://github.com/Amaan-Masood-0086/SIGNAL_dot_agent
