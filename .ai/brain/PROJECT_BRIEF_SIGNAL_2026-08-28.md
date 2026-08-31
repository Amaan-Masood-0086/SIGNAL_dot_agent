# Project Brief — SIGNAL
**Filename convention:** `PROJECT_BRIEF_[ProjectName]_[Date].md`
**Date:** 2026-08-28
**Technical Owner:** NextaSol (Amaan Masood — build; Akasha Azhar — AI CTO/CISO, architecture & security authority)
**External Partners:** Ayesha (domain framing, clinical grounding, knowledge base), Sami (clinical/research validation)
**Phase Gate Status:** Phase 1 — DISCOVER. **Not yet formally closed** — see Section 10, Open Items.
**Source documents:** SIGNAL_Product_Document_v2 (authoritative), superseding SIGNAL_Full_Product.docx (v1)

---

## 1. One-Line Description

SIGNAL is a voice/text conversational AI screening companion that helps untrained institutional caretakers in Pakistan notice developmental and hearing concerns in children (ages 0–6) that would otherwise go unnoticed — and routes every flagged concern into a documented, auditable referral trail toward a real clinician. It does not diagnose.

## 2. Problem

Institutional caretakers (orphanages, shelters, welfare homes) manage dozens of children with no training in developmental norms and no continuity — staff rotate, no single adult watches one child over years. The children most often missed are not the most severely affected; they are the quiet, non-disruptive ones. This is a structural gap driven by understaffing and lack of training, not a lack of care.

## 3. Users & Stakeholders

| Role | Relationship to product |
|---|---|
| Institutional caretaker | Primary user — speaks/types observations, receives flags |
| Institution admin | Secondary user (Phase 2+) — dashboard, open/closed flags |
| Child | Beneficiary — never a direct user |
| Donors / INGOs / government CP bodies | Payer — buy for accountability/compliance, not the user |
| Partner clinic / clinician | Downstream recipient of referral |

**Structural conflict (carried from source doc, not resolved by engineering):** the institution both consents to screening and is a potential subject of what it surfaces. Payer sits deliberately outside the institution (donors/grants) to reduce — not eliminate — this conflict.

## 4. Scope — Two Tracks

**Track A — Hackathon submission** (Alibaba Cloud AI Hackathon Pakistan 2026, build phase to 4 Sep 2026, Qoder-buildable, demo-focused, thin vertical slice)

**Track B — Real Phase 1** (post-hackathon NextaSol engagement, full scope below, timeline pending Section 16 decisions in source doc)

### In scope, Phase 1 (13 items, locked 2026-08-27 in working session):
1. Voice input (Urdu/English) + text fallback
2. Adaptive follow-up questioning (Observation → Risk Reasoning → Explanation pipeline)
3. Confidence-graded flag + plain-language explanation + cited reasoning trail
4. Child profile/registration (name/ID, intake date, age)
5. Estimated-age handling (confirmed DOB vs. estimated range; auto-downgrades confidence)
6. "Insufficient information" output state (safety guardrail)
7. Per-child case memory + multi-session continuity
8. Session save/resume (interrupted shifts)
9. Loop-closing referral record (responsible person, review date, escalation on missed review)
10. Separate safeguarding-escalation pathway (abuse/neglect signals ≠ developmental flags)
11. Two domains only: speech/language (DLD) + hearing
12. Age band 0–6 only
13. Encryption + role-based access control + audit logging (first-class, not hardening)

### Out of scope, Phase 1:
Photo input, institution dashboard, donor/compliance reporting feed, in-the-moment guidance activity, DSED/autism/ADHD/vision domains, ages 6–18, multi-tenant SaaS, offline mode, lab/blood-screening integration.

## 5. Sensitive Data Classification

**Highest sensitivity category** — children's health/developmental data. Pakistan has no enacted data-protection law (Bill still in draft); build to GDPR-grade technical controls regardless, because donors and international partners will require it, and because it is the right baseline for this data class. **All Phase 1 data — hackathon and real build — must be synthetic.** This is a hard technical control (env-gated), not a policy statement.

## 6. Scale — ASSUMPTION (undocumented by source, flagged per Rule 6)

No explicit target user count was given by Akasha or by Ayesha/Sami. Assumption, based on the source document's own corrected market analysis (Section 2 of SIGNAL_Product_Document_v2):
- Real addressable population: tens of thousands of institutionally-cared children in Pakistan (not millions — the "4.2M orphans" figure was explicitly rejected by the source doc itself)
- Real Phase 1 pilot (Track B): 1–2 partner institutions, 100–300 children (source doc §12)
- Hackathon demo (Track A): single-digit concurrent synthetic sessions

**This is an assumption, not a confirmed requirement. Revise if Akasha or Ayesha/Sami provide an actual target.**

## 7. Compliance Target — ASSUMPTION

GDPR-grade technical controls adopted voluntarily. DRAP (Pakistan medical-device regulator) classification review is required **before any commercial or clinical launch** (source doc §11) but is explicitly **out of scope for Phase 1 engineering** — tracked in RISK_REGISTER as a non-blocking, forward-looking item.

## 8. Deployment Target — ASSUMPTION

Cloud-hosted web app (not specified in source doc). No hosting/data-residency decision has been made by Akasha or the partners — this is flagged as Open Item #7 below and must not be assumed to be resolved.

## 9. Budget

Compute cost only is modeled in the source doc (~$0.10–0.60/screening, ~$1,000–6,000/month at 10,000 screenings/month). **No development/infrastructure budget has been discussed or set.** Not assumed here.

## 10. Open Items — Blocking Formal Gate 1 Close

These are NOT guessed. Do not proceed past DB-schema scaffolding in Quest/Claude Code until they are resolved:

| # | Item | Owner | Blocks |
|---|---|---|---|
| 1 | Hackathon team eligibility for external commercial partner | Akasha (confirm via Discord/organizers) | Legitimacy of any code written under the hackathon team name |
| 2 | Interim IP/ownership note with Ayesha/Sami | Akasha | Any shared repo/co-development |
| 3 | DLD + Hearing structured knowledge base (WHO milestones + red-flag indicators) | Ayesha/Sami | RAG grounding — nothing in the reasoning pipeline works without this |
| 4 | 5–10 synthetic caretaker test conversations | Ayesha/Sami | Test plan execution, demo scenarios |
| 5 | Engagement structure (paid vs. milestone-equity) | Akasha (business decision) | Formal Track B kickoff |
| 6 | Mandatory-reporting pathway design (abuse/neglect signals) | Ayesha/Sami + legal counsel | Safeguarding-escalation feature (#10) full depth — Phase 1 hackathon ships routing/stub only |
| 7 | Consent/guardianship mechanism for real institutional data | Ayesha/Sami + ethics review | Any use of real (non-synthetic) child data — out of scope until resolved |

## 11. Success Criteria — Phase 1 (Hackathon cut)

A caretaker can speak a description in Urdu or English, be asked at least one adaptive follow-up question that materially changes the output, receive an explained confidence-graded flag with a cited reasoning trail, and have that flag plus its loop-closing referral record persist to the child's case record — visible to a different session on a later date, proving continuity.
