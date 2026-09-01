# Test Plan — SIGNAL
**Date:** 2026-08-28
**Coverage target:** 80%+ (framework Definition of Done)
**Rule A2a reminder (NextaSol permanent rule):** every security-critical test suite must be mutation-verified — a test that passes regardless of code correctness is worse than no test.

## 1. IDOR Test Suite (T1–T5, mandatory per endpoint)

Apply to every endpoint in TRD §4's IDOR table (`/children/{id}`, `/children/{id}/sessions`, `/sessions/{id}/messages`, `/flags/{id}`, `/referrals/{id}`, `/audit_log`, `/safeguarding_escalations`):

- **T1 — Direct object reference swap:** authenticated staff at Institution A requests a resource ID belonging to Institution B → expect 403
- **T2 — Forced browsing:** sequential/guessable ID enumeration across institutions → expect 403 on every out-of-scope ID, no information leakage in the error response
- **T3 — Parameter tampering:** modify `institution_id` in request body/query where present → server must derive scope from the JWT claim, never trust client-supplied scope
- **T4 — Missing function-level access control:** non-admin role attempts admin-only actions (`GET /audit_log`) → expect 403
- **T5 — Broken object-property authorization:** partial field-level leakage (e.g. a caretaker response including another institution's data nested in a joined record) → expect the field to be absent, not just the top-level object blocked

## 2. Business Rule Tests (one per rule in TRD §4)

| Rule | Test |
|---|---|
| Flag requires reasoning_trail | Attempt to create a flag with empty `reasoning_trail` → expect rejection at service layer |
| Insufficient-information guardrail | Feed the Risk Reasoning Agent an observation below confidence threshold → expect `status=insufficient_information`, not a forced grade |
| Referral requires caretaker confirmation | Attempt to persist a referral without the confirm step → expect rejection |
| Estimated-age downgrade | Create a child with `dob_confirmed=false`, run an age-dependent milestone check → expect confidence one tier lower than the equivalent confirmed-DOB case |
| Adaptive loop cap | Simulate 6 follow-up turns → expect the loop to terminate/force a conclusion at turn 5 |
| Safeguarding separation | Trigger an abuse/neglect-pattern observation → expect a `safeguarding_escalations` row, and expect NO corresponding row in `flags` |
| Synthetic-data enforcement | Attempt to write a record with `is_synthetic=false` while `ENVIRONMENT=synthetic_only` → expect hard rejection at the application layer |

## 3. Domain / Product-Level Test Cases

- Session save/resume: start a session, interrupt mid-conversation, resume in a new request → conversation state and turn history intact
- Multi-session continuity: create two sessions for the same child on different dates → second session's agent context references the first session's flag/observations
- Reasoning-trail citation integrity: every `flags` row in test data must resolve `reasoning_trail` milestone_ids to real rows in `milestones` — no dangling citations
- Audit-log tamper-evidence: alter a historical `audit_log` row directly in the DB (test-only) → hash-chain verification must detect the break

## 3a. Cross-Domain Reasoning Tests (ADR-05 binding requirement — FEAT-05)

ADR-05 requires the Risk Reasoning Agent to check Speech_Language and Hearing jointly, never domain-isolated. This is not optional coverage — it is a named binding test requirement in that ADR, flagged during the ADR-04/05/grading-rules verification pass (2026-08-31) as missing from this file until now.

- **T5** (`signal_test_conversations_v2.csv`) — 3-year-old, limited talking + doesn't listen. Correct resolution is a Hearing flag, not Speech_Language, and only emerges by cross-referencing "doesn't react to sound" against the speech-delay pattern. A domain-isolated agent would misattribute this to language delay alone.
- **T6** (`signal_test_conversations_v2.csv`) — 4-year-old, ear-pulling + says "what?" + sits close to TV. OME/glue-ear pattern; resolves correctly only when hearing is checked as a live differential rather than assumed absent because the presenting complaint sounds language-related.

Both cases must pass through the full pipeline (not just the FEAT-04 retrieval layer, which is already verified to return both domains unconditionally) once FEAT-05 is built. A regression here — the pipeline defaulting to a single-domain read — would be a silent but serious correctness failure, since FEAT-04's structural guarantee (no domain parameter in the query) only proves both domains are *available* to the agent, not that the agent actually *uses* both.

## 4. Security Scans (Definition of Done, every phase)

- SAST + dependency scan + secret scan = zero High/Critical
- Rate-limit test on `/sessions/{id}/messages` (30/min) — confirm 429 beyond threshold
- Encryption verification: confirm TLS on all endpoints, confirm at-rest encryption on `children`, `flags`, `referrals`, `audit_log` tables specifically

## 5. Test Data

Blocked on PROJECT_BRIEF Open Item #4 (5–10 synthetic caretaker conversations from Ayesha/Sami). Until received, use minimal internally-authored synthetic fixtures covering: a clear DLD signal, a clear Hearing signal, an ambiguous/insufficient-information case, and one abuse/neglect-pattern case for the safeguarding-separation test.

## 6. Admin Console & Credentials Tests (added 2026-09-01 — ADR-10 + admin console)

Implemented in `backend/tests/test_credentials.py` and `test_admin_console.py`:

- **Write-only enforcement** — sentinel value asserted absent from every response across success/failure/error paths; `encrypted_value` never part of the status query (`load_only` display columns only).
- **Encryption round-trip** — DB column ≠ plaintext; service resolves it only at provider construction; undecryptable token degrades to env fallback.
- **Audit grep** — raw value (and even the masked suffix) absent from every audit row.
- **Precedence** — active DB row beats env for key AND model; env used when no active row; deactivate falls back to env.
- **Guards** — caretaker 403 on all admin surfaces incl. children oversight roster; PUT rate-limited 5/5min; unknown provider 404.
- **Regression** — env-only setups unchanged (FEAT-03/FEAT-05 paths); suite-wide 360 tests vs real PostgreSQL.
