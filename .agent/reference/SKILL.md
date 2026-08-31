---
name: AI Software Factory — Complete SDLC Framework
description: |
  A comprehensive, security-first Software Development Lifecycle (SDLC) framework
  for AI-assisted software engineering. This skill transforms any AI assistant into
  a disciplined, autonomous software factory with built-in security, compliance,
  and professional delivery standards.

  USE THIS SKILL WHEN:
  - Starting a new software project from scratch
  - Needing structured phase-gated development (Discover → Design → Build → Deploy)
  - Requiring security-first architecture (OWASP, STRIDE threat modeling, GDPR/PCI-DSS)
  - Building backend APIs, web apps, cloud infrastructure, or data systems
  - Needing professional documentation (TRD, ADRs, runbooks, release notes)
  - Enforcing coding contracts, IDOR prevention, and compliance standards

  DO NOT USE when: answering quick factual questions or simple one-off tasks.
---

# AI Software Factory — Complete SDLC Framework

## Overview

This skill contains the **complete AI Software Factory framework** — a set of
interlocking documents that specify exactly how an AI agent must behave when
building software professionally, securely, and autonomously.

**Loaded modules:**

| File | Description |
|------|-------------|
| `masterSDLC_v1.2.md` | Security foundation — OWASP, STRIDE, compliance, threat modeling, secure coding patterns |
| `A-SDLC_v2.2.md` | AI autonomy layer — role hierarchy, phase gates, deterministic tech selection, coding contracts |
| `masterBackendSDLC.md` | Backend/API deep-dive — OWASP API Top 10, authZ/IDOR, rate limiting, queues, versioning |
| `masterWebSDLC_v1.1.md` | Web app deep-dive — browser threat model, CSP/CSRF/CORS, SSR caching safety, Next.js patterns |
| `masterCloudSDLC.md` | Cloud/IaC/DevSecOps — Terraform/K8s hardening, IAM, WAF/CDN, secrets, CI/CD, DR |
| `masterDataSDLC.md` | Data/DB deep-dive — Postgres/Redis security, RLS, migrations, PII retention, encryption |
| `masterReleaseGovernance.md` | CTO-level governance — SLO/SLA, change management, incident drills, vendor risk |
| `IDEPromptContracts.md` | IDE prompt contracts — memory discipline, context packing, Cursor/Claude agent rules |
| `AI_SoftwareFactory_README.md` | Operator guide — bootstrap prompt, repo conventions, "done" definition |

---

## How The AI Must Behave When This Skill Is Active

### Core Contracts (NON-NEGOTIABLE)

1. **Follow the 8 Phase Gates** — Never skip phases. Each gate must pass before the next begins:
   - Phase 1: DISCOVER → Phase 2: DESIGN → Phase 3: DECIDE → Phase 4: SCAFFOLD
   - Phase 5: BUILD → Phase 6: VALIDATE → Phase 7: DEPLOY → Phase 8: OPERATE

2. **Maintain `.ai/brain/` artifacts** at all times:
   - `PROJECT_BRIEF_[Name]_[Date].md`
   - `TRD_[Name]_[Date].md`
   - `THREAT_MODEL_[Name]_[Date].md`
   - `ADR_[NN]_[Decision].md` (Architecture Decision Records)
   - `TEST_PLAN.md`, `RISK_REGISTER.md`, `RUNBOOK.md`, `RELEASE_NOTES.md`

3. **Security is law** — Rules from `masterSDLC_v1.2.md` are non-negotiable and override all other guidance.

4. **Never guess requirements** — Ask or document assumptions. Never invent missing requirements.

5. **Run all checks before declaring done** — lint → typecheck → tests → security scan → docs.

### Role Hierarchy

The AI operates in a strict role hierarchy:

```
HUMAN (Vision + Approval)
  └─► AI CTO / Lead Architect (technical decisions, stack selection)
        ├─► AI System Architect (module design, interfaces)
        ├─► AI DevOps Engineer (CI/CD, IaC, deployment)
        ├─► AI Security Officer (threat model, compliance, veto power)
        └─► AI QA Engineer (test plans, coverage)
              └─► AI Executor (code generation only within scope)
```

### Bootstrap Prompt (Copy-Paste to Start Any Project)

```
You are operating under the A-SDLC framework with the full AI Software Factory skill loaded.

RULES:
1) Read and obey: masterSDLC + A-SDLC + relevant domain modules (web/backend/cloud/data).
2) Do NOT skip phases. Identify current phase and proceed only if the previous gate is passed.
3) Create and maintain .ai/brain/ with: PROJECT_BRIEF, TRD, THREAT_MODEL, ADRs, TEST_PLAN, RISK_REGISTER, RUNBOOK, RELEASE_NOTES.
4) For every code change: implement → tests → lint/typecheck → security scan → commit message.
5) Security rules are non-negotiable. No exceptions without written human approval.

START NOW — Phase 1 (DISCOVER):
- Ask the 10 mandatory discovery questions.
- Produce PROJECT_BRIEF_[ProjectName]_[Date].md
- Conduct competitor analysis (3-5 competitors) + differentiation plan
- Output a phase gate report for Gate 1.
Stop after Gate 1 and wait for approval.
```

---

## Key Security Rules (Summary)

### Always Apply

- **Authentication:** bcrypt (cost 12+) or argon2id for passwords. Short-lived JWTs (15 min access, 7 day refresh). HttpOnly + Secure + SameSite cookies.
- **Authorization:** Object-level authZ on every request. Never trust client-supplied IDs. Deny by default.
- **IDOR Prevention:** `resource.owner_id == current_user.id` check on every endpoint. Run IDOR test suite (T1-T5) in Gate 6.
- **Rate Limiting:** 5 attempts/5 min for login, 3/15 min for unauthenticated. 429 + Retry-After headers.
- **Input Validation:** Schema-based (Pydantic/Zod/Joi). Whitelist approach. Length limits everywhere.
- **Secrets:** Never in code, logs, or client. Always in Secret Manager / Vault. Rotate per schedule.
- **Logging:** Structured logs with request_id, user_id, tenant_id. Audit logs for all security events. No PII in logs.

### Web Apps

- Security headers: `HSTS`, `CSP`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`
- CSRF protection for cookie-based sessions (SameSite=Lax + synchronizer token)
- No secrets in `NEXT_PUBLIC_` env vars
- Cache-Control: `private, no-store` for authenticated pages

### Backend APIs

- Canonical response envelope: `{ success, data, meta: { request_id, timestamp, version } }`
- REST versioning: `/v1/resources/{id}`
- Webhook verification: HMAC signature + timestamp tolerance (5 min)
- Background jobs: idempotent, max retries + DLQ, no secrets in payload

### Cloud / Infrastructure

- DB and cache never exposed to internet
- IAM deny by default, scoped to specific resources
- Container: non-root user, read-only filesystem, no secrets baked in
- Secrets rotation: JWT keys (90 days), DB creds (60-90 days), API keys (60-90 days)

### Database

- App never uses DB superuser
- Row-Level Security (RLS) for multi-tenant SaaS
- Migrations reviewed like code; backward compatible by default
- Never use real PII in dev/staging (use masked or synthetic data)

---

## Tech Stack Selection (Deterministic)

The AI must use these rules — never guess:

| Scenario | Preferred Stack |
|----------|----------------|
| High concurrency (>10K users, <50ms latency) | Go + Gin/Echo |
| Rapid MVP, data APIs, ML | Python + FastAPI |
| Enterprise / large team / SOC2/HIPAA | Java + Spring Boot |
| Full-stack JS / real-time | TypeScript + NestJS |
| Serverless / edge | TypeScript + Hono |
| SEO-critical web app | Next.js (App Router) + TypeScript |
| Complex SPA / dashboard | React + Vite + TypeScript |
| Default DB | PostgreSQL |
| Cache / rate limiting | Redis |
| Container orchestration | Docker + Kubernetes |
| IaC | Terraform |
| CI/CD | GitHub Actions |

---

## Definition of "Done"

A feature is complete ONLY when:
- [ ] All requirements met per TRD/PRD
- [ ] Unit + integration tests written (80%+ coverage)
- [ ] SAST + dependency scan + secret scan = zero High/Critical
- [ ] Lint/typecheck passes
- [ ] IDOR/authZ tests pass for all resource endpoints
- [ ] API docs updated
- [ ] Runbook + Release Notes updated
- [ ] Monitoring + alerts configured for new flows
- [ ] No TODO/FIXME left unresolved

---

## Document Locations

All framework documents are in the same folder as this SKILL.md:

- `masterSDLC_v1.2.md` — Primary security reference (173 KB)
- `A-SDLC_v2.2.md` — AI orchestration reference (227 KB)
- `masterBackendSDLC.md` — Backend security reference
- `masterWebSDLC_v1.1.md` — Web/frontend security reference
- `masterCloudSDLC.md` — Cloud/DevOps security reference
- `masterDataSDLC.md` — Database/data security reference
- `masterReleaseGovernance.md` — Release + ops governance
- `IDEPromptContracts.md` — Agent/IDE memory discipline rules
- `AI_SoftwareFactory_README.md` — Quick-start operator guide

---

## AGENT v2 — Ultimate Next Level (A-Z Combined Master Structure)

### 01. Complete Agent Structure

```
AGENT_v2/
│
├── CORE_IDENTITY/
│   ├── AI_CTO/
│   ├── AI_Architect/
│   ├── AI_Security_Officer/
│   ├── AI_QA_Lead/
│   ├── AI_DevOps/
│   └── AI_Executor/
│
├── PHASE_ENGINE/
│   ├── DISCOVER/
│   ├── DESIGN/
│   ├── DECIDE/
│   ├── SCAFFOLD/
│   ├── BUILD/
│   ├── VALIDATE/
│   ├── DEPLOY/
│   └── OPERATE/
│
├── SECURITY_MODULES/
│   ├── OWASP_Top_10/
│   ├── OWASP_API_Top_10/
│   ├── STRIDE/
│   ├── IDOR_Test_Suite/
│   ├── Rate_Limiting/
│   ├── Auth_Security/
│   └── Zero_Trust/
│
├── DEVSECOPS_PIPELINE/
│   ├── Lint/
│   ├── Type_Check/
│   ├── Unit_Tests/
│   ├── SAST/
│   ├── Dependency_Scan/
│   ├── Secret_Scan/
│   ├── Container_Scan/
│   ├── IaC_Scan/
│   ├── DAST/
│   └── Canary_Deploy/
│
└── PROJECT_MEMORY/
    ├── PROJECT_BRIEF.md
    ├── PRD.md
    ├── TRD.md
    ├── THREAT_MODEL.md
    ├── ARCHITECTURE.md
    ├── API_SPEC.md
    ├── DB_SCHEMA.md
    ├── TEST_PLAN.md
    ├── SECURITY_PLAN.md
    ├── RUNBOOK.md
    ├── RELEASE_NOTES.md
    └── CHANGELOG.md
```

---

### 02. Zero Trust Enterprise Model

**Principle:** Never Trust. Always Verify.

| Layer | Controls |
|-------|----------|
| Identity | MFA, short-lived tokens |
| Device | Validation checks |
| Network | Micro-segmentation, private subnets |
| Application | Object-level authorization |
| Data | Encryption + RLS |
| Monitoring | Continuous verification |

**Hard Rules:**
- No wildcard IAM
- No public DB
- Least privilege everywhere
- Secret rotation enforced
- Short token lifetime

---

### 03. Red Team vs Blue Team

#### 🟥 Red Team (Attacker Mindset)
- Recon (endpoint discovery)
- IDOR exploitation
- SQLi, XSS, SSRF
- JWT tampering
- Privilege escalation
- Data exfiltration

#### 🟦 Blue Team (AGENT v2 Defender)
- Authorization middleware on all routes
- IDOR test suite mandatory (T1-T5)
- CSP + secure headers
- Rate limiting (layered)
- Structured logging + audit trails
- Alerting & anomaly detection

---

### 04. Attack Surface Breakdown

**External:**
- APIs, Login endpoints, File uploads, Webhooks, CDN exposure

**Internal:**
- Service-to-service calls, Background jobs, Admin panels, DB migrations

**Human:**
- Dev laptops, CI secrets, IAM misconfig, Social engineering

**Reduction Strategy:**
- Disable unused endpoints
- Strict CORS allowlist
- Minimal open ports
- Secret Manager only (no env file in prod)
- Weekly dependency audits

---

### 05. Full DevSecOps Pipeline Flow

```
Developer Commit
  → Lint
  → Type Check
  → Unit Tests
  → SAST
  → Dependency Scan
  → Secret Scan
  → Container Build
  → Container Scan
  → IaC Scan
  → Deploy to Staging
  → DAST
  → E2E Tests
  → Approval Gate
  → Canary / Blue-Green Deploy
  → Production Monitoring
```

**Automatic Security Gates:**
- Fail on High/Critical CVE
- Block deploy on DAST failure
- Coverage threshold required (80%+)
- Zero secrets allowed in repo

---

### 06. Startup CTO Edition

Focus Areas:
- MVP vs long-term scalability balance
- Cost-aware infra decisions
- Risk-based security prioritization
- Security as competitive advantage
- Observability before scale
- Governance discipline from day one

---

### 07. Cybersecurity Deep Enforcement

- OWASP Top 10 mapping (all endpoints)
- OWASP API Top 10 (all API routes)
- STRIDE threat modeling (every feature)
- ASVS control mapping (L1 minimum)
- IDOR prevention templates (T1-T5 per resource)
- Secure file handling (magic bytes + AV scan)
- Webhook verification (HMAC + timestamp)
- Least privilege IAM (deny by default)
- Disaster recovery planning (RPO/RTO defined)

---

### Final Definition

```
AGENT v2 = Human Vision
         + Structured AI Engineering Organization
         + Zero Trust Enforcement
         + DevSecOps Discipline
         + Security Governance
         = Production-Grade Secure System
```
