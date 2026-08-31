# Feature Backlog — SIGNAL Phase 1
**Date:** 2026-08-28
**Ordered by build sequence** (matches the 6-day hackathon plan; Track B follows the same order at full depth)

---

### FEAT-01 — Project Skeleton & Data Model
**Description:** FastAPI backend + Next.js frontend skeleton; full schema per TRD §3 (institutions, staff, children, sessions, observations, milestones, flags, referrals, safeguarding_escalations, audit_log); auth stub (JWT with institution_id + role claims).
**Acceptance criteria:** migrations run cleanly; RLS policies active at DB role level; `ENVIRONMENT=synthetic_only` gate enforced and tested.
**Depends on:** nothing — can start immediately.

### FEAT-02 — Child Profile & Estimated-Age Intake
**Description:** Registration flow capturing name/ID, intake date, and the confirmed-DOB-vs-estimated-range dual field per ADR-02.
**Acceptance criteria:** child record correctly stores `dob_confirmed`, `dob`, `estimated_age_range`; UI clearly distinguishes the two entry modes.
**Depends on:** FEAT-01.

### FEAT-03 — Voice + Text Input Layer
**Description:** STT integration (Azure Speech ur-PK, reusing NextaSol's WA VoiceAgent pattern) with text-box fallback.
**Acceptance criteria:** both input modes produce the same downstream observation format; text fallback works with zero STT dependency.
**Depends on:** FEAT-01.

### FEAT-04 — Knowledge Base Ingestion (RAG)
**Description:** Load Ayesha/Sami's DLD + Hearing milestone dataset into the `milestones` table; retrieval layer for the Risk Reasoning Agent.
**Acceptance criteria:** a test query against a known milestone returns the correct row with source citation.
**Depends on:** **PROJECT_BRIEF Open Item #3 (external data) — blocked until received.**

### FEAT-05 — Observation → Risk Reasoning → Explanation Pipeline
**Description:** The three-agent direct-call pipeline per ADR-01. Risk Reasoning Agent grounded strictly against retrieved milestones per ADR-03; enforces the insufficient-information guardrail and the estimated-age confidence downgrade.
**Acceptance criteria:** given a synthetic test conversation, the pipeline produces either a graded flag with a valid reasoning trail, or `insufficient_information` — never an ungrounded flag.
**Depends on:** FEAT-03, FEAT-04.

### FEAT-06 — Adaptive Follow-Up Loop
**Description:** Multi-turn questioning driven by the Risk Reasoning Agent, capped at `max_turns=5`.
**Acceptance criteria:** at least one follow-up question demonstrably changes the final flag's confidence grade or domain, in a test conversation.
**Depends on:** FEAT-05.

### FEAT-07 — Case Memory & Multi-Session Continuity
**Description:** Per-child conversation history; a later session's agent context references prior flags/observations.
**Acceptance criteria:** two sessions for the same child, different dates — second session visibly references the first.
**Depends on:** FEAT-05.

### FEAT-08 — Session Save/Resume
**Description:** Interrupted-shift handling — a conversation can be paused and resumed without losing turn history.
**Acceptance criteria:** interrupt mid-conversation, resume via a new request, full context intact.
**Depends on:** FEAT-05.

### FEAT-09 — Confidence-Graded Flag UI + Reasoning Trail Display
**Description:** Caretaker-facing plain-language explanation output; internally, the cited milestone(s) behind every flag.
**Acceptance criteria:** every displayed flag has a visible, traceable basis.
**Depends on:** FEAT-05.

### FEAT-10 — Loop-Closing Referral Record
**Description:** Referral status {referred, pending_capacity, closed}, responsible person, review date, escalation on missed review date. Requires explicit caretaker confirmation before persisting (never auto-populated).
**Acceptance criteria:** a flag cannot silently exist without an associated referral record; escalation logic tested against a passed review date.
**Depends on:** FEAT-09.

### FEAT-11 — Safeguarding-Escalation Pathway (Phase 1 stub depth)
**Description:** Separate table and service path for abuse/neglect-pattern signals, entirely distinct from developmental flags. **Downstream mandatory-reporting process is out of scope for Phase 1 (PROJECT_BRIEF Open Item #6)** — this ticket delivers routing/separation only.
**Acceptance criteria:** an abuse/neglect-pattern test input produces a `safeguarding_escalations` row and explicitly does NOT produce a `flags` row.
**Depends on:** FEAT-05.

### FEAT-12 — Security Pass
**Description:** Encryption (rest + transit) verification, RBAC enforcement across all endpoints, append-only hash-chained audit log, IDOR T1–T5 suite (TEST_PLAN §1), rate limiting.
**Acceptance criteria:** all items in TEST_PLAN §1, §2, §4 pass; zero High/Critical from SAST/dependency/secret scans.
**Depends on:** all prior FEAT tickets (run after core pipeline is functional, before demo polish).

### FEAT-13 — Demo Packaging
**Description:** Two-session demo scenario proving continuity (per PROJECT_BRIEF §11 success criteria); architecture diagram; short demo video; Qoder-usage evidence captured (per hackathon grading note).
**Acceptance criteria:** the exact PROJECT_BRIEF §11 success-criteria sentence is demonstrably true on the recorded demo.
**Depends on:** FEAT-01 through FEAT-12.

---

**Explicitly not ticketed for Phase 1** (per PROJECT_BRIEF §4 out-of-scope): photo input, institution dashboard, donor/compliance reporting feed, in-the-moment guidance activity, DSED/autism/ADHD/vision domains, ages 6–18, multi-tenant SaaS, offline mode. Do not create tickets for these without an explicit scope-change decision from Akasha.
