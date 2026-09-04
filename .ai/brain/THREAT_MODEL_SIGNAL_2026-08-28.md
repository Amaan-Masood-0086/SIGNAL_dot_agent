# Threat Model & Security/Access Document — SIGNAL
**Filename convention:** `THREAT_MODEL_[ProjectName]_[Date].md` (STRIDE + mitigations)
**Date:** 2026-08-28
**Data classification:** Highest sensitivity — children's health/developmental data
**Regulatory posture:** Non-diagnostic screening/triage aid (Cures Act §520(o)(1)(E) non-device CDS carve-out target — see ADR_03)

---

## 1. STRIDE Threat Model

| Category | Threat | Mitigation |
|---|---|---|
| **Spoofing** | Caretaker/staff credential compromise; cross-institution identity confusion | JWT with short-lived access token + refresh rotation; `institution_id` + `role` embedded as signed claims, verified on every request |
| **Tampering** | Referral or audit record edited after the fact to hide an unactioned concern | **Append-only, hash-chained `audit_log`** — each entry stores a hash of the previous entry; any edit breaks the chain and is detectable. This is not generic hardening — it is the technical basis of the product's entire liability-protection value proposition (see §3) |
| **Repudiation** | Staff member denies having seen/actioned a flag | Every write (flag creation, referral status change, escalation) logged in `audit_log` with `actor_id` + timestamp; non-repudiation is a first-class design goal, not an afterthought |
| **Information Disclosure** | Children's health data breach — the single worst-case outcome for this product | Encryption at rest (DB-level) and in transit (TLS everywhere); Row-Level Security enforced at the **Postgres role level**, never application-layer only (locked NextaSol principle); no plaintext PII in application logs; synthetic-data-only env gate for all of Phase 1 |
| **Denial of Service** | Unbounded LLM calls driving cost/availability failure | Rate limiting (30 req/min per staff member on message endpoints); adaptive follow-up loop hard-capped at `max_turns=5`; circuit breaker + fallback LLM provider |
| **Elevation of Privilege** | A caretaker at Institution A views/edits a child's record at Institution B | RLS at DB role level + IDOR T1–T5 tests mandatory on every resource endpoint (see TRD §4) |

### LLM-specific threat (outside classic STRIDE, addressed per ai-agent-architecture skill)
**Prompt injection via transcribed speech** — a caretaker's voice input could contain adversarial phrasing. Mitigation: the Observation Agent's system prompt explicitly instructs it to treat all user input as data to extract from, never as instructions to follow. No agent in the pipeline has tool-use or system-level capability that injected text could hijack.

## 2. Role-Based Access Control Matrix

| Resource / Action | Caretaker | Institution Admin (Phase 2) | NextaSol/Dev Admin |
|---|---|---|---|
| Create session, converse with agent | ✅ (own institution only) | ✅ (own institution only) | ❌ (not a product user) |
| View child profile | ✅ (own institution only) | ✅ (own institution only) | ❌ |
| View flag + reasoning trail | ✅ (own institution only) | ✅ (own institution only) | ❌ |
| Create/update referral record | ✅ (own institution only, with confirm step) | ✅ | ❌ |
| View safeguarding escalation | ❌ (routes to a restricted view — Open Item #6 pending) | Restricted pending mandatory-reporting design | ❌ |
| Read `audit_log` | ❌ | ❌ | ✅ (system-level only) |
| Cross-institution data access | ❌ (hard blocked, IDOR-tested) | ❌ | N/A |

### 2026-09-01 addendum — Admin console (built; supersedes parts of the matrix above)

The system-level admin now has a real console (`/dashboard/admin`, API `/api/v1/admin/*`), delivered with the RBAC/Admin-Panel and ADR-10 tickets. Matrix updates:

| Resource / Action | NextaSol/Dev Admin |
|---|---|
| Staff management (list all institutions, promote/demote, soft deactivate) | ✅ (audit-logged; self-demotion/self-deactivation blocked) |
| Children oversight roster (read-only, cross-institution) | ✅ — **owner-requested RBAC extension** (Akasha, 2026-09-01). Caretaker-facing surfaces remain strictly institution-scoped; the extension exists ONLY in the admin console. |
| Provider credentials (ADR-10, supersedes ADR-09) | ✅ write-only: PUT stores a Fernet-encrypted key under required `CREDENTIAL_ENCRYPTION_KEY`; responses carry only `masked_suffix`/`updated_at`/`model_name`; DELETE is soft (env fallback). Precedence: active DB row → env var. |
| Usage breakdown (staff / institution) | ✅ |
| Provider status + test-connection | ✅ (honours the same precedence; reports success/failure only) |

**New Information-Disclosure consideration (credentials at rest):** ADR-10 intentionally moves from ADR-09's "nothing to steal" to encrypted-at-rest storage. Mitigations in place: Fernet encryption, write-only API contract (encrypted column never selected for output), admin-only + rate-limited writes, audit trail without values, soft-delete only. Residual risks flagged for Track B (see PROGRESS.md): master-key rotation procedure undocumented, key shares the `.env` blast radius with JWT keys (KMS/Vault migration would shrink it), no MFA/second-admin approval on writes.

**Note:** the safeguarding-escalation access model is deliberately left conservative (nobody has full read access yet) because the downstream mandatory-reporting duty is undefined (PROJECT_BRIEF Open Item #6). Do not widen this access without that decision being made first.

### 2026-09-04 addendum — controls the deep-code audit found MISSING and now present

The audit's finding was not that these controls were designed badly. It was
that three of them were designed, built, tested — and then not connected.

**Tenant isolation was inert at runtime (F1).** Migration 0001 enables and
FORCEs row-level security and `test_postgres_rls.py` proves the policies
work. The application connected as a superuser carrying `BYPASSRLS`, which
bypasses RLS even where FORCE is set — so every database-level guarantee was
decorative and isolation depended entirely on each handler remembering its
`WHERE institution_id`. One forgotten clause was one cross-tenant leak.

Caretaker-facing endpoints now use an unprivileged role with a
transaction-local `app.institution_id`. Verified from the attacker's side:
`tests/integration/test_tenant_session_rls.py` runs queries with **no**
application filter and asserts the database returns nothing.

The same connection change restores two protections that were also inert:
`audit_log` append-only (a GRANT only binds a non-superuser) and the absence
of any `DELETE` grant on tenant data.

**"Who read this record" was unanswerable (F3).** All fifteen audited actions
were writes while seven endpoints returned child health data with no trace.
Reads are now chained like any other entry. Denied reads are deliberately not
logged — an audit row keyed to an id the caller may not own would leak what
the uniform 403 exists to hide.

**A documented basis could be silently rewritten (F11).** The knowledge base
upserts on `citation_ref` and the flag read path resolved descriptions live,
so editing a milestone changed the stated basis of every historical flag.
For a product whose regulatory argument is "the basis is documented and
reviewable", that was the one thing that could not be allowed. The trail is
now a write-time snapshot, and drift is surfaced rather than hidden.

**Newly acknowledged residual risks:**

- Free-text caretaker observations reach a third-party LLM. Prompts carry no
  name, id or institution — de-identified by construction — but a caretaker
  who types a child's name sends it. No redaction pass exists.
- Cost figures on the admin usage page are estimates priced with
  gpt-4o-mini rates that were never updated for the provider actually in use.
  Counts are exact; the money column is not, and the page says so.
- `SL-RF-022` / `HEAR-RF-014` make "any caretaker concern" a HIGH red flag at
  any age. In a tool people only open when worried this is nearly always
  true, and the acceptance dataset contradicts it in at least three cases
  (T3, T7, T8). What currently separates them is an undocumented, untested
  LLM judgement about whether a concern is "confirmed". See
  `.ai/audit/AUDIT_REPORT.md`.

## 3. Why Tamper-Evidence Is a Product Requirement, Not Just Hardening

The source document's core "why institutions pay" argument is liability protection through documented response. The source doc's own v1→v2 correction states plainly: a documented concern with no recorded action is documented negligence, not protection. That argument only survives scrutiny if the record itself cannot be plausibly alleged to have been edited after the fact. The hash-chained audit log (§1, Tampering) is the direct technical answer to that legal exposure — this line item should be treated as business-critical, not as a nice-to-have security feature.

## 4. Regulatory Grounding Requirement

Per source doc §11, the non-device Clinical Decision Support carve-out requires that a professional can independently review the basis for any recommendation. This is why `flags.reasoning_trail` citing specific `milestone_id`s is a **mandatory, non-optional** field (enforced in TRD §4, business rule #1). An opaque confidence score without a cited basis pushes SIGNAL toward regulated-device classification — this is a compliance requirement expressed as a database constraint, not a stylistic choice.

## 5. Explicitly Out of Scope for Phase 1 Threat Model

- Consent/guardianship attack surface (no real data is processed in Phase 1 — synthetic-only env gate removes this threat surface entirely until Open Item #7 is resolved)
- Mandatory-reporting legal duty (Open Item #6 — engineering builds the routing/separation, not the downstream legal process)
- DRAP medical-device classification risk (tracked in RISK_REGISTER, not a Phase 1 engineering concern)
