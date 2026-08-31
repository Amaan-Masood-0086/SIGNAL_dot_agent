---
description: CTO-level code review checklist for SIGNAL. Run this workflow before any PR merge or deployment.
---

# Code Review Checklist (AI CTO) — SIGNAL

## Pre-Review Setup

// turbo
1. Read `.ai/brain/RISK_REGISTER.md` for known open risks
2. Read `.ai/brain/FEATURE_BACKLOG_SIGNAL.md` for the ticket this PR addresses and its acceptance criteria

## Security Review (MUST PASS ALL)

- [ ] All endpoints use `get_current_verified_staff` (not a lower-tier dependency)
- [ ] All queries filter by `current_staff.institution_id` — no cross-institution data leakage
- [ ] No raw SQL strings anywhere — SQLAlchemy ORM only
- [ ] No secrets/keys hardcoded in code
- [ ] All Pydantic schemas have `Field(...)` constraints
- [ ] Server-generated values (IDs, confidence grades, timestamps) not accepted from client
- [ ] Error responses don't expose internal details
- [ ] Rate limiting applied to write endpoints
- [ ] Audit log created for every state change, hash-chain intact

## SIGNAL-Specific Review (do not skip — these are product-critical, not generic)

- [ ] **Every new `flags` row has a non-empty `reasoning_trail` citing a real `milestone_id`** — no ungrounded flags
- [ ] **Risk Reasoning Agent prompt does not permit free-recall clinical claims** — retrieval-grounded only
- [ ] **`dob_confirmed=false` correctly downgrades confidence** on any touched age-dependent logic
- [ ] **`safeguarding_escalations` writes never touch the `flags` table** — verify no shared service/code path was introduced
- [ ] **`ENVIRONMENT=synthetic_only` gate is not bypassable** by any new code path touched in this PR
- [ ] **Adaptive follow-up loop still respects `max_turns=5`** if this PR touches the conversation orchestrator
- [ ] **Referral creation still requires the explicit caretaker confirmation step**

## Auth Review

- [ ] JWT tokens checked for blacklist status
- [ ] `actor_id` set server-side from JWT, never from request
- [ ] Account lockout check in auth chain

## Testing Review

- [ ] Every endpoint has a happy-path test
- [ ] 401 test (no token)
- [ ] 403 test (wrong institution)
- [ ] 422 test (invalid input)
- [ ] IDOR T1–T5 present for any new resource endpoint (`.ai/brain/TEST_PLAN_SIGNAL.md` §1)
- [ ] Relevant business-rule test present (`.ai/brain/TEST_PLAN_SIGNAL.md` §2)

## Performance Review

- [ ] Pagination on all list endpoints (max page_size=100)
- [ ] Database indexes on filter/sort columns
- [ ] No N+1 query issues
- [ ] LLM calls in the reasoning pipeline are not duplicated/re-fired unnecessarily per turn

## Before Deployment

- [ ] `JWT_SECRET_KEY` / RS256 key files present, correctly configured
- [ ] CORS origins set to production domain (not localhost)
- [ ] Redis available (session-state + rate limiter depend on it)
- [ ] `.env` has all required variables, no secrets committed
- [ ] Alembic migrations applied
- [ ] `ENVIRONMENT` is explicitly set (never defaults silently to a non-synthetic mode)
