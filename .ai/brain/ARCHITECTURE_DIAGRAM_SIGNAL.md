# SIGNAL — Architecture Diagram (FEAT-13 deliverable)

**Date:** 2026-08-31 · Phase 1 as-built (FEAT-01 → FEAT-12 + RBAC/Admin Panel)

## System overview

```mermaid
flowchart TB
    subgraph Browser["Caretaker browser (Next.js App Router, TS strict)"]
        UI_LOGIN[Login] --> UI_DASH[Dashboard roster]
        UI_DASH --> UI_CHILD[Child profile + Screening history]
        UI_DASH --> UI_SESSION[Session chat: voice / text capture]
        UI_SESSION --> UI_PANEL[ReasoningPanel — adaptive loop]
    end

    subgraph Proxy["Next.js proxy routes (cookie session, CSRF, Zod)"]
        P1["/api/auth/* · /api/children/* · /api/sessions/*\n/api/stt/transcribe · /api/sessions/:id/reason"]
    end

    subgraph Backend["FastAPI (port 8002) — direct multi-call pipeline, NOT LangChain"]
        DEPS["Auth chain: JWT RS256 → verified staff →\nrequire_active_staff / get_current_admin_staff (system-level)"]
        EP["Endpoints: sessions · reasoning · flags · referrals\nstt · usage · audit_log · admin/*"]
        subgraph Agents["Three-agent pipeline (FEAT-05)"]
            OA["Observation Agent\n(cheap tier — extraction only,\ninput fenced as DATA)"]
            RA["Risk Reasoning Agent\n(strong tier — grounded,\nadaptive, max_turns=5)"]
            EA["Explanation Agent\n(mid tier — plain language,\ndiagnosis scrub)"]
            OA --> RA --> EA
        end
        SVC["Services: knowledge (retrieval + grade),\nflag / referral / safeguarding / audit / usage,\nllm seam + circuit breaker, synthetic fallback"]
        DEPS --> EP --> Agents
        EP --> SVC
    end

    subgraph External["External providers (env-only keys, ADR-09)"]
        STT["Azure Speech (ur-PK STT)"]
        LLM["LLM primary (+ optional fallback endpoint)"]
    end

    subgraph Data["PostgreSQL 16 (docker) — RLS at DB role level"]
        DB_TENANT["tenant tables (RLS: institution_isolation,\nfail-closed, FORCE)"]
        DB_KB["milestones — global KB, SELECT-only to app role"]
        DB_AUDIT["audit_log — append-only, hash-chained"]
        DB_USAGE["usage_log — append-only cost ledger"]
    end

    UI_SESSION --> P1 --> EP
    UI_PANEL --> P1
    SVC --> STT
    SVC --> LLM
    SVC --> DB_TENANT
    SVC --> DB_KB
    SVC --> DB_AUDIT
    SVC --> DB_USAGE
```

## The reasoning loop (one turn)

```mermaid
sequenceDiagram
    participant C as Caretaker
    participant E as POST /sessions/{id}/reason
    participant O as Observation Agent
    participant R as Risk Reasoning Agent
    participant G as grade() (deterministic)
    participant X as Explanation Agent

    C->>E: raw_input (voice transcript or text)
    E->>E: scope check · rate limit (30/min) · active guard
    E->>O: fenced input + age context
    alt safeguarding pattern
        O-->>E: route out → safeguarding_escalations row, NO flag
    else developmental
        E->>R: signals + FULL in-scope KB (both domains, ADR-04/05)<br/>+ case memory (prior sessions, FEAT-07)
        alt not concluded & turn < 5
            R-->>E: follow_up_question (discriminating)
            E-->>C: status=follow_up
        else concluded (or turn 5 forced)
            R->>G: confirmed flags / missed milestones / modifiers
            G-->>R: HIGH · MODERATE · LOW_MONITOR · INSUFFICIENT_INFORMATION<br/>(+ citation_refs — the model never picks the grade)
            R->>X: grade + trail
            X-->>E: plain-language text (server-scrubbed, ADR-07)
            E->>E: FlagService.create_flag (trail must resolve, ADR-03/08)
            E-->>C: status=flagged + grade + citations + explanation
        end
    end
    Note over E: every LLM call → usage_log · every write → audit_log (hash-chained)
```

## Trust boundaries at a glance

| Boundary | Mechanism |
|---|---|
| Tenant isolation | JWT-signed `institution_id` claim + app-layer scoping on EVERY endpoint + Postgres RLS (ENABLE+FORCE, fail-closed) for the unprivileged `signal_app` role |
| Admin (system-level) | `get_current_admin_staff` — DB row is the privilege authority; cross-institution ONLY on marked admin endpoints |
| Tamper-evidence | hash-chained append-only `audit_log` (UPDATE/DELETE revoked at DB level) + `/audit_log/integrity` |
| Secrets | env-var only (ADR-09); no key storage surface anywhere |
| Grounding | citations validated server-side against the injected knowledge universe; `grade()` deterministic (ADR-06) |
| Cost/DoS | rate limits (30/min capture+reasoning, 5/5min provider tests) + `usage_log` visibility + max_turns=5 |
