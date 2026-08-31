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

**Note:** the safeguarding-escalation access model is deliberately left conservative (nobody has full read access yet) because the downstream mandatory-reporting duty is undefined (PROJECT_BRIEF Open Item #6). Do not widen this access without that decision being made first.

## 3. Why Tamper-Evidence Is a Product Requirement, Not Just Hardening

The source document's core "why institutions pay" argument is liability protection through documented response. The source doc's own v1→v2 correction states plainly: a documented concern with no recorded action is documented negligence, not protection. That argument only survives scrutiny if the record itself cannot be plausibly alleged to have been edited after the fact. The hash-chained audit log (§1, Tampering) is the direct technical answer to that legal exposure — this line item should be treated as business-critical, not as a nice-to-have security feature.

## 4. Regulatory Grounding Requirement

Per source doc §11, the non-device Clinical Decision Support carve-out requires that a professional can independently review the basis for any recommendation. This is why `flags.reasoning_trail` citing specific `milestone_id`s is a **mandatory, non-optional** field (enforced in TRD §4, business rule #1). An opaque confidence score without a cited basis pushes SIGNAL toward regulated-device classification — this is a compliance requirement expressed as a database constraint, not a stylistic choice.

## 5. Explicitly Out of Scope for Phase 1 Threat Model

- Consent/guardianship attack surface (no real data is processed in Phase 1 — synthetic-only env gate removes this threat surface entirely until Open Item #7 is resolved)
- Mandatory-reporting legal duty (Open Item #6 — engineering builds the routing/separation, not the downstream legal process)
- DRAP medical-device classification risk (tracked in RISK_REGISTER, not a Phase 1 engineering concern)
