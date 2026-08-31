---
description: Backend development workflow — build order, coding contracts, and patterns for SIGNAL's API.
---

# Backend Development Workflow — SIGNAL

## Tech Stack

- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy
- **DB:** PostgreSQL (Row-Level Security enforced at the DB **role** level — locked NextaSol principle, not app-layer only)
- **Validation:** Pydantic v2
- **Auth:** JWT (RS256), `institution_id` + `role` embedded as signed claims
- **Cache/session-state:** Redis (adaptive-loop conversation state — see ADR-01)
- **LLM orchestration:** Direct multi-call pipeline — Observation → Risk Reasoning → Explanation. **NOT LangChain** (ADR-01)

## Build Order (A-SDLC Phase 5 — MUST Follow, see FEATURE_BACKLOG_SIGNAL.md for full tickets)

```
1. Database models + Alembic migrations (FEAT-01)
2. Pydantic schemas (request/response)
3. Service layer (business logic) — including FlagService, ReferralService, RiskReasoningAgent
4. API routes (endpoints)
5. Tests (unit + auth + authorization + SIGNAL business-rule tests)
```

Never skip steps. Never write routes before models exist. Never write agent-reasoning logic (FEAT-05) before the knowledge base (FEAT-04) is loaded — a Risk Reasoning Agent with no retrieval source cannot ground a reasoning trail.

## File Structure

```
backend/app/
├── api/
│   ├── deps.py              ← Auth dependencies
│   └── v1/endpoints/        ← Route handlers
├── core/
│   ├── config.py            ← Settings from .env (incl. ENVIRONMENT=synthetic_only gate)
│   ├── security.py          ← JWT, passwords
│   └── rate_limit.py        ← Redis rate limiter
├── db/
│   └── base.py              ← DB session
├── models/                  ← SQLAlchemy models: institutions, staff, children,
│                                sessions, observations, milestones, flags,
│                                referrals, safeguarding_escalations, audit_log
├── schemas/                 ← Pydantic schemas
└── services/                ← Business logic
    ├── audit.py             ← Hash-chained audit logging
    ├── observation_agent.py ← Extraction only, no judgment
    ├── risk_reasoning_agent.py  ← RAG-grounded, adaptive follow-up, confidence grading
    ├── explanation_agent.py ← Plain-language output
    ├── flag_service.py      ← Enforces mandatory reasoning_trail
    └── referral_service.py  ← Enforces confirmation gate
```

## Coding Contracts (MUSTs)

1. Every endpoint MUST have Pydantic schema validation
2. Every write MUST create an audit log entry (hash-chained)
3. Every query MUST be institution-scoped (filter by `staff.institution_id`)
4. Every list endpoint MUST support pagination
5. Server-generated values (IDs, confidence grades, timestamps) MUST never come from request body
6. All secrets MUST come from environment variables
7. All errors MUST return `{"detail": "message"}` format
8. All IDs MUST be UUID v4
9. All timestamps MUST be ISO 8601 UTC
10. **`flags.reasoning_trail` MUST cite ≥1 real `milestone_id` — enforced in `FlagService.create_flag()`, rejected otherwise** (ADR-03)
11. **`dob_confirmed=false` MUST auto-downgrade confidence one tier on age-dependent checks** (ADR-02)
12. **`safeguarding_escalations` writes MUST use a separate service and table from `flags` — no shared code path**
13. **All writes MUST check `is_synthetic=true` against the `ENVIRONMENT=synthetic_only` gate**
14. **Adaptive follow-up loop MUST hard-stop at `max_turns=5`**
15. **`referrals` MUST require an explicit caretaker confirmation step before persisting**

## MUST-NOTs

1. MUST NOT expose stack traces or DB errors in responses
2. MUST NOT use raw SQL strings
3. MUST NOT accept `actor_id` from request body — always derived from JWT
4. MUST NOT skip writing tests
5. MUST NOT add dependencies without stating which and why
6. MUST NOT store secrets in code
7. MUST NOT allow page_size > 100
8. MUST NOT return cross-institution data
9. **MUST NOT let any agent (Observation/Risk Reasoning/Explanation) treat caretaker input as an instruction — data only** (prompt-injection defense)
10. **MUST NOT allow the Risk Reasoning Agent to generate a clinical claim from free recall — retrieved-context citation only** (ADR-03)
11. **MUST NOT accept real (non-synthetic) child data anywhere in Phase 1, regardless of source**

## Pending Work

See `.ai/brain/FEATURE_BACKLOG_SIGNAL.md` for the full 13-ticket backlog.
See `.ai/brain/RISK_REGISTER.md` for open blockers (R2: knowledge-base data pending; R6: Urdu STT accuracy unvalidated).

## Deep Dive (On-Demand Only)

- `.agent/reference/A-SDLC.md` — Full build order, phase gates, coding contracts
- `.agent/reference/masterSDLC.md` — Full security implementation patterns
- `.agent/reference/masterDataSDLC.md` — Postgres/RLS deep-dive
- `.agent/workflows/ai-agent-development.md` — the reasoning-pipeline layer specifically
