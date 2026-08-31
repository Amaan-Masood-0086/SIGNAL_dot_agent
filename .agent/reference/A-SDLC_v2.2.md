---
description: A-SDLC — AI autonomy layer for secure development. Role hierarchy, phase gates, tech selection engine, coding contracts, IDE playbooks.
---

# A-SDLC: AI-Native Autonomous Secure Development Lifecycle

## Purpose

This document is the **AI autonomy layer** that sits on top of the SecureSDLC foundation (`masterSDLC.md`). Together, they form a **complete, self-executing software factory** where AI agents build, test, secure, and deploy projects with minimal human intervention.

**SecureSDLC** = Security processes, compliance, threat modeling, coding standards
**A-SDLC** = AI orchestration, tech selection, coding contracts, automation, IDE playbooks

Feed BOTH files to any AI (Claude, GPT, Cursor, Antigravity, Copilot) and it becomes a fully autonomous, security-first development engine.

---

## Software Factory Quickstart (Read This First)

### Required Document Set (MUST Load)

- `masterSDLC.md` — Security foundation (OWASP, threat modeling, compliance, secure coding rules)
- `A-SDLC.md` — AI control plane (roles, phase gates, deterministic stack selection, coding contracts)
- `IDEPromptContracts.md` (recommended) — IDE prompt contracts + rule files + memory discipline

### Domain Modules (Load Based on Project Type)

- `masterWebSDLC.md` — Web applications (browser threat model, CSP/CSRF/CORS, SSR/edge cache safety, Next.js/React patterns)
- `masterMobileSDLC.md` — Mobile applications (OWASP MASVS, secure storage, Expo/React Native hardening, EAS CI/CD)
- `masterBackendSDLC.md` — Backend/APIs (OWASP API Top 10, authZ/IDOR prevention, rate limiting, jobs/queues, API versioning)
- `masterCloudSDLC.md` — Cloud/IaC/DevSecOps (Terraform/K8s hardening, IAM least privilege, WAF/CDN, secrets vault patterns, CI/CD, DR)
- `masterDataSDLC.md` — Data/DB (Postgres/Redis security, row-level security, migrations governance, PII retention, encryption + key rotation)
- `masterReleaseGovernance.md` — CTO-level release governance (SLO/SLA, change mgmt, incident drills, vendor risk, cost budgets)
- `IDEPromptContracts.md` — IDE rules + agent memory discipline (Cursor rules, antigravity prompts, AGENTS.md templates)

**Rule:** If you do not load the relevant domain module, the AI must assume it is missing context and must NOT improvise platform-specific security.

### Optional: Project OS (Notion)

- `NotionProjectOS.md` — Notion setup + templates. AI outputs **copy‑paste ready** Notion pages/rows (because AI cannot edit your Notion directly).

### Required “Project Brain” Folder (AI Memory)

On project start, AI MUST create and maintain:

- `.ai/brain/` (preferred) **or** `.cursor/brain/` (Cursor-friendly)

Minimum artifacts (files) inside:

1. `PROJECT_BRIEF_[ProjectName]_[Date].md`
2. `TRD_[ProjectName]_[Date].md` (technical design)
3. `THREAT_MODEL_[ProjectName]_[Date].md` (STRIDE + mitigations)
4. `ADR_[NN]_[Decision].md` (Architecture Decision Records)
5. `TEST_PLAN_[ProjectName].md`
6. `RISK_REGISTER.md` (security + delivery risks)
7. `RUNBOOK.md` (ops + incidents)
8. `RELEASE_NOTES.md` (every release)

### Non‑Negotiable Quality Gates (Every Phase)

At the end of **every** phase, AI must run and report:

- **Security:** SAST + dependency scan + secret scan + authZ/IDOR checks + rate limits + secure headers
- **Quality:** lint/format + typecheck + unit/integration tests + coverage threshold
- **Performance:** baseline metrics + budgets (API p95, DB slow queries, web Lighthouse, mobile memory/bundle)
- **UX:** responsive checks (multiple viewports) + accessibility checks (WCAG AA / platform a11y)
- **Ops:** structured logs + metrics + tracing + alerts + rollback plan

---

## Document Information

| Field | Value |
|-------|-------|
| **Version** | 2.2 |
| **Companion Documents** | masterSDLC.md • masterWebSDLC.md • masterMobileSDLC.md • masterBackendSDLC.md • masterCloudSDLC.md • masterDataSDLC.md • masterReleaseGovernance.md • IDEPromptContracts.md |
| **Created** | 2026-02-10 |
| **Last Updated** | 2026-02-20 |
| **Target AI Models** | Claude Opus 4.6, GPT-4+, Cursor AI, Antigravity, GitHub Copilot |
| **Target IDEs** | Cursor, Antigravity, VS Code, JetBrains |
| **Scope** | Universal — any project, any tech, any scale |

---

## Table of Contents

1. [A-SDLC Overview & Philosophy](#1-a-sdlc-overview--philosophy)
2. [AI Role Hierarchy & Control Plane](#2-ai-role-hierarchy--control-plane)
3. [Phase-Gated Execution Model](#3-phase-gated-execution-model)
4. [Deterministic Tech Stack Selection Engine](#4-deterministic-tech-stack-selection-engine)
5. [AI Coding Contracts & Guardrails](#5-ai-coding-contracts--guardrails)
6. [IDE Agent Playbooks](#6-ide-agent-playbooks)
7. [Autonomous Feedback & Self-Correction Loop](#7-autonomous-feedback--self-correction-loop)
8. [Golden Infrastructure Stack](#8-golden-infrastructure-stack)
9. [One-Command Project Bootstrap](#9-one-command-project-bootstrap)
10. [AI Prompt Library for Secure Code Generation](#10-ai-prompt-library-for-secure-code-generation)
11. [Compliance Automation Engine](#11-compliance-automation-engine)
12. [Monitoring & Observability Automation](#12-monitoring--observability-automation)
13. [Disaster Recovery & Rollback Automation](#13-disaster-recovery--rollback-automation)
14. [Token & Context Management for AI IDEs](#14-token--context-management-for-ai-ides)
15. [Universal Project Type Support](#15-universal-project-type-support)
16. [Internationalization & Localization](#16-internationalization--localization-i18n)
17. [API Versioning Strategy](#17-api-versioning-strategy)
18. [Multi-Tenancy Architecture Rules](#18-multi-tenancy-architecture-rules)
19. [Feature Flags & Gradual Rollout](#19-feature-flags--gradual-rollout)
20. [Auto-Generated Documentation Rules](#20-auto-generated-documentation-rules)
21. [Load Testing & Performance Strategy](#21-load-testing--performance-strategy)
22. [Frontend UI/UX Standards](#22-frontend-uiux-standards)
23. [Backend API Design Patterns](#23-backend-api-design-patterns)
24. [Authentication Flow Patterns](#24-authentication-flow-patterns)
25. [Git Workflow & Branching Strategy](#25-git-workflow--branching-strategy)
26. [Real-Time Features](#26-real-time-features)
27. [File Storage & CDN Strategy](#27-file-storage--cdn-strategy)
28. [Email & Notification System](#28-email--notification-system)
29. [Database Migration Strategy](#29-database-migration-strategy)
30. [Error Handling Patterns](#30-error-handling-patterns)
31. [Background Jobs & Task Queues](#31-background-jobs--task-queues)
32. [Environment Management](#32-environment-management)
33. [Command Reference](#33-command-reference)

---

## 1. A-SDLC Overview & Philosophy

### 1.1 What is A-SDLC?

A-SDLC (Autonomous Secure Development Lifecycle) is a **governance and orchestration framework** that transforms AI coding assistants from passive helpers into a **coordinated, self-correcting software factory**.

Traditional SDLC tells humans what to do.
SecureSDLC tells humans how to do it securely.
**A-SDLC tells AI agents how to execute the entire process autonomously.**

### 1.2 Core Principles

| Principle | Description |
|-----------|-------------|
| **Deterministic Decisions** | AI never guesses. Every choice follows explicit rules. If no rule exists, AI asks the human. |
| **Role Separation** | Each AI agent has a defined role. Agents do NOT overstep their authority. |
| **Phase Gates** | AI cannot skip phases. Each phase must pass validation before the next begins. |
| **Self-Correction** | When code fails tests or security scans, AI fixes it automatically — up to 3 attempts, then escalates. |
| **Human-in-the-Loop** | Humans provide vision and approve critical decisions. They do NOT write code. |
| **Security is Law** | Security rules from masterSDLC.md are non-negotiable. No agent can override them. |
| **Contract-Driven Code** | Every line of generated code must satisfy a contract. No cowboy coding. |
| **Universal Applicability** | This framework works for ANY project type, ANY language, ANY scale. |

### 1.3 How A-SDLC and SecureSDLC Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                     HUMAN (Vision & Approval)                    │
│  "I want to build X"                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    A-SDLC (This Document)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AI Control Plane                                        │    │
│  │  ├─ Role assignment                                      │    │
│  │  ├─ Tech stack selection                                 │    │
│  │  ├─ Phase gating                                         │    │
│  │  ├─ Coding contracts enforcement                         │    │
│  │  └─ Autonomous feedback loops                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SecureSDLC (masterSDLC.md)                              │    │
│  │  ├─ Security rules                                       │    │
│  │  ├─ OWASP compliance                                     │    │
│  │  ├─ Threat modeling                                      │    │
│  │  ├─ Testing strategy                                     │    │
│  │  └─ Deployment security                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AI Executors (Cursor, Claude, Antigravity)              │    │
│  │  ├─ Code generation                                      │    │
│  │  ├─ Testing                                              │    │
│  │  ├─ Deployment                                           │    │
│  │  └─ Self-correction                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. AI Role Hierarchy & Control Plane

### 2.1 Role Architecture

AI agents operate in a strict hierarchy. Higher-level agents make decisions. Lower-level agents execute. No agent may exceed its authority.

```
┌──────────────────────────────────────────────────────────────┐
│  LEVEL 0: HUMAN OPERATOR                                      │
│  Authority: Vision, final approval, budget, timeline          │
│  Actions: Describes idea, approves architecture, approves     │
│           deployment to production                            │
│  Does NOT: Write code, choose libraries, configure infra      │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  LEVEL 1: AI CTO / LEAD ARCHITECT                             │
│  Authority: Final technical decisions, architecture, security │
│             veto power, tech stack approval                   │
│  Actions:                                                     │
│   - Interprets human vision into technical requirements       │
│   - Selects tech stack using Selection Engine (Section 4)     │
│   - Designs system architecture                               │
│   - Defines API contracts                                     │
│   - Creates database schemas                                  │
│   - Approves or rejects lower-level agent outputs             │
│   - Escalates to human when rules are ambiguous               │
│  Constraints:                                                 │
│   - Cannot override security rules from masterSDLC.md         │
│   - Cannot deploy to production without human approval        │
│   - Must justify all tech stack choices with reasoning         │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  LEVEL 2: SPECIALIST AGENTS                                   │
│                                                               │
│  ┌─────────────────────────────────────────┐                  │
│  │  AI SYSTEM ARCHITECT                     │                  │
│  │  - Designs module boundaries             │                  │
│  │  - Defines folder structure              │                  │
│  │  - Creates interface contracts           │                  │
│  │  - Designs data flow                     │                  │
│  └─────────────────────────────────────────┘                  │
│                                                               │
│  ┌─────────────────────────────────────────┐                  │
│  │  AI DEVOPS ENGINEER                      │                  │
│  │  - CI/CD pipeline creation               │                  │
│  │  - Infrastructure as Code                │                  │
│  │  - Container orchestration               │                  │
│  │  - Cloud resource provisioning           │                  │
│  │  - Secret management setup               │                  │
│  └─────────────────────────────────────────┘                  │
│                                                               │
│  ┌─────────────────────────────────────────┐                  │
│  │  AI SECURITY OFFICER                     │                  │
│  │  - Threat modeling                       │                  │
│  │  - Security review of all outputs        │                  │
│  │  - Penetration test design               │                  │
│  │  - Compliance verification               │                  │
│  │  - Veto power on insecure code           │                  │
│  └─────────────────────────────────────────┘                  │
│                                                               │
│  ┌─────────────────────────────────────────┐                  │
│  │  AI QA / TEST ENGINEER                   │                  │
│  │  - Test case generation                  │                  │
│  │  - Test execution and reporting          │                  │
│  │  - Coverage analysis                     │                  │
│  │  - Performance/load test design          │                  │
│  └─────────────────────────────────────────┘                  │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  LEVEL 3: EXECUTOR AGENTS (Cursor, Claude, Antigravity)       │
│  Authority: Code generation ONLY within assigned scope        │
│  Actions:                                                     │
│   - Implement features as specified by Level 1/2              │
│   - Write code following coding contracts (Section 5)         │
│   - Write tests for their own code                            │
│   - Fix lint errors and test failures                         │
│  Constraints:                                                 │
│   - CANNOT make architecture decisions                        │
│   - CANNOT choose or add new dependencies without approval    │
│   - CANNOT modify infrastructure files                        │
│   - CANNOT modify security configurations                     │
│   - CANNOT skip writing tests                                 │
│   - MUST follow file ownership rules                          │
│   - MUST ask Level 1 if requirements are unclear              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Decision Authority Matrix

| Decision Type | Human | AI CTO | Architect | DevOps | Security | Executor |
|--------------|-------|--------|-----------|--------|----------|----------|
| Project vision & goals | **DECIDES** | Advises | - | - | - | - |
| Budget & timeline | **DECIDES** | Advises | - | - | - | - |
| Tech stack selection | Approves | **DECIDES** | Advises | Advises | Veto | - |
| System architecture | Approves | **DECIDES** | Executes | Advises | Reviews | - |
| API design | Reviews | **DECIDES** | Executes | - | Reviews | - |
| Database schema | Reviews | **DECIDES** | Executes | - | Reviews | - |
| Security policy | Approves | Enforces | - | - | **DECIDES** | Follows |
| CI/CD pipeline | - | Approves | - | **DECIDES** | Reviews | - |
| Cloud infrastructure | Approves | Approves | - | **DECIDES** | Reviews | - |
| Code implementation | - | Reviews | Reviews | - | Reviews | **EXECUTES** |
| Test strategy | - | Approves | - | - | Reviews | Executes |
| Production deployment | **APPROVES** | Initiates | - | Executes | Validates | - |
| Incident response | Notified | Coordinates | - | Executes | **LEADS** | Assists |
| Dependency additions | - | **APPROVES** | Requests | Requests | Reviews | Requests |
| Rollback decisions | Notified | **DECIDES** | - | Executes | Advises | - |

### 2.3 Conflict Resolution Protocol

When AI agents disagree:

```
1. SECURITY ALWAYS WINS
   If Security Agent vetoes something, it is vetoed. Period.
   Only the Human can override a security veto (with documented justification).

2. HIERARCHY PREVAILS
   Level 1 overrides Level 2.
   Level 2 overrides Level 3.
   
3. RULES OVER OPINIONS
   If a deterministic rule exists (Section 4), follow the rule.
   If no rule exists, escalate to the next level up.

4. ESCALATION PATH
   Executor → Specialist → AI CTO → Human
   Maximum 2 escalations before human decides.

5. DEADLOCK RESOLUTION
   If AI CTO cannot resolve within its rules:
   → Present options to human with pros/cons
   → Human decides
   → Decision is logged and becomes a new rule
```

### 2.4 Communication Protocol Between Agents

When operating in a single AI session (e.g., one Claude conversation), the AI switches "hats" between roles. It MUST clearly indicate which role it is currently operating as:

```markdown
## Role Switching Format

[AI CTO]: I've analyzed the requirements. For this e-commerce platform with 
high traffic and PII handling, the tech stack will be:
- Backend: Go + Gin (high concurrency needed)
- Database: PostgreSQL (PII requires row-level security)
- Reasoning: Traffic estimate >10K concurrent → Go outperforms Python/Node

[AI ARCHITECT]: Based on CTO's stack decision, here's the module structure:
/cmd/api/         → API entry point
/internal/handler → HTTP handlers
/internal/service → Business logic
/internal/repo    → Database layer

[AI SECURITY]: Reviewing architect's structure. 
✅ Separation of concerns: correct
✅ Internal packages prevent external access
⚠️ MISSING: /internal/middleware for auth/rate-limiting
→ Architect must add middleware layer

[AI EXECUTOR]: Implementing handler for user registration as specified.
Following contracts: input validation, bcrypt hashing, rate limiting...
```

---

## 3. Phase-Gated Execution Model

### 3.1 Why Phase Gates?

AI agents tend to rush ahead. They'll start coding before the architecture is designed, or deploy before tests pass. Phase gates **force sequential discipline**.

**RULE: No phase can begin until the previous phase's exit criteria are met.**

### 3.2 The 8 Phases

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Phase 1  │───▶│ Phase 2  │───▶│ Phase 3  │───▶│ Phase 4  │
│ DISCOVER │    │ DESIGN   │    │ DECIDE   │    │ SCAFFOLD │
│          │    │          │    │          │    │          │
│ Gate: ✓  │    │ Gate: ✓  │    │ Gate: ✓  │    │ Gate: ✓  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                    │
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Phase 8  │◀───│ Phase 7  │◀───│ Phase 6  │◀───│ Phase 5  │
│ OPERATE  │    │ DEPLOY   │    │ VALIDATE │    │ BUILD    │
│          │    │          │    │          │    │          │
│ Gate: ✓  │    │ Gate: ✓  │    │ Gate: ✓  │    │ Gate: ✓  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 3.3 Phase Details

#### Phase 1: DISCOVER (Idea → Requirements)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI CTO |
| **Input** | Human's project idea (can be vague) |
| **Activities** | Ask clarifying questions, identify project type, determine scale, identify compliance needs, assess security requirements, determine budget constraints |
| **Output** | Project Brief Document |
| **SecureSDLC Link** | Phase 1 (Secure Ideation) + Phase 2 (PRD) |

**Questions AI MUST Ask (if not already answered):**

```
1. What does this project do? (1-2 sentences)
2. Who are the users? (public/internal/enterprise)
3. Expected scale? (users: <1K / 1K-100K / 100K-1M / 1M+)
4. Sensitive data involved? (PII / financial / health / none)
5. Compliance requirements? (GDPR / HIPAA / PCI-DSS / SOC2 / none)
6. Deployment target? (cloud / on-prem / hybrid / edge)
7. Budget level? (free-tier / startup / enterprise)
8. Timeline? (MVP: weeks / months / quarters)
9. Existing codebase? (greenfield / brownfield / migration)
10. Must-have integrations? (payment / auth / email / SMS / etc.)
```

**MANDATORY: Project Documentation & Analysis**

After gathering all answers, AI CTO MUST:

1. **Create Project Brief File**
   - Filename: `PROJECT_BRIEF_[ProjectName]_[Date].md`
   - Location: Project root or `.cursor/brain/` directory
   - Contents:
     - Complete Q&A session transcript
     - Project vision and goals
     - Technical requirements
     - Feature list
     - Security and compliance requirements
     - All strategic decisions made

2. **Conduct Competitor Analysis**
   - Research 3-5 main competitors or similar solutions
   - Document for each:
     - Name, website, and overview
     - Key features and capabilities
     - Pricing model
     - Strengths and weaknesses
     - Market positioning
     - **Our differentiation strategy**
   - Add to project brief under "Competitor Analysis" section

3. **Provide Strategic Recommendations**
   - Unique features to differentiate
   - Market positioning strategies
   - Monetization approaches
   - Technology advantages
   - Security features as selling points
   - Compliance certifications for market access
   - Add to project brief under "Strategic Recommendations" section

**Exit Criteria (Gate 1):**
- [ ] All 10 questions answered (or explicitly marked N/A)
- [ ] Project type identified (see Section 15)
- [ ] Scale tier determined
- [ ] Compliance requirements listed
- [ ] Security classification assigned (Critical / High / Medium / Low)
- [ ] **Project Brief file created with all Q&A documented**
- [ ] **Competitor analysis completed (3-5 competitors minimum)**
- [ ] **Strategic recommendations provided**

---

#### Phase 2: DESIGN (Requirements → Architecture)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI CTO + AI Architect |
| **Input** | Project Brief from Phase 1 |
| **Activities** | Tech stack selection (Section 4), system architecture design, API contract design, database schema design, threat modeling |
| **Output** | Technical Design Document (TRD) |
| **SecureSDLC Link** | Phase 3 (Secure TRD) + Phase 4 (Security Review) |

**Exit Criteria (Gate 2):**
- [ ] Tech stack selected with reasoning documented
- [ ] System architecture diagram created
- [ ] API contracts defined (endpoints, request/response schemas)
- [ ] Database schema designed with security annotations
- [ ] STRIDE threat model completed
- [ ] Security review passed (AI Security Officer approved)
- [ ] Human approved architecture (for Critical/High security projects)

---

#### Phase 3: DECIDE (Architecture → Contracts)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI CTO + AI Security Officer |
| **Input** | TRD from Phase 2 |
| **Activities** | Define coding contracts, establish file ownership, set forbidden patterns, create dependency allowlist, define test requirements |
| **Output** | Coding Contract Document |
| **SecureSDLC Link** | Section 1 (Security Principles) |

**Exit Criteria (Gate 3):**
- [ ] Coding contracts defined (Section 5)
- [ ] File ownership map created
- [ ] Forbidden patterns list created
- [ ] Approved dependency list created
- [ ] Minimum test coverage threshold set
- [ ] CI/CD pipeline design approved

---

#### Phase 4: SCAFFOLD (Contracts → Project Structure)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI DevOps + AI Architect |
| **Input** | Contracts from Phase 3 |
| **Activities** | Generate project structure, create config files, set up CI/CD, create Dockerfiles, set up IaC, configure linters/formatters, create .env templates |
| **Output** | Empty but fully configured project |
| **SecureSDLC Link** | Phase 5 (Secure Implementation - Structure) |

**Exit Criteria (Gate 4):**
- [ ] Project directory structure created
- [ ] All config files generated (Docker, CI/CD, linters, formatters)
- [ ] Security configs in place (headers, CORS, CSP)
- [ ] .env.example with all required variables
- [ ] README.md with setup instructions
- [ ] Git repository initialized with .gitignore
- [ ] CI/CD pipeline runs successfully (empty project builds)
- [ ] Security scan passes on scaffolded project

---

#### Phase 5: BUILD (Structure → Working Code)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI Executor (Cursor/Claude/Antigravity) |
| **Input** | Scaffolded project from Phase 4 |
| **Activities** | Implement features one by one, write unit tests for each feature, follow coding contracts strictly, run linter after each file, commit after each feature |
| **Output** | Working application code with tests |
| **SecureSDLC Link** | Phase 5 (Secure Implementation - Code) |

**Build Order (MUST follow this sequence):**
```
1. Database models/migrations
2. Core utilities (logging, error handling, validation)
3. Authentication & authorization
4. Core business logic (service layer)
5. API endpoints/routes
6. Middleware (rate limiting, security headers, CORS)
7. Background jobs (if needed)
8. Frontend components (if applicable)
9. Integration between layers
10. API documentation generation
```

**Exit Criteria (Gate 5):**
- [ ] All features implemented per TRD specification
- [ ] Unit tests written (minimum coverage: 80%)
- [ ] All tests pass
- [ ] Linter passes with zero errors
- [ ] No hardcoded secrets
- [ ] No TODO/FIXME left unresolved
- [ ] Code follows coding contracts
- [ ] Each feature committed separately with descriptive messages

---

#### Phase 6: VALIDATE (Code → Verified Code)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI Security Officer + AI QA |
| **Input** | Working code from Phase 5 |
| **Activities** | Security scanning (SAST/DAST), integration testing, performance testing, security testing, compliance checking, code review |
| **Output** | Validation Report |
| **SecureSDLC Link** | Phase 6 (Security Testing) |

**Exit Criteria (Gate 6):**
- [ ] SAST scan: zero critical/high findings
- [ ] Dependency scan: zero known vulnerabilities (critical/high)
- [ ] Secret scan: zero secrets detected
- [ ] Lint/format checks pass (no ignored errors)
- [ ] Type checks pass (tsc/mypy/go vet/etc.)
- [ ] Unit test coverage meets threshold (default: 80%+)
- [ ] Accessibility checks pass (WCAG 2.1 AA / platform a11y)
- [ ] Responsive/UI checks pass (no layout breaks at key breakpoints)
- [ ] Observability wired (structured logs + metrics + traces + alerts)
- [ ] Integration tests pass
- [ ] Security tests pass (OWASP Top 10 coverage)
- [ ] Performance baseline established
- [ ] Compliance checklist passed
- [ ] AI Security Officer signs off

---

#### Phase 7: DEPLOY (Verified Code → Running System)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI DevOps + Human Approval |
| **Input** | Validated code from Phase 6 |
| **Activities** | Build production image, deploy to staging, run smoke tests, deploy to production (after human approval), configure monitoring, set up alerts |
| **Output** | Running production system |
| **SecureSDLC Link** | Phase 7 (Secure Deployment) |

**Exit Criteria (Gate 7):**
- [ ] Staging deployment successful
- [ ] Smoke tests pass on staging
- [ ] Human approves production deployment (Critical/High projects)
- [ ] Production deployment successful
- [ ] Health checks passing
- [ ] Monitoring dashboards active
- [ ] Alerting configured
- [ ] Rollback plan documented and tested

---

#### Phase 8: OPERATE (Running System → Maintained System)

| Attribute | Value |
|-----------|-------|
| **AI Role** | AI DevOps + AI Security Officer |
| **Input** | Running system from Phase 7 |
| **Activities** | Monitor health, respond to alerts, rotate secrets, patch vulnerabilities, scale resources, incident response |
| **Output** | Continuous system health |
| **SecureSDLC Link** | Phase 7 (Operations) |

**Ongoing Criteria:**
- [ ] Uptime meets SLA (99.9%+)
- [ ] Security patches applied within SLA
- [ ] Secrets rotated on schedule
- [ ] Dependency updates reviewed weekly
- [ ] Security scans run daily
- [ ] Backup verification monthly
- [ ] Incident response drills quarterly

---

## 4. Deterministic Tech Stack Selection Engine

### 4.1 Purpose

AI must NEVER guess which technology to use. This section provides **rule-based decision trees** that deterministically select the optimal, secure tech stack based on project parameters.

### 4.2 How It Works

```
Project Parameters (from Phase 1)
         ↓
    Selection Rules (this section)
         ↓
    Recommended Stack (with reasoning)
         ↓
    Human Approval (optional for low-risk)
         ↓
    Locked Stack (no changes without re-evaluation)
```

### 4.3 Backend Language & Framework Selection

```yaml
backend_selection:
  
  # Rule 1: High-performance, high-concurrency systems
  when:
    concurrent_users: ">10,000"
    latency_requirement: "<50ms"
    OR:
      project_type: "real-time"
      project_type: "high-frequency-trading"
      project_type: "game-server"
  then:
    preferred:
      language: "Go"
      framework: "Gin or Echo"
      reasoning: "Goroutines handle massive concurrency natively. Type-safe. Minimal memory footprint."
    alternative:
      language: "Rust"
      framework: "Actix-web or Axum"
      reasoning: "When zero-cost abstractions and memory safety are paramount."

  # Rule 2: Rapid development, startup MVP, data-heavy APIs
  when:
    timeline: "< 3 months"
    team_size: "< 5"
    OR:
      project_type: "web-api"
      project_type: "saas"
      project_type: "data-pipeline"
      project_type: "ml-service"
  then:
    preferred:
      language: "Python"
      framework: "FastAPI"
      reasoning: "Async by default. Auto-generates OpenAPI docs. Pydantic validation. Fastest Python framework."
    alternative:
      language: "Python"
      framework: "Django + DRF"
      reasoning: "When you need built-in admin panel, ORM, and batteries-included approach."

  # Rule 3: Enterprise, large team, microservices
  when:
    team_size: ">10"
    OR:
      compliance: "SOC2"
      compliance: "HIPAA"
      project_type: "enterprise"
      project_type: "banking"
      project_type: "healthcare"
  then:
    preferred:
      language: "Java"
      framework: "Spring Boot"
      reasoning: "Enterprise-proven. Massive ecosystem. Strong typing. Built-in security (Spring Security)."
    alternative:
      language: "C#"
      framework: ".NET 8"
      reasoning: "When team has .NET expertise or Azure is the primary cloud."

  # Rule 4: Full-stack JavaScript, real-time features
  when:
    frontend_and_backend: true
    OR:
      project_type: "real-time-chat"
      project_type: "collaborative-tool"
      team_preference: "javascript"
  then:
    preferred:
      language: "TypeScript"
      framework: "NestJS"
      reasoning: "Type-safe Node.js. Decorator-based. Built-in modules for auth, validation, WebSocket."
    alternative:
      language: "TypeScript"
      framework: "Express + tRPC"
      reasoning: "Lighter weight. When NestJS overhead is not needed."

  # Rule 5: Serverless / Edge / Lambda
  when:
    deployment: "serverless"
    OR:
      project_type: "webhook-handler"
      project_type: "edge-function"
      budget: "minimal"
  then:
    preferred:
      language: "TypeScript"
      framework: "Hono"
      reasoning: "Ultra-lightweight. Works on Cloudflare Workers, Deno Deploy, AWS Lambda."
    alternative:
      language: "Go"
      framework: "Standard library"
      reasoning: "Fastest cold starts. Minimal binary size."

  # Rule 6: CLI tools, system utilities, DevOps tools
  when:
    OR:
      project_type: "cli-tool"
      project_type: "system-utility"
      project_type: "devops-tool"
  then:
    preferred:
      language: "Go"
      framework: "Cobra + Viper"
      reasoning: "Single binary distribution. Cross-platform. Industry standard for CLI tools."
    alternative:
      language: "Rust"
      framework: "Clap"
      reasoning: "When performance is critical and zero dependencies needed."

  # Default fallback
  default:
    language: "Python"
    framework: "FastAPI"
    reasoning: "Widest AI training data. Best AI code generation quality. Secure defaults."
```

### 4.4 Frontend Framework Selection

```yaml
frontend_selection:

  # Rule 1: SEO-critical, content-heavy, marketing sites
  when:
    OR:
      seo_required: true
      project_type: "e-commerce"
      project_type: "blog"
      project_type: "marketing-site"
      project_type: "saas-landing"
  then:
    preferred:
      framework: "Next.js (App Router)"
      language: "TypeScript"
      reasoning: "SSR/SSG. Best SEO. React ecosystem. Middleware for security headers."
    alternative:
      framework: "Nuxt 3"
      language: "TypeScript"
      reasoning: "When team prefers Vue over React."

  # Rule 2: Complex SPAs, dashboards, admin panels
  when:
    OR:
      project_type: "dashboard"
      project_type: "admin-panel"
      project_type: "internal-tool"
      project_type: "crm"
  then:
    preferred:
      framework: "React + Vite"
      language: "TypeScript"
      reasoning: "Rich component ecosystem. Best for complex interactive UIs."
    alternative:
      framework: "Vue 3 + Vite"
      language: "TypeScript"
      reasoning: "Simpler learning curve. When team is smaller."

  # Rule 3: Lightweight, minimal JS, progressive enhancement
  when:
    OR:
      performance_critical: true
      bundle_size: "< 50kb"
      project_type: "embedded-widget"
  then:
    preferred:
      framework: "SvelteKit"
      language: "TypeScript"
      reasoning: "Smallest bundle size. No virtual DOM overhead. Compiled output."
    alternative:
      framework: "Astro"
      language: "TypeScript"
      reasoning: "When content-first with islands of interactivity."

  # Rule 4: Mobile-first or cross-platform
  when:
    OR:
      mobile_required: true
      project_type: "mobile-app"
      project_type: "cross-platform"
  then:
    preferred:
      framework: "React Native + Expo"
      language: "TypeScript"
      reasoning: "Largest community. Code sharing with web. OTA updates."
    alternative:
      framework: "Flutter"
      language: "Dart"
      reasoning: "When pixel-perfect UI and performance are more important than ecosystem."

  # Rule 5: Desktop applications
  when:
    OR:
      project_type: "desktop-app"
      project_type: "electron-app"
  then:
    preferred:
      framework: "Tauri + React/Svelte"
      language: "TypeScript + Rust"
      reasoning: "10x smaller than Electron. Secure by design. Native performance."
    alternative:
      framework: "Electron + React"
      language: "TypeScript"
      reasoning: "When web compatibility and quick development are priority."

  # Default fallback
  default:
    framework: "Next.js (App Router)"
    language: "TypeScript"
    reasoning: "Most versatile. Best AI code generation support. Security middleware built-in."
```

### 4.5 Database Selection

```yaml
database_selection:

  # Rule 1: Relational data, PII, financial, compliance-required
  when:
    OR:
      data_type: "relational"
      has_pii: true
      compliance: ["GDPR", "HIPAA", "PCI-DSS", "SOC2"]
      project_type: ["banking", "healthcare", "e-commerce", "enterprise"]
  then:
    preferred:
      engine: "PostgreSQL"
      version: "16+"
      reasoning: "Row-level security. Field-level encryption. ACID compliance. JSON support. Extensions ecosystem."
      security_features:
        - "Row-Level Security (RLS)"
        - "pgcrypto for field encryption"
        - "SSL/TLS connections"
        - "Audit triggers"
        - "pg_audit extension"
    alternative:
      engine: "MySQL 8+"
      reasoning: "When team has MySQL expertise. InnoDB encryption."

  # Rule 2: Document-oriented, flexible schema, rapid iteration
  when:
    OR:
      data_type: "document"
      schema_flexibility: "high"
      project_type: ["cms", "catalog", "iot-data"]
  then:
    preferred:
      engine: "MongoDB 7+"
      reasoning: "Flexible schema. Client-Side Field Level Encryption (CSFLE). Queryable encryption."
      security_features:
        - "Client-Side Field Level Encryption"
        - "Queryable Encryption"
        - "Role-based access control"
        - "Audit logging"
    alternative:
      engine: "PostgreSQL + JSONB"
      reasoning: "When you need relational + document flexibility in one DB."

  # Rule 3: Caching, sessions, real-time
  when:
    OR:
      use_case: "cache"
      use_case: "session-store"
      use_case: "rate-limiting"
      use_case: "real-time-leaderboard"
  then:
    preferred:
      engine: "Redis 7+"
      reasoning: "In-memory speed. ACLs. TLS. Persistence options."
      security_features:
        - "ACL-based access control"
        - "TLS encryption"
        - "Password authentication"
        - "Command renaming/disabling"
    alternative:
      engine: "Valkey"
      reasoning: "Open-source Redis fork. When licensing is a concern."

  # Rule 4: Search functionality
  when:
    OR:
      use_case: "full-text-search"
      use_case: "log-aggregation"
      use_case: "analytics"
  then:
    preferred:
      engine: "Elasticsearch 8+ or OpenSearch"
      reasoning: "Powerful full-text search. Field-level security. Audit logging."
    alternative:
      engine: "Meilisearch or Typesense"
      reasoning: "Simpler setup. When advanced search features aren't needed."

  # Rule 5: Time-series data
  when:
    OR:
      data_type: "time-series"
      project_type: ["monitoring", "iot", "financial-data"]
  then:
    preferred:
      engine: "TimescaleDB (PostgreSQL extension)"
      reasoning: "SQL interface. Compression. Continuous aggregates. Inherits PG security."
    alternative:
      engine: "InfluxDB"
      reasoning: "Purpose-built. When pure time-series without relational needs."

  # Rule 6: Graph data
  when:
    OR:
      data_type: "graph"
      project_type: ["social-network", "recommendation-engine", "knowledge-graph"]
  then:
    preferred:
      engine: "Neo4j"
      reasoning: "Native graph storage. Role-based access. Encryption at rest."
    alternative:
      engine: "PostgreSQL + Apache AGE"
      reasoning: "When you need graph queries but can't add another DB to the stack."

  # Rule 7: Message queue / event streaming
  when:
    OR:
      use_case: "event-streaming"
      use_case: "message-queue"
      project_type: "microservices"
  then:
    preferred:
      engine: "Apache Kafka"
      reasoning: "Industry standard. TLS. SASL authentication. ACLs."
    alternative:
      engine: "RabbitMQ"
      reasoning: "When simpler pub/sub is sufficient. When message ordering per-queue is enough."
    lightweight:
      engine: "Redis Streams"
      reasoning: "When you already have Redis and don't need Kafka's scale."
```

### 4.6 Authentication Strategy Selection

```yaml
auth_selection:

  # Rule 1: Simple web app, MVP, startup
  when:
    scale: "<10,000 users"
    budget: "minimal"
    NOT:
      compliance: ["SOC2", "HIPAA"]
  then:
    strategy: "JWT + bcrypt"
    implementation:
      tokens: "Access (15min) + Refresh (7 days)"
      hashing: "bcrypt cost 12"
      storage: "HttpOnly secure cookies"
      mfa: "Optional TOTP"
    libraries:
      python: "python-jose + passlib[bcrypt]"
      nodejs: "jsonwebtoken + bcrypt"
      go: "golang-jwt + golang.org/x/crypto/bcrypt"
      java: "Spring Security + jjwt"

  # Rule 2: Enterprise, SSO required
  when:
    OR:
      project_type: "enterprise"
      sso_required: true
      compliance: "SOC2"
  then:
    strategy: "OAuth 2.0 + OIDC + SAML"
    implementation:
      provider: "Keycloak (self-hosted) or Auth0 (managed)"
      protocols: "OIDC for web, SAML for enterprise"
      mfa: "Required for all users"
    reasoning: "Enterprise SSO. Centralized identity. Compliance-ready."

  # Rule 3: Consumer app, social login
  when:
    OR:
      social_login: true
      project_type: ["consumer-app", "mobile-app"]
  then:
    strategy: "OAuth 2.0 social providers + local auth"
    implementation:
      providers: "Google, GitHub, Apple (minimum)"
      local: "Email/password as fallback"
      session: "JWT or server-side sessions"
    libraries:
      nextjs: "NextAuth.js (Auth.js)"
      python: "authlib + social-auth-app-django"

  # Rule 4: API-only, machine-to-machine
  when:
    OR:
      project_type: "api-service"
      project_type: "microservice"
      consumers: "machines"
  then:
    strategy: "API keys + OAuth 2.0 client credentials"
    implementation:
      api_keys: "Scoped, rotatable, rate-limited"
      oauth: "Client credentials grant for service-to-service"
      signing: "HMAC-SHA256 for webhooks"

  # Rule 5: Zero-trust, high-security
  when:
    OR:
      security_level: "critical"
      compliance: ["HIPAA", "PCI-DSS"]
      project_type: ["banking", "healthcare"]
  then:
    strategy: "mTLS + OAuth 2.0 + MFA mandatory"
    implementation:
      service_auth: "Mutual TLS certificates"
      user_auth: "OAuth 2.0 + PKCE"
      mfa: "Hardware key (FIDO2/WebAuthn) preferred"
      session: "Server-side, 15-minute timeout"
      audit: "Every auth event logged"
```

### 4.7 Cloud Provider Selection

```yaml
cloud_selection:

  # Rule 1: Default / Most services / Best AI integration
  when:
    OR:
      no_preference: true
      project_type: "general"
      needs: ["widest-service-catalog", "ml-services"]
  then:
    preferred:
      provider: "AWS"
      reasoning: "Widest service catalog. Best IaC support. Most documentation."
      key_services:
        compute: "ECS Fargate or EKS"
        database: "RDS PostgreSQL"
        cache: "ElastiCache Redis"
        secrets: "AWS Secrets Manager"
        cdn: "CloudFront"
        waf: "AWS WAF"
        monitoring: "CloudWatch + X-Ray"

  # Rule 2: Google/Firebase ecosystem, ML-heavy, Kubernetes-native
  when:
    OR:
      preference: "google"
      project_type: "ml-heavy"
      kubernetes_native: true
  then:
    preferred:
      provider: "GCP"
      reasoning: "Best Kubernetes (GKE). Best ML platform. Global network."
      key_services:
        compute: "GKE or Cloud Run"
        database: "Cloud SQL PostgreSQL"
        cache: "Memorystore Redis"
        secrets: "Secret Manager"
        cdn: "Cloud CDN"
        waf: "Cloud Armor"
        monitoring: "Cloud Monitoring + Trace"

  # Rule 3: Microsoft ecosystem, enterprise, hybrid cloud
  when:
    OR:
      preference: "microsoft"
      existing_infra: "azure"
      hybrid_cloud: true
      active_directory: true
  then:
    preferred:
      provider: "Azure"
      reasoning: "Best hybrid cloud. AD integration. Enterprise agreements."
      key_services:
        compute: "AKS or Container Apps"
        database: "Azure Database for PostgreSQL"
        cache: "Azure Cache for Redis"
        secrets: "Azure Key Vault"
        cdn: "Azure CDN"
        waf: "Azure WAF"
        monitoring: "Azure Monitor + Application Insights"

  # Rule 4: Budget-conscious, simple deployment
  when:
    OR:
      budget: "minimal"
      scale: "<1000 users"
      project_type: "side-project"
  then:
    preferred:
      provider: "Railway / Render / Fly.io"
      reasoning: "Simplest deployment. Free tiers. No DevOps needed."
    alternative:
      provider: "DigitalOcean"
      reasoning: "Affordable VPS. Simple managed databases."

  # Rule 5: Privacy-first, EU data residency
  when:
    OR:
      compliance: "GDPR"
      data_residency: "EU"
      privacy_first: true
  then:
    preferred:
      provider: "AWS eu-west-1 / eu-central-1"
      reasoning: "EU data residency. GDPR compliance tools."
    alternative:
      provider: "Hetzner (Germany)"
      reasoning: "EU-based. GDPR by default. Cost-effective."
```

### 4.8 Stack Lock Protocol

Once a tech stack is selected:

```
1. DOCUMENT the complete stack with reasoning
2. LOCK the stack — no changes without re-evaluation
3. RE-EVALUATION requires:
   a. A clear problem with the current choice
   b. AI CTO approval
   c. Impact analysis on existing code
   d. Human approval for major changes
4. NEVER change stack mid-build because AI "prefers" something else
```

### 4.9 Scaling Strategy Rules

AI MUST select the correct scale tier at design time (Phase 2) based on the expected load from Phase 1 discovery. These rules also define when to upgrade and when to switch technologies entirely.

#### 4.9.1 Redis Scaling Tiers

```yaml
redis_scaling:

  tier_1_starter:
    when:
      queries_per_second: "<10,000"
      data_size: "<1 GB"
      use_case: ["cache", "session-store", "rate-limiting"]
    setup:
      instances: "Single Redis 7+ instance"
      persistence: "AOF (appendonly) for durability"
      memory: "2-4 GB"
      replication: "None"
    cost: "~$15-25/month (managed)"

  tier_2_growth:
    when:
      queries_per_second: "10,000 - 100,000"
      data_size: "1 - 10 GB"
      availability: "High (99.9%+)"
    setup:
      instances: "Primary + 1-2 read replicas"
      persistence: "AOF + RDB snapshots"
      memory: "8-16 GB"
      replication: "Async replication to replicas"
      read_strategy: "Read from replicas, write to primary"
    cost: "~$50-150/month (managed)"

  tier_3_scale:
    when:
      queries_per_second: "100,000 - 1,000,000"
      data_size: "10 - 100 GB"
      availability: "Very High (99.99%)"
    setup:
      instances: "Redis Cluster (6+ nodes: 3 primary + 3 replicas)"
      sharding: "Automatic hash-slot sharding (16384 slots)"
      memory: "16-64 GB per node"
      replication: "Each primary has a replica for failover"
      connection: "Smart client with cluster-aware routing"
    cost: "~$300-1000/month (managed)"

  tier_4_massive:
    when:
      queries_per_second: ">1,000,000"
      data_size: ">100 GB"
    setup:
      instances: "Redis Cluster (12+ nodes) + application-level local cache"
      local_cache: "In-process LRU cache (e.g., cachetools in Python, node-cache in Node.js)"
      strategy: "Check local cache → Redis → Database"
      ttl_local: "30-60 seconds (short, to avoid stale data)"
      ttl_redis: "5-30 minutes (medium)"
    cost: "~$1000-5000/month (managed)"

  when_redis_is_wrong:
    # Switch AWAY from Redis when:
    - scenario: "Data exceeds available RAM and cannot be sharded"
      switch_to: "PostgreSQL with application-level caching"
      reasoning: "Redis is in-memory only. If data doesn't fit in RAM, it evicts or crashes."

    - scenario: "Need complex queries (JOIN, aggregation, full-text search) on cached data"
      switch_to: "Elasticsearch or PostgreSQL"
      reasoning: "Redis supports limited data structures. Complex queries need a query engine."

    - scenario: "Need durable, ordered, replayable message streaming"
      switch_to: "Apache Kafka"
      reasoning: "Redis Streams is good for lightweight pub/sub but lacks Kafka's durability, consumer groups at scale, and log compaction."

    - scenario: "Need persistent job queue with complex scheduling"
      switch_to: "Celery + RabbitMQ (Python) or BullMQ + Redis (Node.js)"
      reasoning: "Redis alone doesn't handle delayed jobs, retries, or priority queues well without a library on top."

    - scenario: "Multi-region deployment with strong consistency requirement"
      switch_to: "CockroachDB or Spanner for data, Redis only for local-region cache"
      reasoning: "Redis replication is async. Cross-region consistency requires a distributed database."
```

#### 4.9.2 PostgreSQL Scaling Tiers

```yaml
postgresql_scaling:

  tier_1_starter:
    when:
      concurrent_connections: "<100"
      data_size: "<10 GB"
      queries_per_second: "<500"
    setup:
      instance: "Single PostgreSQL 16+ instance"
      specs: "2 vCPU, 4-8 GB RAM"
      connection_pool: "PgBouncer (max 20 connections to DB)"
      backup: "Daily automated snapshots"
    cost: "~$15-50/month (managed)"

  tier_2_growth:
    when:
      concurrent_connections: "100 - 1,000"
      data_size: "10 - 100 GB"
      queries_per_second: "500 - 5,000"
    setup:
      instance: "Primary + 1-2 read replicas"
      specs: "4-8 vCPU, 16-32 GB RAM"
      connection_pool: "PgBouncer (max 100 connections to DB)"
      read_strategy: "Read replicas for reporting/analytics queries"
      backup: "Point-in-time recovery (PITR)"
      caching: "Redis for frequently read data"
    cost: "~$100-400/month (managed)"

  tier_3_scale:
    when:
      concurrent_connections: "1,000 - 10,000"
      data_size: "100 GB - 1 TB"
      queries_per_second: "5,000 - 50,000"
    setup:
      instance: "Primary + 3-5 read replicas"
      specs: "16-32 vCPU, 64-128 GB RAM"
      connection_pool: "PgBouncer (transaction-level pooling)"
      partitioning: "Table partitioning by date/tenant"
      read_strategy: "Route read traffic to replicas"
      caching: "Redis for hot data + query result caching"
      indexing: "Partial indexes, covering indexes, BRIN indexes for large tables"
    cost: "~$500-2000/month (managed)"

  tier_4_massive:
    when:
      concurrent_connections: ">10,000"
      data_size: ">1 TB"
      queries_per_second: ">50,000"
    setup:
      primary: "High-spec primary (32+ vCPU, 256 GB RAM)"
      replicas: "5-10 read replicas across regions"
      sharding: "Application-level sharding (by tenant_id or region)"
      alternative: "Citus (PostgreSQL extension for horizontal sharding)"
      connection: "PgBouncer pools per shard"
      caching: "Multi-layer: local cache → Redis → PostgreSQL"
      archival: "Move old data to cold storage (S3 + Athena for queries)"
    cost: "~$2000-10000/month (managed)"

  when_postgresql_is_wrong:
    - scenario: "Need sub-millisecond reads at >100K queries/sec"
      switch_to: "Redis for hot data, PostgreSQL as source of truth"

    - scenario: "Highly flexible, schema-less document data"
      switch_to: "MongoDB (or PostgreSQL JSONB if schema is semi-structured)"

    - scenario: "Need full-text search with ranking, faceting, autocomplete"
      switch_to: "Elasticsearch/OpenSearch (keep PostgreSQL as primary, sync to ES)"

    - scenario: "Globally distributed with strong consistency"
      switch_to: "CockroachDB or Google Spanner"

    - scenario: "Time-series data at massive scale (billions of rows)"
      switch_to: "TimescaleDB (PostgreSQL extension) or InfluxDB"
```

#### 4.9.3 Application Server Scaling Tiers

```yaml
app_server_scaling:

  tier_1_starter:
    when:
      concurrent_users: "<1,000"
      requests_per_second: "<100"
    setup:
      instances: "1 container/server"
      specs: "1-2 vCPU, 1-2 GB RAM"
      deployment: "Docker Compose or single PaaS (Railway/Render)"

  tier_2_growth:
    when:
      concurrent_users: "1,000 - 10,000"
      requests_per_second: "100 - 1,000"
    setup:
      instances: "2-4 containers behind a load balancer"
      specs: "2 vCPU, 2-4 GB RAM each"
      deployment: "ECS Fargate / Cloud Run / K8s (small cluster)"
      auto_scaling: "Scale on CPU > 70% or request count"
      session: "Externalized to Redis (not in-memory)"

  tier_3_scale:
    when:
      concurrent_users: "10,000 - 100,000"
      requests_per_second: "1,000 - 10,000"
    setup:
      instances: "4-20 containers with auto-scaling"
      specs: "4 vCPU, 4-8 GB RAM each"
      deployment: "Kubernetes with HPA (Horizontal Pod Autoscaler)"
      auto_scaling: "Scale on CPU, memory, custom metrics (queue depth, latency)"
      cdn: "CloudFront/Cloudflare for static assets"
      rate_limiting: "At API gateway level"

  tier_4_massive:
    when:
      concurrent_users: ">100,000"
      requests_per_second: ">10,000"
    setup:
      instances: "20-100+ containers across multiple regions"
      specs: "8 vCPU, 8-16 GB RAM each"
      deployment: "Multi-region Kubernetes"
      auto_scaling: "KEDA (event-driven) + HPA"
      cdn: "Global CDN with edge caching"
      api_gateway: "Kong / AWS API Gateway with caching"
      strategy: "Microservices (split monolith if not already)"
      queue: "Kafka for async processing"

  language_specific_limits:
    # When to switch languages for performance
    python_fastapi:
      comfortable: "<5,000 req/sec per instance"
      max_practical: "~10,000 req/sec per instance (with uvicorn workers)"
      if_exceeded: "Scale horizontally (more instances) or consider Go for hot paths"

    nodejs_nestjs:
      comfortable: "<8,000 req/sec per instance"
      max_practical: "~15,000 req/sec per instance"
      if_exceeded: "Scale horizontally or use worker threads for CPU-bound tasks"

    go_gin:
      comfortable: "<50,000 req/sec per instance"
      max_practical: "~100,000 req/sec per instance"
      if_exceeded: "Scale horizontally. Go rarely needs language switching."

    java_spring:
      comfortable: "<10,000 req/sec per instance"
      max_practical: "~20,000 req/sec per instance (with virtual threads in Java 21+)"
      if_exceeded: "Scale horizontally. Consider GraalVM native image for faster startup."
```

#### 4.9.4 Monitoring Thresholds That Trigger Scaling

```yaml
scaling_triggers:
  # These alerts indicate it's time to scale UP

  redis:
    - metric: "Memory usage > 80%"
      action: "Upgrade instance size or add shards"
      urgency: "HIGH — evictions will start soon"
    
    - metric: "CPU > 70% sustained for 10 minutes"
      action: "Add read replicas or switch to Cluster mode"
      urgency: "MEDIUM"
    
    - metric: "Connected clients > 80% of maxclients"
      action: "Increase maxclients or add connection pooling"
      urgency: "HIGH"
    
    - metric: "Evictions > 0 (keys being removed due to memory pressure)"
      action: "IMMEDIATELY increase memory or optimize TTLs"
      urgency: "CRITICAL — data loss is occurring"
    
    - metric: "Replication lag > 1 second"
      action: "Check network, upgrade replica, or reduce write load"
      urgency: "HIGH"

  postgresql:
    - metric: "Active connections > 80% of max_connections"
      action: "Add PgBouncer or increase max_connections"
      urgency: "HIGH"
    
    - metric: "Average query time > 500ms"
      action: "Analyze slow queries (pg_stat_statements), add indexes"
      urgency: "MEDIUM"
    
    - metric: "Disk usage > 80%"
      action: "Increase storage, archive old data, add partitioning"
      urgency: "HIGH"
    
    - metric: "Replication lag > 5 seconds"
      action: "Upgrade replica specs or reduce write load"
      urgency: "HIGH"
    
    - metric: "Lock wait time > 1 second average"
      action: "Optimize transactions, review locking patterns"
      urgency: "MEDIUM"
    
    - metric: "Cache hit ratio < 95%"
      action: "Increase shared_buffers or add Redis caching layer"
      urgency: "MEDIUM"

  application:
    - metric: "Response time p95 > 2 seconds"
      action: "Scale horizontally or optimize slow endpoints"
      urgency: "HIGH"
    
    - metric: "CPU > 80% sustained for 5 minutes"
      action: "Auto-scale (add instances)"
      urgency: "HIGH — auto-scaling should handle this"
    
    - metric: "Memory > 85%"
      action: "Check for memory leaks, scale up, or scale out"
      urgency: "HIGH"
    
    - metric: "5xx error rate > 1%"
      action: "Investigate errors, scale if resource-related"
      urgency: "CRITICAL"
    
    - metric: "Request queue depth > 100"
      action: "Add instances, the server cannot keep up"
      urgency: "HIGH"

  # These alerts indicate you might be OVER-provisioned (save money)
  scale_down:
    - metric: "CPU < 20% sustained for 1 hour"
      action: "Consider scaling down (fewer/smaller instances)"
    
    - metric: "Memory < 30% sustained for 1 hour"
      action: "Consider smaller instance size"
    
    - metric: "Redis memory < 20%"
      action: "Consider smaller Redis instance"
```

#### 4.9.5 Multi-Layer Caching Strategy

```yaml
caching_strategy:
  # AI MUST implement the appropriate caching layers based on scale tier

  tier_1:  # Small projects
    layers:
      - "Redis (single layer cache for sessions, rate limits, hot data)"
    pattern: "Cache-aside (lazy loading)"
    # App checks Redis → if miss → query DB → store in Redis → return

  tier_2:  # Medium projects
    layers:
      - "Redis (primary cache)"
      - "HTTP cache headers (browser + CDN caching for static content)"
    pattern: "Cache-aside + Write-through for critical data"
    # Reads: App → Redis → DB
    # Writes: App → DB → Redis (update cache)

  tier_3:  # Large projects
    layers:
      - "CDN edge cache (static assets, API responses with Cache-Control)"
      - "API Gateway cache (frequent identical requests)"
      - "Redis (application data cache)"
      - "Database query cache (materialized views for complex queries)"
    pattern: "Multi-layer with TTL hierarchy"
    # CDN: 1 hour TTL
    # API Gateway: 5 min TTL
    # Redis: 15 min TTL
    # DB materialized view: refresh every 30 min

  tier_4:  # Massive projects
    layers:
      - "CDN edge cache (global)"
      - "API Gateway cache (regional)"
      - "Local in-process cache (per instance, 30-60 sec TTL)"
      - "Redis Cluster (shared cache)"
      - "Database read replicas"
      - "Cold storage (S3) for archival data"
    pattern: "Request → Local cache → Redis → Read replica → Primary DB → Cold storage"

  cache_invalidation:
    strategies:
      - name: "TTL-based"
        description: "Cache expires after set time. Simplest, eventual consistency."
        use_when: "Data can be slightly stale (product catalog, user profiles)"
      
      - name: "Event-based"
        description: "Invalidate cache when data changes (pub/sub or DB trigger)"
        use_when: "Data must be fresh (inventory count, account balance)"
      
      - name: "Version-based"
        description: "Cache key includes version number, increment on change"
        use_when: "Need atomic cache updates (config, feature flags)"

    rules:
      - "NEVER cache authentication tokens or session data without TTL"
      - "NEVER cache PII without encryption"
      - "ALWAYS have a manual cache-clear mechanism for emergencies"
      - "ALWAYS log cache hit/miss ratio for monitoring"
      - "ALWAYS set a maximum TTL — no infinite caching"
```

#### 4.9.6 Scaling Decision Flowchart

```
USER REPORTS: "App is slow" or monitoring alert fires
                    │
                    ▼
         ┌─────────────────────┐
         │ Check: Where is the │
         │ bottleneck?         │
         └────────┬────────────┘
                  │
    ┌─────────────┼──────────────┬──────────────────┐
    ▼             ▼              ▼                  ▼
 APP SERVER    DATABASE       REDIS             NETWORK
    │             │              │                  │
    ▼             ▼              ▼                  ▼
 CPU>80%?    Slow queries?   Memory>80%?      Latency high?
    │             │              │                  │
   YES           YES            YES                YES
    │             │              │                  │
    ▼             ▼              ▼                  ▼
 Add more     Add indexes    Upgrade size      Add CDN /
 instances    or read        or add cluster     move closer
              replicas       shards             to users
    │             │              │                  │
    ▼             ▼              ▼                  ▼
 Still slow?  Still slow?   Still slow?       Still slow?
    │             │              │                  │
   YES           YES            YES                YES
    │             │              │                  │
    ▼             ▼              ▼                  ▼
 Profile &    Add Redis      Re-evaluate       Multi-region
 optimize     caching        if Redis is        deployment
 code         layer          right tool
    │             │              │
    ▼             ▼              ▼
 Consider     Partition      Switch to
 faster       tables or      Kafka (streaming)
 language     shard DB       or PostgreSQL
 for hot                     (if data too big
 paths                       for RAM)
```

---

## 5. AI Coding Contracts & Guardrails

### 5.1 Purpose

Coding contracts prevent AI hallucination, scope creep, and insecure code generation. Every AI executor agent MUST follow these contracts. Violations trigger automatic rejection and re-generation.

### 5.2 Universal Contract (Applies to ALL Projects)

```markdown
## UNIVERSAL AI CODING CONTRACT

### Section A: YOU MUST

A1. Write production-quality code — no placeholders, no TODOs, no "implement later".
A2. Write unit tests for every public function/method (minimum 80% coverage).
A3. Validate ALL user inputs — never trust external data.
A4. Use parameterized queries — NEVER concatenate SQL strings.
A5. Encode ALL outputs — context-aware (HTML, JS, URL, CSS).
A6. Hash passwords with bcrypt (cost 12+) or argon2id — NEVER store plaintext.
A7. Use HTTPS/TLS for ALL external communications — no exceptions.
A8. Log security-relevant events — auth, access, errors, data changes.
A9. Handle errors gracefully — return generic messages to users, log details internally.
A10. Follow the principle of least privilege — minimum permissions everywhere.
A11. Run linter/formatter after writing each file.
A12. Add type annotations/hints to all function signatures.
A13. Write docstrings/JSDoc for all public APIs.
A14. Use environment variables for ALL configuration — never hardcode.
A15. Implement rate limiting on all public endpoints.
A16. Set security headers on all HTTP responses.
A17. Implement CSRF protection on all state-changing operations.
A18. Use secure session management — HttpOnly, Secure, SameSite cookies.
A19. Implement proper CORS — never use wildcard (*) in production.
A20. Create database migrations — never modify schema manually.

### Section B: YOU MUST NOT

B1. NEVER introduce new dependencies without explicit approval from AI CTO.
B2. NEVER store secrets, keys, passwords, or tokens in code or config files.
B3. NEVER use eval(), exec(), or dynamic code execution.
B4. NEVER use MD5 or SHA1 for security purposes (hashing, signing).
B5. NEVER disable SSL/TLS verification.
B6. NEVER use wildcard CORS (*) in production configuration.
B7. NEVER log passwords, tokens, credit card numbers, or full PII.
B8. NEVER expose stack traces or internal errors to users.
B9. NEVER use root/admin database credentials in application code.
B10. NEVER commit .env files, private keys, or certificates to git.
B11. NEVER use innerHTML or dangerouslySetInnerHTML without sanitization.
B12. NEVER make architecture decisions — that's Level 1/2 authority.
B13. NEVER modify infrastructure files (Terraform, K8s manifests) — that's DevOps.
B14. NEVER modify security configurations — that's Security Officer.
B15. NEVER skip writing tests "to save time".
B16. NEVER use deprecated or end-of-life libraries.
B17. NEVER generate fake/mock data that looks like real PII.
B18. NEVER use console.log/print for production logging — use structured loggers.
B19. NEVER create god classes/functions — keep functions under 50 lines.
B20. NEVER ignore linter warnings — fix them or document why they're exceptions.

### Section C: WHEN IN DOUBT

C1. If requirements are unclear → ASK the human (do not guess).
C2. If two approaches exist → Choose the MORE SECURE one.
C3. If a dependency is needed → Request approval with justification.
C4. If performance vs security trade-off → Security wins.
C5. If a task seems outside your role → Escalate to the appropriate agent level.
```

### 5.3 File Ownership Rules

```yaml
file_ownership:
  # Only DevOps Agent may create or modify these
  devops_owned:
    - "Dockerfile*"
    - "docker-compose*.yml"
    - ".github/workflows/*"
    - ".gitlab-ci.yml"
    - "Jenkinsfile"
    - "terraform/**"
    - "pulumi/**"
    - "ansible/**"
    - "k8s/**"
    - "kubernetes/**"
    - "helm/**"
    - "infrastructure/**"
    - "scripts/deploy*"
    - "scripts/setup*"
    - "Makefile"
    - "Procfile"
    - "fly.toml"
    - "railway.json"
    - "render.yaml"
    - "nginx.conf"

  # Only Security Agent may create or modify these
  security_owned:
    - "SECURITY.md"
    - "security/**"
    - "**/security_config*"
    - "**/cors_config*"
    - "**/csp_config*"
    - "**/rate_limit_config*"
    - ".bandit"
    - ".snyk"
    - ".gitleaks.toml"
    - "sonar-project.properties"

  # Executor Agents may create or modify these
  executor_owned:
    - "src/**"
    - "app/**"
    - "lib/**"
    - "internal/**"
    - "cmd/**"
    - "pkg/**"
    - "tests/**"
    - "test/**"
    - "spec/**"
    - "components/**"
    - "pages/**"
    - "routes/**"
    - "models/**"
    - "services/**"
    - "controllers/**"
    - "handlers/**"
    - "repositories/**"
    - "utils/**"
    - "helpers/**"
    - "middlewares/**"  # implementation only, not security config
    - "types/**"
    - "interfaces/**"

  # Shared (any agent within its scope)
  shared:
    - "README.md"
    - "docs/**"
    - "CHANGELOG.md"
    - "package.json"  # executor can add scripts, devops manages versions
    - "requirements.txt"  # managed by approval process
    - "go.mod"
    - "go.sum"
    - "pyproject.toml"
    - "Cargo.toml"
```

### 5.4 Approved Dependency Policy

```markdown
## Dependency Approval Process

### Pre-Approved Libraries (No approval needed)

**Python:**
- fastapi, uvicorn, gunicorn
- sqlalchemy, alembic
- pydantic, pydantic-settings
- bcrypt, passlib, python-jose, cryptography
- httpx, aiohttp
- pytest, pytest-cov, pytest-asyncio
- celery, redis
- structlog, python-json-logger
- sentry-sdk

**Node.js / TypeScript:**
- express, fastify, nestjs, hono
- prisma, drizzle-orm, typeorm, knex
- zod, joi (validation)
- bcrypt, jsonwebtoken, jose
- helmet (security headers)
- express-rate-limit, rate-limiter-flexible
- jest, vitest, supertest
- winston, pino (logging)
- bull, bullmq (queues)

**React / Next.js:**
- next, react, react-dom
- tailwindcss, shadcn/ui
- react-hook-form, zod
- tanstack/react-query
- zustand, jotai (state)
- next-auth (auth.js)
- lucide-react (icons)

**Go:**
- gin, echo, chi (routers)
- gorm, sqlx (database)
- golang-jwt/jwt
- golang.org/x/crypto
- zerolog, zap (logging)
- testify (testing)
- viper (config)
- cobra (CLI)

**Java / Spring:**
- spring-boot-starter-web
- spring-boot-starter-security
- spring-boot-starter-data-jpa
- spring-boot-starter-validation
- jjwt (JWT)
- lombok
- mapstruct
- springdoc-openapi

### Approval Required (Must justify to AI CTO)
- Any dependency not in the pre-approved list
- Any dependency with < 1000 GitHub stars
- Any dependency last updated > 6 months ago
- Any dependency with known CVEs
- Any dependency that requires native compilation
```

### 5.5 Forbidden Patterns

```yaml
forbidden_patterns:

  # Security anti-patterns — NEVER generate these
  security:
    - pattern: "eval("
      reason: "Remote code execution risk"
      fix: "Use safe parsing (JSON.parse, ast.literal_eval)"
    
    - pattern: "exec("
      reason: "Remote code execution risk"
      fix: "Use subprocess with shell=False"
    
    - pattern: "f\"SELECT.*{.*}.*\""
      reason: "SQL injection via string interpolation"
      fix: "Use parameterized queries"
    
    - pattern: "innerHTML ="
      reason: "XSS vulnerability"
      fix: "Use textContent or sanitize with DOMPurify"
    
    - pattern: "dangerouslySetInnerHTML"
      reason: "XSS vulnerability"
      fix: "Use sanitize-html or DOMPurify before rendering"
    
    - pattern: "password.*=.*['\"]"
      reason: "Hardcoded credentials"
      fix: "Use environment variables"
    
    - pattern: "CORS.*\\*"
      reason: "Wildcard CORS allows any origin"
      fix: "Specify explicit allowed origins"
    
    - pattern: "verify.*=.*False"
      reason: "Disabled SSL verification"
      fix: "Always verify SSL certificates"
    
    - pattern: "MD5|md5"
      reason: "Broken hash algorithm"
      fix: "Use SHA-256+ or bcrypt for passwords"
    
    - pattern: "console\\.log"
      reason: "Debug logging in production"
      fix: "Use structured logger (winston, pino, structlog)"
    
    - pattern: "TODO|FIXME|HACK|XXX"
      reason: "Unfinished code"
      fix: "Complete the implementation before committing"

  # Code quality anti-patterns
  quality:
    - pattern: "function with >50 lines"
      fix: "Break into smaller, focused functions"
    
    - pattern: "file with >400 lines"
      fix: "Split into multiple modules"
    
    - pattern: "deeply nested if/else (>3 levels)"
      fix: "Use early returns or guard clauses"
    
    - pattern: "catch(e) { /* empty */ }"
      fix: "Log the error or handle it properly"
    
    - pattern: "any type (TypeScript)"
      fix: "Define proper types/interfaces"
    
    - pattern: "magic numbers"
      fix: "Extract to named constants"
```

---

## 6. IDE Agent Playbooks

### 6.1 Purpose

Each IDE/AI tool has different capabilities and limitations. These playbooks tell each tool exactly how to behave when working on projects governed by A-SDLC.

### 6.2 Cursor IDE Playbook

```markdown
## CURSOR IDE AGENT PLAYBOOK

### Your Identity
You are an AI EXECUTOR (Level 3) in the A-SDLC hierarchy.
You write code. You do NOT make architecture decisions.

### When You Start a Session
1. READ the project's A-SDLC.md and masterSDLC.md (if referenced)
2. READ the project's README.md for tech stack and setup
3. READ any existing code contracts or .cursor/rules
4. IDENTIFY your current phase (Build? Fix? Test?)
5. ASK the user what specific task they want done

### When You Write Code
1. BEFORE writing: check coding contracts (Section 5)
2. IMPLEMENT exactly what's specified — no more, no less
3. WRITE tests alongside the implementation
4. RUN linter after each file
5. CHECK for forbidden patterns (Section 5.5)
6. COMMIT with descriptive messages per feature

### When You're Unsure
1. NEVER guess requirements — ask the user
2. NEVER add dependencies without stating which and why
3. NEVER refactor unrelated code
4. If blocked: state what you need and stop

### Code Generation Rules
1. Always use TypeScript (not JavaScript) when the project uses TS
2. Always add proper error handling
3. Always add input validation
4. Always add type annotations
5. Always use async/await (not .then())
6. Always use const/let (never var)
7. Always handle loading/error states in UI components
8. Always use named exports (not default exports)
9. Always add JSDoc/docstrings to public functions
10. Always check for null/undefined before accessing properties

### File Organization
- One component per file
- One utility function group per file
- One test file per source file
- Keep files under 300 lines
- Use barrel exports (index.ts) for directories

### Commit Message Format
type(scope): description

Examples:
  feat(auth): implement JWT login endpoint with rate limiting
  fix(api): prevent SQL injection in user search endpoint
  test(auth): add security tests for password reset flow
  refactor(db): extract user repository from service layer

### What to Do When Tests Fail
1. READ the error message carefully
2. FIX the root cause (not the symptom)
3. RE-RUN the specific test
4. If still failing after 3 attempts: ask the user
5. NEVER delete or skip failing tests

### What to Do When Linter Fails
1. FIX all linter errors immediately
2. DO NOT suppress warnings without justification
3. If a rule seems wrong: ask the user, don't disable it
```

### 6.3 Claude (in Cursor/API) Playbook

```markdown
## CLAUDE AGENT PLAYBOOK

### Your Identity
When working inside Cursor or via API, you operate as the AI CTO (Level 1)
AND Executor (Level 3) — switching roles as needed.

### Role Switching Protocol
- When PLANNING: operate as AI CTO
  → Select tech stack, design architecture, define contracts
  → Prefix thoughts with [AI CTO]
  
- When IMPLEMENTING: operate as Executor
  → Write code, tests, follow contracts
  → Prefix thoughts with [EXECUTOR]
  
- When REVIEWING: operate as Security Officer
  → Check for vulnerabilities, contract violations
  → Prefix thoughts with [SECURITY]

### Context Management (CRITICAL)
Claude has limited context windows. To maximize effectiveness:

1. FRONT-LOAD important information
   - Tech stack, current file structure, active contracts
   
2. SUMMARIZE before switching tasks
   - "I've completed auth module. Moving to payment integration."
   
3. REFERENCE files by path, don't paste entire files
   - "As defined in src/auth/service.ts:45-60..."
   
4. KEEP working memory lean
   - Complete one feature fully before starting the next
   - Don't open 10 files at once

### Multi-File Operations
When a feature touches multiple files:
1. LIST all files that will be created/modified
2. IMPLEMENT in dependency order (models → services → handlers → tests)
3. TEST after each file is complete
4. NEVER leave a file half-done

### When You Don't Know Something
1. DO NOT hallucinate library APIs — check docs or ask
2. DO NOT invent configuration options
3. DO NOT assume environment variables exist — check .env.example
4. If documentation is unclear: state the ambiguity and propose 2 options
```

### 6.4 Antigravity IDE Playbook

```markdown
## ANTIGRAVITY AGENT PLAYBOOK

### Your Identity
You are an AI EXECUTOR (Level 3) optimized for full-stack development.

### Special Capabilities
Antigravity excels at full-project generation. Use this strength by:
1. Generating complete feature slices (frontend + backend + tests)
2. Maintaining consistency across the stack
3. Leveraging multi-file awareness

### Operating Rules
1. Follow ALL rules from the Universal Coding Contract (Section 5.2)
2. Follow ALL file ownership rules (Section 5.3)
3. When generating a full project:
   a. Generate scaffold FIRST (Phase 4)
   b. Generate code layer by layer (Phase 5 build order)
   c. Generate tests alongside each layer
   d. NEVER generate the entire project in one shot without structure

### Quality Gates
Before declaring a feature "complete":
- [ ] All files follow coding contracts
- [ ] All files have corresponding tests
- [ ] No forbidden patterns present
- [ ] No hardcoded secrets or config
- [ ] Linter passes
- [ ] Types/interfaces are properly defined
```

### 6.5 GitHub Copilot Playbook

```markdown
## GITHUB COPILOT PLAYBOOK

### Your Identity
You are a CODE HELPER — Level 3 Executor, inline completion mode.

### Behavior Rules
1. FOLLOW the patterns already established in the codebase
2. COMPLETE functions using the same style as surrounding code
3. NEVER suggest deprecated APIs
4. NEVER suggest insecure patterns (eval, innerHTML, string concatenation in SQL)
5. ALWAYS include error handling in suggested code
6. ALWAYS match the project's naming conventions
7. PREFER strong types over `any` or dynamic types

### When Suggesting Imports
1. Suggest from the project's existing dependencies FIRST
2. NEVER suggest new dependencies without explicit installation
3. Prefer relative imports for project files
4. Prefer absolute imports for packages

### Comment-Driven Development
When you see a descriptive comment, generate implementation that:
- Exactly matches what the comment describes
- Includes error handling
- Includes input validation
- Follows the project's patterns
```

### 6.6 General AI IDE Rules (Universal)

```markdown
## UNIVERSAL IDE AGENT RULES

### File Creation Checklist
Before creating any new file:
1. Check if a similar file already exists
2. Verify the file belongs in the intended directory
3. Use the project's naming convention (camelCase, snake_case, kebab-case)
4. Include license header if project requires it
5. Add necessary imports
6. Export the public API

### Naming Conventions by Language

**Python:**
- Files: snake_case.py
- Classes: PascalCase
- Functions: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private: _prefix

**TypeScript/JavaScript:**
- Files: kebab-case.ts or PascalCase.tsx (components)
- Classes: PascalCase
- Functions: camelCase
- Variables: camelCase
- Constants: UPPER_SNAKE_CASE
- Interfaces: PascalCase (no I prefix)
- Types: PascalCase
- Enums: PascalCase with PascalCase members

**Go:**
- Files: lowercase.go
- Public: PascalCase
- Private: camelCase
- Packages: lowercase, single word
- Interfaces: -er suffix (Reader, Writer)
- Acronyms: ALL CAPS (HTTP, URL, ID)

**Java:**
- Files: PascalCase.java (matches class name)
- Classes: PascalCase
- Methods: camelCase
- Variables: camelCase
- Constants: UPPER_SNAKE_CASE
- Packages: lowercase.dotted

### Error Handling Patterns

**Python:**
try:
    result = await service.create_user(data)
except ValidationError as e:
    logger.warning("Validation failed", extra={"errors": str(e)})
    raise HTTPException(status_code=400, detail="Invalid input")
except DuplicateError:
    logger.info("Duplicate registration attempt", extra={"email_hash": hash_email(data.email)})
    raise HTTPException(status_code=409, detail="Account already exists")
except Exception as e:
    logger.error("Unexpected error in user creation", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

**TypeScript:**
try {
  const result = await userService.create(data);
  return res.status(201).json({ success: true, data: result });
} catch (error) {
  if (error instanceof ValidationError) {
    logger.warn('Validation failed', { errors: error.details });
    return res.status(400).json({ success: false, error: 'Invalid input' });
  }
  if (error instanceof ConflictError) {
    logger.info('Duplicate attempt', { emailHash: hashEmail(data.email) });
    return res.status(409).json({ success: false, error: 'Already exists' });
  }
  logger.error('Unexpected error', { error: error.message, stack: error.stack });
  return res.status(500).json({ success: false, error: 'Internal server error' });
}

**Go:**
result, err := service.CreateUser(ctx, data)
if err != nil {
    switch {
    case errors.Is(err, ErrValidation):
        logger.Warn("validation failed", "error", err)
        return c.JSON(http.StatusBadRequest, ErrorResponse{Error: "Invalid input"})
    case errors.Is(err, ErrDuplicate):
        logger.Info("duplicate registration", "email_hash", hashEmail(data.Email))
        return c.JSON(http.StatusConflict, ErrorResponse{Error: "Already exists"})
    default:
        logger.Error("unexpected error", "error", err)
        return c.JSON(http.StatusInternalServerError, ErrorResponse{Error: "Internal server error"})
    }
}
```

---

## 7. Autonomous Feedback & Self-Correction Loop

### 7.1 Purpose

The self-correction loop ensures that AI-generated code meets quality and security standards automatically, without human intervention for routine issues.

### 7.2 The Loop Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AI GENERATES CODE                          │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              AUTOMATED VALIDATION PIPELINE                    │
│                                                               │
│  Step 1: LINT CHECK                                          │
│  ├─ Run project linter (eslint/ruff/golangci-lint)           │
│  ├─ If FAIL → AI fixes → re-run (max 3 attempts)            │
│  └─ If PASS → proceed                                       │
│                                                               │
│  Step 2: TYPE CHECK                                          │
│  ├─ Run type checker (mypy/tsc/go vet)                       │
│  ├─ If FAIL → AI fixes → re-run (max 3 attempts)            │
│  └─ If PASS → proceed                                       │
│                                                               │
│  Step 3: UNIT TESTS                                          │
│  ├─ Run test suite                                           │
│  ├─ If FAIL → AI reads error, fixes code → re-run            │
│  ├─ Max 3 fix attempts per failing test                       │
│  └─ If still failing → ESCALATE to human                     │
│                                                               │
│  Step 4: SECURITY SCAN                                       │
│  ├─ Run SAST (bandit/semgrep/eslint-security)                │
│  ├─ If CRITICAL/HIGH found → AI fixes → re-scan              │
│  ├─ If MEDIUM found → AI fixes if straightforward            │
│  └─ If LOW/INFO → log and continue                           │
│                                                               │
│  Step 5: DEPENDENCY CHECK                                    │
│  ├─ Run dependency scanner (safety/npm audit/snyk)            │
│  ├─ If vulnerable dependency found → update/replace           │
│  └─ If no fix available → ESCALATE with advisory              │
│                                                               │
│  Step 6: SECRET SCAN                                         │
│  ├─ Run secret detector (gitleaks/detect-secrets)             │
│  ├─ If secret found → REMOVE immediately, replace with env    │
│  └─ No secret in code → proceed                              │
│                                                               │
│  Step 7: CONTRACT COMPLIANCE                                 │
│  ├─ Check file ownership rules                               │
│  ├─ Check forbidden patterns                                 │
│  ├─ Check dependency policy                                  │
│  └─ If violation → AI fixes → re-check                       │
│                                                               │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
                    ALL PASSED? ──── NO ──→ Fix Loop (max 3)
                        │                      │
                       YES                  STILL FAILING
                        │                      │
                        ▼                      ▼
                   ┌─────────┐          ┌──────────────┐
                   │ COMMIT  │          │ ESCALATE TO  │
                   │ & NEXT  │          │ HUMAN        │
                   │ FEATURE │          │ WITH DETAILS │
                   └─────────┘          └──────────────┘
```

### 7.3 Self-Correction Rules

```markdown
## Self-Correction Protocol

### Rule 1: Three Strikes
- AI gets 3 attempts to fix any issue
- Each attempt must try a DIFFERENT approach
- After 3 failures: stop and escalate

### Rule 2: Fix the Root Cause
- Don't suppress warnings
- Don't delete failing tests
- Don't add type: ignore / @ts-ignore / nolint without justification
- Fix the actual problem, not the symptom

### Rule 3: Regression Prevention
- After fixing a bug, add a test that catches it
- Never introduce a fix that breaks existing tests
- If a fix breaks something else: revert and escalate

### Rule 4: Escalation Format
When escalating to human, provide:

ESCALATION REPORT
================
Issue: [What's wrong]
Location: [File:line]
Attempts Made:
  1. [What I tried first] → [Why it failed]
  2. [What I tried second] → [Why it failed]
  3. [What I tried third] → [Why it failed]
Root Cause Analysis: [My best understanding]
Recommended Options:
  A. [Option A with trade-offs]
  B. [Option B with trade-offs]
Blocking: [What can't proceed until this is resolved]

### Rule 5: Never Auto-Fix These (Always Escalate)
- Architecture changes
- New dependency additions
- Security policy modifications
- Database schema changes (beyond migrations)
- Infrastructure configuration changes
- Anything touching production credentials
```

### 7.4 CI/CD Integration of Self-Correction

```yaml
# .github/workflows/ai-validation.yml
name: AI Code Validation Pipeline

on:
  push:
    branches: [main, develop, 'feature/*']
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    name: Lint Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Runtime
        uses: ./.github/actions/setup  # Project-specific setup
      - name: Run Linter
        run: make lint
      - name: Run Formatter Check
        run: make format-check

  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Runtime
        uses: ./.github/actions/setup
      - name: Run Type Checker
        run: make type-check

  test:
    name: Unit & Integration Tests
    needs: [lint, type-check]
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Setup Runtime
        uses: ./.github/actions/setup
      - name: Run Tests
        run: make test-ci
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
      - name: Upload Coverage
        uses: codecov/codecov-action@v4

  security-scan:
    name: Security Scanning
    needs: [lint]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Runtime
        uses: ./.github/actions/setup
      
      - name: SAST Scan
        run: make security-sast
      
      - name: Dependency Vulnerability Scan
        run: make security-deps
      
      - name: Secret Detection
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Container Scan (if Dockerfile exists)
        if: hashFiles('Dockerfile') != ''
        run: |
          docker build -t app:scan .
          trivy image --severity HIGH,CRITICAL --exit-code 1 app:scan

  contract-check:
    name: Coding Contract Compliance
    needs: [lint]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Forbidden Patterns
        run: |
          # Check for eval/exec usage
          ! rg 'eval\(|exec\(' --type py --type js --type ts -l || \
            (echo "FORBIDDEN: eval/exec found" && exit 1)
          
          # Check for hardcoded secrets patterns
          ! rg '(password|secret|api_key|token)\s*=\s*["\x27][^"]+["\x27]' \
            --type py --type js --type ts --type go --type java \
            -g '!*.test.*' -g '!*.spec.*' -g '!*test*' -g '!*.md' -l || \
            (echo "FORBIDDEN: Possible hardcoded secret found" && exit 1)
          
          # Check for TODO/FIXME
          ! rg 'TODO|FIXME|HACK|XXX' --type py --type js --type ts --type go \
            -g '!*.md' -g '!A-SDLC.md' -g '!masterSDLC.md' -l || \
            (echo "WARNING: Unresolved TODOs found" && exit 1)
          
          # Check for console.log in production code
          ! rg 'console\.(log|debug|info)' --type ts --type js \
            -g '!*.test.*' -g '!*.spec.*' -g '!jest.config.*' -l || \
            (echo "FORBIDDEN: console.log found in production code" && exit 1)

  deploy-staging:
    name: Deploy to Staging
    needs: [test, security-scan, contract-check]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Staging
        run: make deploy-staging

  deploy-production:
    name: Deploy to Production
    needs: [test, security-scan, contract-check]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: 
      name: production
      # Human approval required for production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Production
        run: make deploy-production
```

---

## 8. Golden Infrastructure Stack

### 8.1 Purpose

Define the **default** infrastructure choices so AI agents don't waste time debating tools. Defaults can be overridden with justification.

### 8.2 The Golden Stack

```yaml
golden_stack:
  
  infrastructure_as_code:
    preferred: "Terraform"
    alternatives: ["Pulumi (for TypeScript teams)", "CDK (for AWS-only)"]
    override_justification_required: true
    reasoning: "Widest provider support. Largest community. Best AI code generation."

  ci_cd:
    preferred: "GitHub Actions"
    alternatives: ["GitLab CI", "Azure DevOps", "Jenkins"]
    override_justification_required: false  # Team preference acceptable
    reasoning: "Tightest GitHub integration. Largest marketplace. Free for public repos."

  containerization:
    preferred: "Docker"
    alternatives: ["Podman (for rootless requirement)"]
    non_negotiable_rules:
      - "Non-root user in all containers"
      - "Multi-stage builds"
      - "Minimal base images (alpine/distroless)"
      - "No latest tag in production"
      - "Health checks required"

  orchestration:
    preferred: "Kubernetes (EKS/GKE/AKS)"
    alternatives: 
      - "Docker Compose (for small projects)"
      - "AWS ECS Fargate (for serverless containers)"
      - "Railway/Render/Fly.io (for startups)"
    selection_rule: |
      if scale < 5 services: Docker Compose
      if scale 5-20 services: ECS Fargate or Cloud Run
      if scale > 20 services: Kubernetes
      if team has K8s expertise: Kubernetes regardless

  secrets_management:
    preferred: "HashiCorp Vault"
    alternatives:
      - "AWS Secrets Manager (for AWS-native)"
      - "GCP Secret Manager (for GCP-native)"
      - "Azure Key Vault (for Azure-native)"
      - "Doppler (for multi-cloud)"
    non_negotiable_rules:
      - "NO secrets in environment variables in code"
      - "NO secrets in Docker images"
      - "NO secrets in git (even .gitignore'd files)"
      - "Rotation policy: 90 days maximum"

  observability:
    logging:
      preferred: "ELK Stack (Elasticsearch + Logstash + Kibana)"
      alternatives: ["Grafana Loki + Grafana", "Datadog", "AWS CloudWatch"]
      format: "Structured JSON logging — ALWAYS"
    
    metrics:
      preferred: "Prometheus + Grafana"
      alternatives: ["Datadog", "AWS CloudWatch", "New Relic"]
    
    tracing:
      preferred: "OpenTelemetry + Jaeger"
      alternatives: ["Datadog APM", "AWS X-Ray", "Honeycomb"]
    
    error_tracking:
      preferred: "Sentry"
      alternatives: ["Rollbar", "Bugsnag"]
    
    uptime_monitoring:
      preferred: "UptimeRobot or Betterstack"
      alternatives: ["Pingdom", "StatusCake"]

  web_application_firewall:
    preferred: "Cloudflare WAF"
    alternatives: ["AWS WAF", "ModSecurity (self-hosted)"]
    non_negotiable_rules:
      - "OWASP Core Rule Set enabled"
      - "Rate limiting enabled"
      - "Bot detection enabled"
      - "DDoS protection enabled"

  cdn:
    preferred: "Cloudflare"
    alternatives: ["AWS CloudFront", "Fastly", "Bunny CDN"]

  email:
    transactional:
      preferred: "Resend or Postmark"
      alternatives: ["SendGrid", "AWS SES", "Mailgun"]
    marketing:
      preferred: "ConvertKit or Mailchimp"

  dns:
    preferred: "Cloudflare DNS"
    alternatives: ["AWS Route 53", "Google Cloud DNS"]

  version_control:
    preferred: "GitHub"
    alternatives: ["GitLab (for self-hosted)", "Bitbucket (for Jira integration)"]
    non_negotiable_rules:
      - "Branch protection on main/master"
      - "PR reviews required"
      - "CI must pass before merge"
      - "No force push to main"
```

### 8.3 Non-Negotiable Infrastructure Rules

```markdown
## Infrastructure Laws (Cannot Be Overridden)

1. ALL data encrypted at rest (AES-256)
2. ALL data encrypted in transit (TLS 1.3)
3. ALL containers run as non-root
4. ALL infrastructure defined as code (no manual console changes)
5. ALL secrets managed by a secrets manager (never in code/env files)
6. ALL production deployments require health checks
7. ALL production systems have monitoring and alerting
8. ALL databases have automated backups
9. ALL cloud resources have least-privilege IAM policies
10. ALL production networks are segmented (DMZ, private, data)
11. NO public SSH access to production servers
12. NO database ports exposed to the internet
13. NO wildcard (*) in security group rules
14. NO unencrypted S3 buckets / storage blobs
15. AUTOMATIC patching enabled for OS and managed services
```

---

## 9. One-Command Project Bootstrap

### 9.1 Purpose

Generate a complete, security-hardened project structure with a single command or prompt. The AI should be able to scaffold an entire project based on the decisions made in Phases 1-3.

### 9.2 Bootstrap Prompt Template

When a human says "create a project" or "bootstrap" or "scaffold", the AI should follow this template:

```markdown
## PROJECT BOOTSTRAP CHECKLIST

### Step 1: Collect Requirements (Phase 1 — DISCOVER)
Ask the user:
1. What does this project do?
2. Who are the users?
3. Expected scale?
4. Sensitive data involved?
5. Compliance requirements?
6. Deployment target?
7. Budget level?
8. Timeline?
9. Existing codebase?
10. Must-have integrations?

### Step 2: Select Tech Stack (Phase 2 — DESIGN)
Using Section 4 rules, select:
- Backend language + framework
- Frontend framework (if applicable)
- Database(s)
- Authentication strategy
- Cloud provider
- CI/CD platform

### Step 3: Generate Project Structure (Phase 4 — SCAFFOLD)
Create the complete folder structure (see templates below).

### Step 4: Generate Configuration Files
- Dockerfile (multi-stage, non-root)
- docker-compose.yml (dev + prod)
- CI/CD pipeline (.github/workflows/)
- Linter config (eslint/ruff/golangci-lint)
- Formatter config (prettier/black/gofmt)
- .env.example
- .gitignore
- README.md

### Step 5: Generate Base Code
- Entry point (main.py / index.ts / main.go)
- Health check endpoint
- Structured logging setup
- Error handling middleware
- Security headers middleware
- CORS configuration
- Rate limiting middleware
- Database connection setup
- Authentication module skeleton
- Test configuration

### Step 6: Verify Bootstrap
- Project builds successfully
- All tests pass (even if just health check test)
- Linter passes
- Docker image builds
- CI pipeline definition is valid
```

### 9.3 Project Structure Templates

#### Template: Python + FastAPI

```
project-name/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                     # Lint + Test + Security scan
│   │   ├── deploy-staging.yml         # Deploy to staging
│   │   └── deploy-production.yml      # Deploy to production
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI application entry
│   ├── config.py                      # Settings (pydantic-settings)
│   ├── dependencies.py                # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # API v1 router
│   │   │   ├── auth.py                # Auth endpoints
│   │   │   ├── users.py               # User endpoints
│   │   │   └── health.py              # Health check
│   │   └── deps.py                    # Route dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py                # JWT, hashing, encryption
│   │   ├── exceptions.py              # Custom exceptions
│   │   ├── logging.py                 # Structured logging setup
│   │   └── middleware.py              # Security headers, CORS, rate limit
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                    # SQLAlchemy base model
│   │   ├── user.py                    # User model
│   │   └── audit_log.py              # Audit log model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                    # Auth request/response schemas
│   │   ├── user.py                    # User schemas
│   │   └── common.py                  # Shared schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py            # Auth business logic
│   │   ├── user_service.py            # User business logic
│   │   └── email_service.py           # Email sending
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                    # Base repository pattern
│   │   ├── user_repo.py              # User data access
│   │   └── audit_repo.py             # Audit log data access
│   └── utils/
│       ├── __init__.py
│       ├── validators.py              # Input validators
│       └── helpers.py                 # Utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_auth_service.py
│   │   ├── test_user_service.py
│   │   └── test_security.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_auth_api.py
│   │   └── test_user_api.py
│   └── security/
│       ├── __init__.py
│       ├── test_injection.py          # SQL/XSS injection tests
│       ├── test_auth_security.py      # Auth bypass tests
│       └── test_rate_limiting.py      # Rate limit tests
├── alembic/
│   ├── env.py
│   ├── versions/
│   └── alembic.ini
├── scripts/
│   ├── setup-dev.sh                   # Dev environment setup
│   ├── run-tests.sh                   # Test runner
│   ├── security-scan.sh               # Security scanning
│   └── seed-data.py                   # Database seeding (dev only)
├── docs/
│   ├── API.md                         # API documentation
│   ├── ARCHITECTURE.md                # Architecture decisions
│   └── DEPLOYMENT.md                  # Deployment guide
├── .env.example                       # Environment template
├── .gitignore
├── .dockerignore
├── .pre-commit-config.yaml            # Pre-commit hooks
├── Dockerfile                         # Multi-stage secure build
├── docker-compose.yml                 # Development
├── docker-compose.prod.yml            # Production-like
├── Makefile                           # Project commands
├── pyproject.toml                     # Python project config (ruff, pytest, mypy)
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt               # Development dependencies
├── README.md
├── SECURITY.md                        # Security disclosure policy
├── CHANGELOG.md
└── LICENSE
```

#### Template: TypeScript + Next.js (Full-Stack)

```
project-name/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── deploy-staging.yml
│   │   └── deploy-production.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Home page
│   │   ├── error.tsx                  # Error boundary
│   │   ├── not-found.tsx              # 404 page
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/page.tsx
│   │   │   └── layout.tsx
│   │   └── api/
│   │       ├── auth/[...nextauth]/route.ts
│   │       ├── health/route.ts
│   │       └── v1/
│   │           ├── users/route.ts
│   │           └── users/[id]/route.ts
│   ├── components/
│   │   ├── ui/                        # Reusable UI (shadcn/ui)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── forms/
│   │   │   ├── login-form.tsx
│   │   │   └── register-form.tsx
│   │   ├── layout/
│   │   │   ├── header.tsx
│   │   │   ├── footer.tsx
│   │   │   └── sidebar.tsx
│   │   └── providers/
│   │       ├── auth-provider.tsx
│   │       ├── theme-provider.tsx
│   │       └── query-provider.tsx
│   ├── lib/
│   │   ├── auth.ts                    # NextAuth configuration
│   │   ├── db.ts                      # Database client (Prisma)
│   │   ├── redis.ts                   # Redis client
│   │   ├── logger.ts                  # Structured logging
│   │   ├── rate-limit.ts              # Rate limiting
│   │   └── validations/
│   │       ├── auth.ts                # Zod schemas for auth
│   │       └── user.ts               # Zod schemas for users
│   ├── services/
│   │   ├── auth-service.ts
│   │   ├── user-service.ts
│   │   └── email-service.ts
│   ├── types/
│   │   ├── api.ts                     # API types
│   │   ├── auth.ts                    # Auth types
│   │   └── user.ts                    # User types
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-user.ts
│   │   └── use-debounce.ts
│   ├── utils/
│   │   ├── cn.ts                      # className utility
│   │   ├── format.ts                  # Formatters
│   │   └── security.ts                # Security helpers
│   └── middleware.ts                   # Next.js middleware (auth, headers, rate limit)
├── prisma/
│   ├── schema.prisma                  # Database schema
│   ├── migrations/
│   └── seed.ts                        # Database seeding
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   └── utils/
│   ├── integration/
│   │   ├── api/
│   │   └── auth/
│   ├── e2e/
│   │   ├── login.spec.ts
│   │   └── register.spec.ts
│   └── security/
│       ├── xss.spec.ts
│       ├── csrf.spec.ts
│       └── injection.spec.ts
├── public/
│   ├── favicon.ico
│   └── robots.txt
├── scripts/
│   ├── setup-dev.sh
│   ├── security-scan.sh
│   └── seed-db.ts
├── .env.example
├── .env.local.example
├── .gitignore
├── .dockerignore
├── .eslintrc.json
├── .prettierrc.json
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── next.config.ts                     # Security headers, CSP
├── tailwind.config.ts
├── tsconfig.json
├── vitest.config.ts
├── playwright.config.ts               # E2E test config
├── package.json
├── README.md
├── SECURITY.md
├── CHANGELOG.md
└── LICENSE
```

#### Template: Go + Gin

```
project-name/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── deploy-staging.yml
│   │   └── deploy-production.yml
│   └── CODEOWNERS
├── cmd/
│   └── api/
│       └── main.go                    # Entry point
├── internal/
│   ├── config/
│   │   └── config.go                  # Configuration (Viper)
│   ├── handler/
│   │   ├── auth_handler.go            # Auth HTTP handlers
│   │   ├── user_handler.go            # User HTTP handlers
│   │   ├── health_handler.go          # Health check
│   │   └── handler.go                 # Handler group
│   ├── middleware/
│   │   ├── auth.go                    # JWT middleware
│   │   ├── cors.go                    # CORS config
│   │   ├── rate_limit.go              # Rate limiting
│   │   ├── security_headers.go        # Security headers
│   │   ├── logging.go                 # Request logging
│   │   └── recovery.go               # Panic recovery
│   ├── model/
│   │   ├── user.go                    # User model
│   │   ├── audit_log.go              # Audit model
│   │   └── base.go                    # Base model
│   ├── repository/
│   │   ├── user_repo.go              # User data access
│   │   ├── audit_repo.go             # Audit data access
│   │   └── repository.go             # Repository interface
│   ├── service/
│   │   ├── auth_service.go            # Auth business logic
│   │   ├── user_service.go            # User business logic
│   │   └── email_service.go           # Email service
│   ├── dto/
│   │   ├── auth_dto.go                # Auth request/response
│   │   └── user_dto.go               # User request/response
│   └── pkg/
│       ├── security/
│       │   ├── jwt.go                 # JWT utilities
│       │   ├── hash.go                # Password hashing
│       │   └── encryption.go          # Data encryption
│       ├── logger/
│       │   └── logger.go              # Structured logging (zerolog)
│       ├── validator/
│       │   └── validator.go           # Input validation
│       └── errors/
│           └── errors.go              # Custom error types
├── migrations/
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
├── tests/
│   ├── integration/
│   │   ├── auth_test.go
│   │   └── user_test.go
│   └── security/
│       ├── injection_test.go
│       └── auth_security_test.go
├── scripts/
│   ├── setup-dev.sh
│   ├── security-scan.sh
│   └── migrate.sh
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
├── .dockerignore
├── .golangci.yml                      # Linter config
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── go.mod
├── go.sum
├── README.md
├── SECURITY.md
├── CHANGELOG.md
└── LICENSE
```

#### Template: Java + Spring Boot

```
project-name/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── deploy-staging.yml
│   │   └── deploy-production.yml
│   └── CODEOWNERS
├── src/
│   ├── main/
│   │   ├── java/com/company/project/
│   │   │   ├── Application.java               # Spring Boot entry
│   │   │   ├── config/
│   │   │   │   ├── SecurityConfig.java         # Spring Security
│   │   │   │   ├── CorsConfig.java             # CORS
│   │   │   │   ├── RateLimitConfig.java        # Rate limiting
│   │   │   │   └── WebConfig.java              # Web configuration
│   │   │   ├── controller/
│   │   │   │   ├── AuthController.java
│   │   │   │   ├── UserController.java
│   │   │   │   └── HealthController.java
│   │   │   ├── service/
│   │   │   │   ├── AuthService.java
│   │   │   │   ├── UserService.java
│   │   │   │   └── EmailService.java
│   │   │   ├── repository/
│   │   │   │   ├── UserRepository.java
│   │   │   │   └── AuditLogRepository.java
│   │   │   ├── model/
│   │   │   │   ├── User.java
│   │   │   │   ├── AuditLog.java
│   │   │   │   └── BaseEntity.java
│   │   │   ├── dto/
│   │   │   │   ├── auth/
│   │   │   │   │   ├── LoginRequest.java
│   │   │   │   │   ├── RegisterRequest.java
│   │   │   │   │   └── AuthResponse.java
│   │   │   │   └── user/
│   │   │   │       ├── UserRequest.java
│   │   │   │       └── UserResponse.java
│   │   │   ├── security/
│   │   │   │   ├── JwtTokenProvider.java
│   │   │   │   ├── JwtAuthFilter.java
│   │   │   │   └── SecurityUtils.java
│   │   │   ├── exception/
│   │   │   │   ├── GlobalExceptionHandler.java
│   │   │   │   ├── ResourceNotFoundException.java
│   │   │   │   └── UnauthorizedException.java
│   │   │   └── util/
│   │   │       ├── ValidationUtils.java
│   │   │       └── SecurityHelpers.java
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-staging.yml
│   │       ├── application-prod.yml
│   │       └── db/migration/          # Flyway migrations
│   │           └── V1__create_users.sql
│   └── test/
│       └── java/com/company/project/
│           ├── unit/
│           │   ├── AuthServiceTest.java
│           │   └── UserServiceTest.java
│           ├── integration/
│           │   ├── AuthControllerTest.java
│           │   └── UserControllerTest.java
│           └── security/
│               ├── InjectionTest.java
│               └── AuthSecurityTest.java
├── scripts/
│   ├── setup-dev.sh
│   └── security-scan.sh
├── docs/
│   ├── API.md
│   └── ARCHITECTURE.md
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pom.xml                            # Maven (or build.gradle for Gradle)
├── README.md
├── SECURITY.md
└── LICENSE
```

### 9.4 Universal Makefile Template

```makefile
# ============================================
# Universal Project Makefile
# Generated by A-SDLC Bootstrap
# ============================================

.PHONY: help setup dev test lint format security build deploy-staging deploy-production clean

# Default target
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Development
# ============================================

setup: ## Set up development environment
	@echo "Setting up development environment..."
	@./scripts/setup-dev.sh

dev: ## Start development server
	docker-compose up -d
	@echo "Development server started"

dev-down: ## Stop development server
	docker-compose down

dev-logs: ## View development logs
	docker-compose logs -f

# ============================================
# Code Quality
# ============================================

lint: ## Run linter
	# Python: ruff check app/ tests/
	# TypeScript: npx eslint src/ --ext .ts,.tsx
	# Go: golangci-lint run ./...
	# Java: mvn checkstyle:check
	@echo "Linting passed"

format: ## Format code
	# Python: ruff format app/ tests/
	# TypeScript: npx prettier --write src/
	# Go: gofmt -w .
	# Java: mvn spotless:apply
	@echo "Formatting complete"

format-check: ## Check formatting without changes
	# Python: ruff format --check app/ tests/
	# TypeScript: npx prettier --check src/
	# Go: gofmt -l .
	@echo "Format check complete"

type-check: ## Run type checker
	# Python: mypy app/
	# TypeScript: npx tsc --noEmit
	# Go: go vet ./...
	@echo "Type check passed"

# ============================================
# Testing
# ============================================

test: ## Run all tests
	# Python: pytest tests/ -v --cov=app --cov-report=term-missing
	# TypeScript: npx vitest run --coverage
	# Go: go test ./... -v -cover
	# Java: mvn test
	@echo "All tests passed"

test-unit: ## Run unit tests only
	# Python: pytest tests/unit/ -v
	# TypeScript: npx vitest run tests/unit/
	# Go: go test ./internal/... -v
	@echo "Unit tests passed"

test-integration: ## Run integration tests
	# Python: pytest tests/integration/ -v
	# TypeScript: npx vitest run tests/integration/
	# Go: go test ./tests/integration/... -v
	@echo "Integration tests passed"

test-security: ## Run security tests
	# Python: pytest tests/security/ -v
	# TypeScript: npx vitest run tests/security/
	# Go: go test ./tests/security/... -v
	@echo "Security tests passed"

test-ci: ## Run tests for CI (with coverage output)
	# Python: pytest tests/ -v --cov=app --cov-report=xml --junitxml=test-results.xml
	# TypeScript: npx vitest run --coverage --reporter=junit
	# Go: go test ./... -v -coverprofile=coverage.out -json > test-results.json
	@echo "CI tests complete"

# ============================================
# Security
# ============================================

security: security-sast security-deps security-secrets ## Run all security scans

security-sast: ## Static Application Security Testing
	# Python: bandit -r app/ -f json -o reports/bandit.json && semgrep --config=p/owasp-top-ten app/
	# TypeScript: npx eslint src/ --config .eslintrc.security.json
	# Go: gosec ./...
	# Java: mvn spotbugs:check
	@echo "SAST scan complete"

security-deps: ## Dependency vulnerability scan
	# Python: safety check && pip-audit
	# TypeScript: npm audit --audit-level=high
	# Go: govulncheck ./...
	# Java: mvn dependency-check:check
	@echo "Dependency scan complete"

security-secrets: ## Secret detection scan
	gitleaks detect --source . --verbose
	@echo "Secret scan complete"

security-container: ## Container security scan
	docker build -t app:scan .
	trivy image --severity HIGH,CRITICAL app:scan
	@echo "Container scan complete"

# ============================================
# Build & Deploy
# ============================================

build: ## Build production image
	docker build -t app:latest .
	@echo "Build complete"

deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	@./scripts/deploy-staging.sh

deploy-production: ## Deploy to production (requires approval)
	@echo "WARNING: Deploying to PRODUCTION"
	@read -p "Are you sure? (yes/no) " confirm && [ "$$confirm" = "yes" ] || exit 1
	@./scripts/deploy-production.sh

# ============================================
# Database
# ============================================

db-migrate: ## Run database migrations
	# Python: alembic upgrade head
	# TypeScript: npx prisma migrate deploy
	# Go: migrate -path migrations/ -database $DATABASE_URL up
	# Java: mvn flyway:migrate
	@echo "Migrations complete"

db-rollback: ## Rollback last migration
	# Python: alembic downgrade -1
	# TypeScript: npx prisma migrate resolve
	# Go: migrate -path migrations/ -database $DATABASE_URL down 1
	# Java: mvn flyway:undo
	@echo "Rollback complete"

db-seed: ## Seed database with development data
	@echo "Seeding database..."
	# Python: python scripts/seed-data.py
	# TypeScript: npx prisma db seed
	@echo "Seeding complete"

# ============================================
# Cleanup
# ============================================

clean: ## Clean build artifacts
	docker-compose down -v
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	rm -rf node_modules .next out dist coverage
	rm -rf reports/
	@echo "Cleaned"
```

---

## 10. AI Prompt Library for Secure Code Generation

### 10.1 Purpose

Pre-built prompts that AI agents should use when generating specific types of code. These ensure consistent, secure output regardless of which AI model is used.

### 10.2 Backend Prompts

#### Prompt: Secure API Endpoint

```
Generate a [FRAMEWORK] API endpoint for [RESOURCE] with the following requirements:

Functional:
- HTTP method: [GET/POST/PUT/PATCH/DELETE]
- Route: [/api/v1/resource]
- Request body/params: [schema]
- Response: [schema]
- Business logic: [description]

Security (MANDATORY):
- Input validation using [VALIDATION_LIBRARY] with strict schema
- Authentication required: [yes/no]
- Authorization: [role/permission required]
- Rate limiting: [X requests per Y minutes]
- Audit logging for all state changes
- No PII in logs (hash or redact)
- Parameterized database queries
- Output encoding
- CSRF protection (for state-changing operations)
- Proper error handling (generic errors to user, detailed logs internally)

Testing:
- Unit test for happy path
- Unit test for validation failure
- Unit test for unauthorized access
- Unit test for rate limiting
- Security test for SQL injection attempt
- Security test for XSS attempt

Code Quality:
- Type annotations on all parameters and return types
- Docstring with description, params, returns, raises
- Follow project naming conventions
- Keep function under 50 lines
```

#### Prompt: Database Model

```
Generate a [ORM] model for [ENTITY] with the following requirements:

Fields:
- [field_name]: [type], [constraints]
- (repeat for each field)

Security Requirements:
- UUID primary key (not auto-increment integers)
- Created/updated timestamps (auto-managed)
- Soft delete support (deleted_at timestamp)
- Sensitive fields encrypted at application level: [list fields]
- Password fields: bcrypt hashed, NEVER stored in plain text
- PII fields annotated for GDPR data mapping
- No cascade deletes without explicit specification
- Indexes on frequently queried fields
- Unique constraints where applicable

Relationships:
- [relationship description]

Additional:
- Migration file for creating the table
- Type annotations / TypeScript types
- Validation rules for each field
- Factory/fixture for testing
```

#### Prompt: Authentication Module

```
Generate a complete authentication module with:

Features:
1. User registration (email/password)
   - Email validation (format + uniqueness)
   - Password strength enforcement (min 12 chars, uppercase, lowercase, digit, special)
   - bcrypt hashing (cost 12)
   - Email verification token generation
   - No username enumeration (same response for existing/new email)
   - Rate limiting: 5 registrations per 15 minutes per IP

2. User login
   - Email/password authentication
   - JWT access token (15 min expiry, RS256)
   - Refresh token (7 day expiry, stored hashed in DB)
   - Account lockout after 5 failed attempts (30 min cooldown)
   - Rate limiting: 5 attempts per 5 minutes per IP
   - CSRF protection
   - Secure cookie storage (HttpOnly, Secure, SameSite=Lax)

3. Token refresh
   - Validate refresh token
   - Issue new access token
   - Rotate refresh token on use
   - Detect refresh token reuse (invalidate all tokens)

4. Password reset
   - Cryptographically secure token (32 bytes, URL-safe)
   - 15-minute expiry
   - Single-use
   - No username enumeration
   - Invalidate all sessions on reset
   - Rate limiting: 3 requests per 15 minutes

5. Logout
   - Invalidate refresh token
   - Add access token to blacklist (until expiry)
   - Clear cookies

Testing:
- All happy paths
- All error cases
- All security scenarios (injection, bypass, enumeration)
- Rate limiting behavior
- Token expiry behavior
```

### 10.3 Frontend Prompts

#### Prompt: Secure Form Component

```
Generate a [FRAMEWORK] form component for [PURPOSE] with:

Fields:
- [field_name]: [type], [validation rules]
- (repeat)

Security:
- Client-side validation using [zod/yup/joi]
- XSS prevention (no dangerouslySetInnerHTML)
- CSRF token included in submission
- No sensitive data in URL parameters
- Auto-clear sensitive fields on unmount
- Disable autocomplete on password fields
- Rate limit submit button (prevent double-submission)
- Sanitize all inputs before display

UX:
- Loading state during submission
- Error display (field-level + form-level)
- Success feedback
- Accessible (ARIA labels, keyboard navigation)
- Responsive design
- Form state preservation on navigation (non-sensitive fields only)

Testing:
- Renders correctly
- Validates required fields
- Shows field-level errors
- Submits successfully with valid data
- Handles API errors gracefully
- XSS attempt in input field is sanitized
```

#### Prompt: Protected Route / Page

```
Generate a protected [route/page] that:

Authentication:
- Redirects to login if not authenticated
- Checks token validity (not just existence)
- Handles token refresh transparently
- Shows loading state during auth check

Authorization:
- Required role: [role]
- Required permission: [permission]
- Shows 403 page if unauthorized (not 404)
- Does not leak route existence to unauthorized users

Security:
- No sensitive data in component state that persists after unmount
- No sensitive data in browser history
- Security headers set via middleware
- CSP-compliant (no inline scripts/styles)
```

### 10.4 Infrastructure Prompts

#### Prompt: Dockerfile

```
Generate a Dockerfile for [LANGUAGE/FRAMEWORK] with:

Security Requirements:
- Multi-stage build (builder + runtime)
- Non-root user (UID 1000)
- Minimal base image (alpine or distroless)
- No unnecessary packages in runtime stage
- Health check endpoint configured
- Read-only root filesystem compatible
- No secrets in build args or environment
- Specific version tags (no :latest)
- COPY --chown for application files
- Remove build artifacts and caches

Performance:
- Layer caching optimized (deps before code)
- .dockerignore configured properly
- Minimal final image size

Labels:
- Maintainer
- Version
- Security scan tool
```

#### Prompt: CI/CD Pipeline

```
Generate a [CI/CD platform] pipeline with:

Stages:
1. Lint (code style + formatting)
2. Type check (static type analysis)
3. Unit tests (with coverage)
4. Integration tests (with service containers)
5. Security scan (SAST + dependency + secrets)
6. Build container image
7. Container security scan
8. Deploy to staging (auto, on develop branch)
9. Deploy to production (manual approval, on main branch)

Requirements:
- Cache dependencies between runs
- Parallel execution where possible
- Fail fast on security issues
- Coverage report upload
- Test result reporting
- Artifact storage for build outputs
- Environment-specific secrets
- Slack/Teams notification on failure
```

### 10.5 Database Prompts

#### Prompt: Secure Schema Design

```
Generate a database schema for [PROJECT DESCRIPTION] with:

Tables:
- [list tables and their purpose]

Security Requirements:
- UUID primary keys (gen_random_uuid())
- Created/updated timestamps on all tables
- Soft delete (deleted_at) on user-facing tables
- Row-Level Security (RLS) policies where applicable
- Encrypted columns for sensitive data (PII, financial)
- Audit log table for all data changes
- No cascade deletes (explicit delete handling)
- Foreign key constraints
- Check constraints for data integrity
- Indexes on query-critical columns
- Unique constraints where applicable

Migration:
- Up migration (create)
- Down migration (rollback)
- Seed data for development (no real PII)
```

---

## 11. Compliance Automation Engine

### 11.1 Purpose

Automate compliance checking so AI agents can verify regulatory requirements are met without manual review.

### 11.2 GDPR Compliance Checklist (Automated)

```yaml
gdpr_compliance:
  data_collection:
    - check: "Privacy policy exists and is accessible"
      verify: "Look for /privacy, /privacy-policy route or page"
      severity: "CRITICAL"
    
    - check: "Cookie consent mechanism implemented"
      verify: "Look for cookie consent component/library"
      severity: "CRITICAL"
    
    - check: "Data processing purposes documented"
      verify: "Check for data processing records in docs/"
      severity: "HIGH"
    
    - check: "Legal basis for processing defined"
      verify: "Each data collection point has consent or legitimate interest"
      severity: "HIGH"

  user_rights:
    - check: "Right to Access — data export endpoint exists"
      verify: "GET /api/v1/users/me/data-export"
      severity: "CRITICAL"
    
    - check: "Right to Erasure — account deletion endpoint exists"
      verify: "DELETE /api/v1/users/me with data purge"
      severity: "CRITICAL"
    
    - check: "Right to Rectification — profile update endpoint exists"
      verify: "PUT/PATCH /api/v1/users/me"
      severity: "HIGH"
    
    - check: "Right to Portability — data export in standard format"
      verify: "Export in JSON or CSV format"
      severity: "HIGH"
    
    - check: "Right to Object — opt-out mechanism"
      verify: "Marketing/tracking opt-out functionality"
      severity: "MEDIUM"

  data_protection:
    - check: "Encryption at rest for PII"
      verify: "Database/field encryption configured"
      severity: "CRITICAL"
    
    - check: "Encryption in transit"
      verify: "TLS 1.3 configured, HSTS header present"
      severity: "CRITICAL"
    
    - check: "Data minimization"
      verify: "Only necessary fields collected"
      severity: "HIGH"
    
    - check: "Data retention policy implemented"
      verify: "Automated data cleanup jobs exist"
      severity: "HIGH"
    
    - check: "PII not in logs"
      verify: "Log sanitization middleware/filters in place"
      severity: "CRITICAL"

  breach_notification:
    - check: "Breach detection mechanism"
      verify: "Anomaly detection alerts configured"
      severity: "HIGH"
    
    - check: "72-hour notification process"
      verify: "Incident response plan documented"
      severity: "HIGH"
    
    - check: "User notification capability"
      verify: "Mass email notification system exists"
      severity: "HIGH"

  third_party:
    - check: "Data Processing Agreements with all processors"
      verify: "DPA documents in docs/legal/"
      severity: "HIGH"
    
    - check: "Third-party data sharing documented"
      verify: "Third-party integrations audited"
      severity: "HIGH"
```

### 11.3 PCI-DSS Compliance Checklist (Automated)

```yaml
pci_dss_compliance:
  requirement_1_network:
    - check: "Firewall/security groups configured"
      verify: "Network segmentation in IaC templates"
      severity: "CRITICAL"
    
    - check: "DMZ for public-facing services"
      verify: "Public/private subnet separation"
      severity: "CRITICAL"
    
    - check: "No direct database access from internet"
      verify: "Database in private subnet"
      severity: "CRITICAL"

  requirement_3_stored_data:
    - check: "No credit card numbers stored in application"
      verify: "Grep for card number patterns in codebase"
      severity: "CRITICAL"
    
    - check: "No CVV/CVC storage"
      verify: "No CVV fields in database schema"
      severity: "CRITICAL"
    
    - check: "Tokenization for payment processing"
      verify: "Stripe/Braintree tokenization configured"
      severity: "CRITICAL"

  requirement_4_transmission:
    - check: "TLS 1.3 for all transmissions"
      verify: "TLS config in load balancer/reverse proxy"
      severity: "CRITICAL"
    
    - check: "No fallback to older TLS versions"
      verify: "Only TLS 1.2+ allowed"
      severity: "CRITICAL"

  requirement_6_secure_dev:
    - check: "OWASP Top 10 addressed"
      verify: "Security controls for each OWASP category"
      severity: "CRITICAL"
    
    - check: "Code review process"
      verify: "PR review requirement in branch protection"
      severity: "HIGH"
    
    - check: "Security testing in CI/CD"
      verify: "SAST/DAST in pipeline"
      severity: "HIGH"

  requirement_8_auth:
    - check: "Strong authentication"
      verify: "Password policy enforced (12+ chars, complexity)"
      severity: "CRITICAL"
    
    - check: "MFA for admin access"
      verify: "MFA enforcement for admin roles"
      severity: "CRITICAL"
    
    - check: "Account lockout"
      verify: "Lockout after failed attempts"
      severity: "HIGH"

  requirement_10_logging:
    - check: "Audit logging for all access"
      verify: "Audit log model and middleware exist"
      severity: "CRITICAL"
    
    - check: "Log tamper protection"
      verify: "Centralized logging with append-only"
      severity: "HIGH"
    
    - check: "Log retention (1 year)"
      verify: "Log retention policy configured"
      severity: "HIGH"
```

### 11.4 SOC 2 Compliance Checklist

```yaml
soc2_compliance:
  security:
    - check: "Access control policies defined"
      verify: "RBAC implementation exists"
      severity: "CRITICAL"
    
    - check: "Encryption at rest and in transit"
      verify: "TLS + AES-256 configured"
      severity: "CRITICAL"
    
    - check: "Vulnerability management"
      verify: "Security scanning in CI/CD"
      severity: "HIGH"
    
    - check: "Incident response plan"
      verify: "docs/INCIDENT_RESPONSE.md exists"
      severity: "HIGH"

  availability:
    - check: "Uptime monitoring"
      verify: "Health checks and uptime monitoring configured"
      severity: "HIGH"
    
    - check: "Backup and recovery"
      verify: "Automated backups with tested restore"
      severity: "CRITICAL"
    
    - check: "Disaster recovery plan"
      verify: "DR plan documented and tested"
      severity: "HIGH"

  processing_integrity:
    - check: "Input validation"
      verify: "Validation middleware on all endpoints"
      severity: "HIGH"
    
    - check: "Data integrity checks"
      verify: "Database constraints and checksums"
      severity: "HIGH"

  confidentiality:
    - check: "Data classification"
      verify: "Data classification document exists"
      severity: "HIGH"
    
    - check: "Access logging"
      verify: "Audit trail for sensitive data access"
      severity: "CRITICAL"

  privacy:
    - check: "Privacy notice"
      verify: "Privacy policy exists"
      severity: "HIGH"
    
    - check: "Consent management"
      verify: "User consent tracking implemented"
      severity: "HIGH"
    
    - check: "Data retention"
      verify: "Retention policy and cleanup jobs"
      severity: "HIGH"
```

### 11.5 HIPAA Compliance Checklist

```yaml
hipaa_compliance:
  technical_safeguards:
    - check: "Access control (unique user ID)"
      verify: "Individual user accounts, no shared credentials"
      severity: "CRITICAL"
    
    - check: "Audit controls"
      verify: "Comprehensive audit logging of PHI access"
      severity: "CRITICAL"
    
    - check: "Integrity controls"
      verify: "Data integrity verification mechanisms"
      severity: "CRITICAL"
    
    - check: "Transmission security"
      verify: "End-to-end encryption for PHI"
      severity: "CRITICAL"
    
    - check: "Encryption at rest"
      verify: "AES-256 encryption for stored PHI"
      severity: "CRITICAL"

  administrative_safeguards:
    - check: "Security management process"
      verify: "Risk analysis documented"
      severity: "HIGH"
    
    - check: "Workforce training"
      verify: "Security training documentation"
      severity: "HIGH"
    
    - check: "Contingency plan"
      verify: "Data backup and disaster recovery plan"
      severity: "CRITICAL"
    
    - check: "Business Associate Agreements"
      verify: "BAAs with all third-party services handling PHI"
      severity: "CRITICAL"

  physical_safeguards:
    - check: "Facility access controls"
      verify: "Cloud provider physical security certifications"
      severity: "HIGH"
    
    - check: "Workstation security"
      verify: "Endpoint security policy documented"
      severity: "MEDIUM"
```

---

## 12. Monitoring & Observability Automation

### 12.1 Purpose

Pre-configured monitoring that AI agents deploy automatically with every project.

### 12.2 Monitoring Stack Setup

```yaml
monitoring_setup:
  
  application_metrics:
    tool: "Prometheus"
    auto_instrument:
      - "Request count (by endpoint, method, status)"
      - "Request latency (p50, p95, p99)"
      - "Error rate"
      - "Active connections"
      - "Database query time"
      - "Cache hit/miss ratio"
      - "Authentication success/failure"
      - "Rate limit hits"
      - "Queue depth (if applicable)"
      - "Memory usage"
      - "CPU usage"
    
    endpoints:
      health: "/health"
      readiness: "/ready"
      metrics: "/metrics"

  logging:
    format: "Structured JSON"
    required_fields:
      - "timestamp (ISO 8601)"
      - "level (debug/info/warn/error/fatal)"
      - "message"
      - "service_name"
      - "request_id (correlation ID)"
      - "user_id (hashed, for authenticated requests)"
      - "ip_address (for security events only)"
      - "method + path (for HTTP requests)"
      - "status_code (for HTTP responses)"
      - "duration_ms (for timing)"
      - "error_type + stack_trace (for errors, internal only)"
    
    NEVER_LOG:
      - "Passwords or password hashes"
      - "API keys or tokens (full)"
      - "Credit card numbers"
      - "Social security numbers"
      - "Full email addresses (hash them)"
      - "Session tokens (full)"
      - "Request/response bodies with PII"

  alerting:
    critical_alerts:
      - name: "Service Down"
        condition: "Health check fails for > 1 minute"
        action: "Page on-call + auto-restart"
      
      - name: "Error Rate Spike"
        condition: "5xx rate > 5% for > 5 minutes"
        action: "Page on-call + prepare rollback"
      
      - name: "Security: Brute Force Detected"
        condition: "Failed auth > 50 per minute from same IP"
        action: "Auto-block IP + alert security"
      
      - name: "Security: Unusual Data Access"
        condition: "Bulk data export or unusual query patterns"
        action: "Alert security + log details"
      
      - name: "Database Connection Saturation"
        condition: "Connection pool > 80% utilized"
        action: "Alert DevOps"
      
      - name: "Disk Space Low"
        condition: "Disk usage > 85%"
        action: "Alert DevOps + auto-cleanup logs"

    warning_alerts:
      - name: "High Latency"
        condition: "p95 latency > 2s for > 5 minutes"
        action: "Alert DevOps"
      
      - name: "Memory Usage High"
        condition: "Memory > 80% for > 10 minutes"
        action: "Alert DevOps"
      
      - name: "Certificate Expiry"
        condition: "TLS certificate expires in < 14 days"
        action: "Alert DevOps + auto-renew if configured"
      
      - name: "Dependency Vulnerability"
        condition: "New critical CVE detected in dependencies"
        action: "Alert Security + create ticket"

  dashboards:
    overview:
      - "Request rate (RPM)"
      - "Error rate (%)"
      - "Latency (p50, p95, p99)"
      - "Active users"
      - "Infrastructure health"
    
    security:
      - "Authentication success/failure rate"
      - "Rate limit hits by endpoint"
      - "Blocked IPs"
      - "Failed authorization attempts"
      - "Unusual access patterns"
      - "Security scan results"
    
    infrastructure:
      - "CPU usage by service"
      - "Memory usage by service"
      - "Disk usage"
      - "Network I/O"
      - "Database connections"
      - "Cache hit ratio"
      - "Queue depth"
    
    business:
      - "User registrations"
      - "Active sessions"
      - "API usage by endpoint"
      - "Feature usage metrics"
```

---

## 13. Disaster Recovery & Rollback Automation

### 13.1 Rollback Protocol

```markdown
## Automated Rollback Rules

### When to Auto-Rollback
1. Health check fails within 5 minutes of deployment
2. Error rate exceeds 10% within 10 minutes of deployment
3. Critical security vulnerability detected in deployed version
4. Data corruption detected

### Rollback Process
1. DETECT: Monitoring detects issue (automated)
2. DECIDE: If auto-rollback criteria met → proceed (no human needed)
           If unclear → alert human, pause deployment
3. EXECUTE: 
   - Revert to last known good version
   - Run health checks on reverted version
   - Verify data integrity
4. NOTIFY: Alert team with rollback details
5. INVESTIGATE: Root cause analysis (can be AI-assisted)

### Rollback Commands
# Kubernetes
kubectl rollout undo deployment/app-name

# Docker Compose
docker-compose up -d --force-recreate  # with previous image tag

# Database (if migration was applied)
make db-rollback

### Prevention
- Blue/green deployments for zero-downtime
- Canary releases (10% traffic → 50% → 100%)
- Feature flags for gradual rollout
- Database migrations must be backward-compatible
```

### 13.2 Backup Strategy

```yaml
backup_strategy:
  database:
    frequency: "Every 6 hours (production)"
    retention: "30 days daily, 12 months monthly"
    type: "Point-in-time recovery (PITR)"
    encryption: "AES-256"
    location: "Different region from primary"
    verification: "Monthly restore test"
    automation: "Cloud-native (RDS snapshots, Cloud SQL backups)"

  application_data:
    frequency: "Daily"
    includes: ["User uploads", "Generated reports", "Configuration"]
    excludes: ["Temporary files", "Cache", "Logs (stored separately)"]
    encryption: "AES-256"
    location: "Cross-region replication"

  secrets:
    frequency: "On every change"
    mechanism: "Vault snapshots or secrets manager versioning"
    retention: "All versions"

  disaster_recovery:
    rto: "< 1 hour (Recovery Time Objective)"
    rpo: "< 1 hour (Recovery Point Objective)"
    testing: "Quarterly DR drills"
    documentation: "docs/DISASTER_RECOVERY.md"
```

---

## 14. Token & Context Management for AI IDEs

### 14.1 Why This Matters

AI IDEs (Cursor, Antigravity, Claude) have limited context windows. Poor context management leads to:
- Forgetting earlier decisions
- Inconsistent code generation
- Repeated mistakes
- Lost architecture context

### 14.2 Context Optimization Rules

```markdown
## Context Management Protocol

### Rule 1: Front-Load Critical Context
Always include at the start of a session:
1. Tech stack summary (3-5 lines)
2. Current phase (which phase are we in?)
3. Active coding contracts (key rules only)
4. File being worked on and its dependencies

### Rule 2: Summarize Before Switching
When moving to a new feature/file:
"COMPLETED: Auth module — login, register, reset, MFA endpoints.
 All tests passing. Moving to: User profile management."

### Rule 3: Reference, Don't Paste
Instead of pasting entire files:
"Following the pattern in src/services/auth-service.ts (lines 45-80)..."

### Rule 4: Checkpoint Every Major Feature
After completing each feature:
"CHECKPOINT: Features complete: [list]. Tests passing: [count]. 
 Next: [feature]. Blockers: [none/list]."

### Rule 5: Session Handoff Format
When ending a session and another might continue:

SESSION HANDOFF
==============
Project: [name]
Stack: [backend/frontend/db]
Phase: [current phase]
Completed:
  - [feature 1] ✅
  - [feature 2] ✅
In Progress:
  - [feature 3] — 60% done, needs [X, Y]
Not Started:
  - [feature 4]
  - [feature 5]
Active Issues:
  - [issue 1]
Key Files Modified This Session:
  - [file list]
Next Steps:
  1. [step 1]
  2. [step 2]
```

### 14.3 Efficient Prompting for Large Projects

```markdown
## Large Project Prompting Strategy

### For Projects > 50 Files

1. NEVER try to hold the entire project in context
2. Work on ONE module/feature at a time
3. Use a "context file" (CONTEXT.md) that summarizes:
   - Architecture overview (10 lines)
   - Module dependency map
   - Active contracts
   - Current sprint/phase

4. When starting a new file:
   "I'm implementing [feature] in [file]. 
    It depends on: [dep1], [dep2]. 
    It should follow the pattern in: [reference file].
    Contract: [relevant rules]."

5. When debugging:
   "Error in [file:line]: [error message].
    This file calls: [dependencies].
    Recent changes: [what changed].
    Expected behavior: [what should happen]."
```

---

## 15. Universal Project Type Support

### 15.1 Purpose

A-SDLC supports ANY project type. This section maps project types to their specific considerations.

### 15.2 Project Type Matrix

```yaml
project_types:

  web_api:
    description: "REST/GraphQL API backend"
    typical_stack: "FastAPI/NestJS/Spring Boot + PostgreSQL + Redis"
    key_concerns: ["Authentication", "Rate limiting", "Input validation", "API versioning"]
    security_focus: "OWASP Top 10, API security"
    
  saas:
    description: "Multi-tenant SaaS application"
    typical_stack: "Next.js + NestJS/FastAPI + PostgreSQL + Redis + Stripe"
    key_concerns: ["Multi-tenancy", "Subscription billing", "Data isolation", "Onboarding"]
    security_focus: "Tenant isolation, data leakage prevention"

  e_commerce:
    description: "Online store / marketplace"
    typical_stack: "Next.js + FastAPI/NestJS + PostgreSQL + Redis + Stripe/PayPal"
    key_concerns: ["Payment processing", "Inventory management", "Search", "Performance"]
    security_focus: "PCI-DSS, payment security, fraud detection"

  mobile_backend:
    description: "Backend for mobile applications"
    typical_stack: "FastAPI/NestJS + PostgreSQL + Redis + Firebase Push"
    key_concerns: ["Push notifications", "Offline sync", "API versioning", "App authentication"]
    security_focus: "Mobile auth (PKCE), certificate pinning, API key management"

  real_time:
    description: "Real-time application (chat, collaboration, gaming)"
    typical_stack: "Go/NestJS + PostgreSQL + Redis + WebSocket"
    key_concerns: ["WebSocket security", "Connection management", "Message ordering", "Scaling"]
    security_focus: "WebSocket auth, message validation, DoS prevention"

  microservices:
    description: "Distributed microservices architecture"
    typical_stack: "Go/Java/TypeScript + PostgreSQL + Redis + Kafka + K8s"
    key_concerns: ["Service discovery", "Inter-service auth", "Event consistency", "Tracing"]
    security_focus: "mTLS, service mesh security, API gateway"

  data_pipeline:
    description: "ETL / data processing pipeline"
    typical_stack: "Python + PostgreSQL + Redis + Celery/Airflow"
    key_concerns: ["Data quality", "Idempotency", "Scheduling", "Monitoring"]
    security_focus: "Data encryption in transit, access controls, audit logging"

  ml_service:
    description: "Machine learning model serving"
    typical_stack: "Python + FastAPI + PostgreSQL + Redis + Docker"
    key_concerns: ["Model versioning", "Inference latency", "A/B testing", "Monitoring"]
    security_focus: "Model access control, input validation, adversarial robustness"

  cli_tool:
    description: "Command-line tool / utility"
    typical_stack: "Go (Cobra) or Python (Click/Typer) or Rust (Clap)"
    key_concerns: ["Cross-platform", "Configuration", "Output formatting", "Error handling"]
    security_focus: "Input validation, secure config storage, no secrets in history"

  desktop_app:
    description: "Desktop application"
    typical_stack: "Tauri/Electron + React/Svelte"
    key_concerns: ["Auto-updates", "File system access", "Native integration", "Packaging"]
    security_focus: "IPC security, file system sandboxing, code signing, update verification"

  static_site:
    description: "Static website / documentation"
    typical_stack: "Astro/Next.js/Hugo + Cloudflare Pages"
    key_concerns: ["SEO", "Performance", "Content management", "Deployment"]
    security_focus: "CSP headers, dependency security, supply chain"

  iot_backend:
    description: "IoT device management backend"
    typical_stack: "Go/Python + PostgreSQL + TimescaleDB + MQTT + Redis"
    key_concerns: ["Device auth", "Telemetry ingestion", "Firmware updates", "Scaling"]
    security_focus: "Device certificate auth, mTLS, firmware signing, data encryption"

  blockchain_dapp:
    description: "Decentralized application"
    typical_stack: "Next.js + Solidity/Rust + PostgreSQL (off-chain)"
    key_concerns: ["Smart contract security", "Wallet integration", "Gas optimization"]
    security_focus: "Smart contract auditing, reentrancy prevention, key management"
```

---

## 16. Internationalization & Localization (i18n)

### 16.1 When to Add i18n

```yaml
i18n_rules:
  required:
    - "Users from more than one language region"
    - "Any app targeting Middle East (Arabic + English minimum)"
    - "Any app targeting Europe (multi-language required by EU standards)"
    - "Any app with GDPR compliance (privacy policy must be in user's language)"
  
  not_needed:
    - "Internal tools with single-language team"
    - "MVPs targeting one country only (add later)"
```

### 16.2 i18n Library Selection

```yaml
i18n_library_selection:

  nextjs:
    preferred: "next-intl"
    alternative: "next-i18next"
    reasoning: "next-intl has App Router support, type-safe, smaller bundle"

  react:
    preferred: "react-i18next + i18next"
    alternative: "FormatJS (react-intl)"
    reasoning: "Largest ecosystem, lazy loading, namespace support"

  vue_nuxt:
    preferred: "@nuxtjs/i18n (Nuxt) or vue-i18n (Vue)"
    reasoning: "Official Nuxt module with built-in SEO support"

  python_fastapi:
    preferred: "babel + custom middleware"
    alternative: "python-i18n"
    reasoning: "Babel handles date/number formatting, custom middleware for API responses"

  python_django:
    preferred: "Django built-in i18n (gettext)"
    reasoning: "Battle-tested, built into framework"

  go:
    preferred: "go-i18n"
    reasoning: "Most popular, supports pluralization"

  java_spring:
    preferred: "Spring MessageSource (built-in)"
    reasoning: "Built into framework, supports resource bundles"
```

### 16.3 RTL (Right-to-Left) Support

```yaml
rtl_rules:
  when_required:
    - "Arabic (ar)"
    - "Urdu (ur)"
    - "Hebrew (he)"
    - "Persian/Farsi (fa)"

  implementation:
    css: "Use logical properties (margin-inline-start instead of margin-left)"
    html: "Add dir='rtl' attribute dynamically based on locale"
    tailwind: "Use rtl: prefix (rtl:mr-4 instead of ml-4)"
    icons: "Mirror directional icons (arrows, progress bars)"
    
  testing:
    - "Test every page in both LTR and RTL"
    - "Test form inputs in RTL"
    - "Test numbers (stay LTR even in RTL context)"
    - "Test mixed content (English text inside Arabic page)"

  premium_charge: "+20% of base project cost for full RTL support"
```

### 16.4 Translation File Structure

```
locales/
├── en/
│   ├── common.json        # Shared translations (buttons, labels)
│   ├── auth.json           # Login, register, password reset
│   ├── dashboard.json      # Dashboard-specific
│   └── errors.json         # Error messages
├── ar/
│   ├── common.json
│   ├── auth.json
│   ├── dashboard.json
│   └── errors.json
├── ur/
│   └── ...
└── [language-code]/
    └── ...
```

### 16.5 i18n Rules for AI Agents

```
1. NEVER hardcode user-facing strings — always use translation keys
2. NEVER concatenate translated strings (word order differs per language)
3. ALWAYS use ICU message format for plurals and variables
4. ALWAYS format dates, numbers, and currency using Intl API or locale-aware libraries
5. ALWAYS store user's preferred language in their profile
6. ALWAYS set HTML lang attribute based on current locale
7. ALWAYS include hreflang tags for SEO (multi-language pages)
8. ALWAYS extract translation keys during build (no runtime key generation)
```

---

## 17. API Versioning Strategy

### 17.1 Versioning Method

```yaml
api_versioning:
  preferred: "URL path versioning"
  format: "/api/v1/resource"
  
  alternatives:
    - method: "Header versioning (Accept-Version: v1)"
      use_when: "Internal APIs, microservices"
    - method: "Query parameter (?version=1)"
      use_when: "Never — hard to cache, not recommended"

  rules:
    - "Start every API at v1 — never v0"
    - "Version the ENTIRE API, not individual endpoints"
    - "Keep at most 2 versions active (current + previous)"
    - "Deprecate old versions with 6-month notice"
```

### 17.2 Breaking vs Non-Breaking Changes

```yaml
non_breaking_changes:  # Do NOT require new version
  - "Adding a new optional field to response"
  - "Adding a new endpoint"
  - "Adding a new optional query parameter"
  - "Adding a new enum value"
  - "Improving error messages"
  - "Performance improvements"

breaking_changes:  # REQUIRE new version
  - "Removing a field from response"
  - "Renaming a field"
  - "Changing a field's type"
  - "Removing an endpoint"
  - "Changing authentication method"
  - "Changing error response format"
  - "Making an optional parameter required"
  - "Changing URL structure"
```

### 17.3 Deprecation Protocol

```
1. ANNOUNCE: Add Deprecation header to old version responses
   Deprecation: true
   Sunset: Sat, 01 Jan 2027 00:00:00 GMT
   Link: </api/v2/resource>; rel="successor-version"

2. DOCUMENT: Update API docs with migration guide
   - What changed
   - How to update client code
   - New endpoint mappings

3. NOTIFY: Email all API consumers 6 months before sunset

4. MONITOR: Track v1 usage — don't remove until traffic < 1%

5. REMOVE: After sunset date, return 410 Gone with migration link
```

---

## 18. Multi-Tenancy Architecture Rules

### 18.1 When Multi-Tenancy Applies

```yaml
multi_tenancy_required:
  - "SaaS applications"
  - "White-label platforms"
  - "B2B applications where each client is a tenant"
  - "Marketplace platforms with seller isolation"
```

### 18.2 Isolation Strategy Selection

```yaml
multi_tenancy_strategy:

  # Strategy 1: Row-Level Isolation (Shared DB, shared schema)
  row_level:
    when:
      tenants: "<1,000"
      data_sensitivity: "medium"
      compliance: "none or basic"
      budget: "low"
    implementation:
      - "Add tenant_id column to every table"
      - "PostgreSQL Row-Level Security (RLS) policies"
      - "Middleware injects tenant_id from auth token"
      - "All queries automatically filtered by tenant_id"
    pros: "Cheapest, simplest, easy maintenance"
    cons: "Risk of data leakage if RLS misconfigured, noisy neighbor"

  # Strategy 2: Schema-Level Isolation (Shared DB, separate schemas)
  schema_level:
    when:
      tenants: "10 - 500"
      data_sensitivity: "high"
      compliance: "SOC2 or GDPR"
      budget: "medium"
    implementation:
      - "Each tenant gets own PostgreSQL schema"
      - "Middleware sets search_path based on tenant"
      - "Shared tables (plans, config) in public schema"
      - "Migrations run across all schemas"
    pros: "Better isolation, easier per-tenant backup"
    cons: "Migration complexity, schema limit (~10K in PG)"

  # Strategy 3: Database-Level Isolation (Separate DB per tenant)
  database_level:
    when:
      tenants: "<100 (enterprise clients)"
      data_sensitivity: "critical"
      compliance: "HIPAA, PCI-DSS, or contractual requirement"
      budget: "high"
    implementation:
      - "Each tenant gets own database instance"
      - "Connection routing based on tenant subdomain/token"
      - "Per-tenant backup, restore, and scaling"
      - "Tenant registry in central database"
    pros: "Maximum isolation, per-tenant performance tuning"
    cons: "Most expensive, complex operations, migration overhead"
```

### 18.3 Multi-Tenancy Implementation Rules

```
1. ALWAYS identify tenant from auth token — never from URL or user input
2. ALWAYS enforce tenant isolation at the database level (RLS or separate schema)
3. ALWAYS test cross-tenant data access (should return 403, not 404)
4. NEVER allow tenant A to see/modify tenant B's data
5. ALWAYS include tenant_id in audit logs
6. ALWAYS support tenant-specific configuration (branding, features, limits)
7. ALWAYS test with multiple tenants in staging environment
8. ALWAYS have a "super admin" role that can view across tenants (for support)
```

---

## 19. Feature Flags & Gradual Rollout

### 19.1 Feature Flag Service Selection

```yaml
feature_flags:
  preferred: "Unleash (open-source, self-hosted)"
  alternatives:
    - "LaunchDarkly (managed, enterprise)"
    - "PostHog (open-source, comes with analytics)"
    - "Flagsmith (open-source)"
    - "Custom (simple DB-backed flags for small projects)"

  selection_rule:
    small_project: "Custom DB table (feature_flags: name, enabled, rollout_percentage)"
    medium_project: "Unleash or PostHog (self-hosted)"
    enterprise: "LaunchDarkly (managed, audit trail, compliance)"
```

### 19.2 When to Use Feature Flags

```yaml
use_feature_flags_when:
  - "Rolling out a new feature gradually"
  - "A/B testing different implementations"
  - "Enabling features for specific users/tenants"
  - "Kill switch for features that might cause issues"
  - "Beta testing with select users before general release"
  - "Different feature sets for different pricing tiers"

do_not_use_when:
  - "Simple config changes (use environment variables)"
  - "Permanent differences between environments (use env config)"
  - "One-time data migrations"
```

### 19.3 Gradual Rollout Protocol

```
Phase 1: Internal (0% public)
  → Enable for development team only
  → Test in production environment
  → Duration: 1-3 days

Phase 2: Canary (5-10%)
  → Enable for 5-10% of users randomly
  → Monitor error rates, performance, user feedback
  → Duration: 2-5 days

Phase 3: Partial (25-50%)
  → Increase to 25%, then 50%
  → Monitor at each step
  → Duration: 3-7 days

Phase 4: Full (100%)
  → Enable for all users
  → Monitor for 1 week

Phase 5: Cleanup
  → REMOVE the feature flag from code
  → The feature is now permanent
  → NEVER leave stale flags in code (tech debt)
```

### 19.4 Feature Flag Rules for AI

```
1. ALWAYS clean up flags after full rollout (within 2 weeks)
2. NEVER nest feature flags (flag inside a flag)
3. ALWAYS have a default value (flag off = safe fallback)
4. ALWAYS log flag evaluation (who saw which variant)
5. NEVER use flags for access control (use RBAC instead)
6. ALWAYS document each flag (purpose, owner, expected removal date)
```

---

## 20. Auto-Generated Documentation Rules

### 20.1 Documentation That MUST Be Auto-Generated

```yaml
auto_documentation:
  
  api_docs:
    tool: "Auto-generated from code annotations"
    python_fastapi: "Built-in OpenAPI/Swagger (automatic)"
    nestjs: "@nestjs/swagger decorators"
    spring_boot: "springdoc-openapi"
    go_gin: "swaggo/gin-swagger"
    output: "/docs or /api-docs endpoint"
    rule: "NEVER write API docs manually — they drift from code"

  database_schema:
    tool: "Auto-generated ERD"
    prisma: "prisma-erd-generator"
    sqlalchemy: "eralchemy2"
    typeorm: "typeorm-uml"
    output: "docs/database-schema.png (auto-updated on migration)"

  component_docs:
    tool: "Storybook (frontend components)"
    when: "Projects with 10+ reusable UI components"
    frameworks: "React, Vue, Svelte, Angular"
    rule: "Every shared component gets a Storybook story"

  code_docs:
    tool: "Auto-generated from docstrings/JSDoc"
    python: "Sphinx or pdoc"
    typescript: "TypeDoc"
    go: "godoc"
    java: "Javadoc"
    rule: "Public functions MUST have docstrings"

  changelog:
    tool: "Auto-generated from git commits"
    preferred: "conventional-changelog or auto-changelog"
    format: "Keep a Changelog (keepachangelog.com)"
    rule: "Use conventional commits (feat:, fix:, docs:, etc.)"
```

### 20.2 Documentation Rules for AI

```
1. ALWAYS generate OpenAPI spec from code — never manually
2. ALWAYS add JSDoc/docstring to public functions
3. ALWAYS keep README.md up-to-date with setup instructions
4. ALWAYS generate database ERD after schema changes
5. NEVER create documentation that duplicates what code comments say
6. ALWAYS include example requests/responses in API docs
7. ALWAYS document environment variables in .env.example
```

---

## 21. Load Testing & Performance Strategy

### 21.1 Load Testing Tool Selection

```yaml
load_testing:
  preferred: "k6 (by Grafana Labs)"
  alternatives:
    - "Locust (Python-based, good for complex scenarios)"
    - "Artillery (Node.js, YAML config)"
    - "Apache JMeter (GUI-based, enterprise)"
  
  selection:
    simple_api: "k6 (script-based, CLI, CI/CD friendly)"
    complex_flows: "Locust (Python scripting for complex user journeys)"
    enterprise: "JMeter or Gatling"
```

### 21.2 Performance Baseline (Must Capture Before Launch)

```yaml
performance_baseline:
  metrics_to_capture:
    - "Requests per second (RPS) at normal load"
    - "Response time: p50, p95, p99"
    - "Error rate at normal load"
    - "Max RPS before errors start (breaking point)"
    - "Time to first byte (TTFB)"
    - "Database query time (p50, p95)"
    - "Memory usage under load"
    - "CPU usage under load"

  test_scenarios:
    - name: "Smoke test"
      users: 1-5
      duration: "1 minute"
      purpose: "Verify system works"

    - name: "Average load"
      users: "Expected daily average"
      duration: "10 minutes"
      purpose: "Baseline performance metrics"

    - name: "Peak load"
      users: "Expected peak (2-3x average)"
      duration: "10 minutes"
      purpose: "Verify system handles peaks"

    - name: "Stress test"
      users: "Gradually increase until failure"
      duration: "Until errors > 5%"
      purpose: "Find the breaking point"

    - name: "Soak test"
      users: "Average load"
      duration: "1-4 hours"
      purpose: "Detect memory leaks, connection exhaustion"
```

### 21.3 Performance Budget (Endpoint-Level)

```yaml
performance_budget:
  api_endpoints:
    health_check: "< 50ms p99"
    read_single: "< 200ms p95 (GET /resource/:id)"
    read_list: "< 500ms p95 (GET /resources?page=1)"
    create: "< 300ms p95 (POST /resource)"
    update: "< 300ms p95 (PUT /resource/:id)"
    delete: "< 200ms p95 (DELETE /resource/:id)"
    search: "< 1000ms p95 (GET /search?q=term)"
    auth_login: "< 500ms p95 (POST /auth/login)"
    file_upload: "< 3000ms p95 (POST /upload)"

  frontend:
    first_contentful_paint: "< 1.5s"
    largest_contentful_paint: "< 2.5s"
    time_to_interactive: "< 3.5s"
    cumulative_layout_shift: "< 0.1"
    total_bundle_size: "< 200KB gzipped (initial load)"

  database:
    simple_query: "< 10ms"
    join_query: "< 50ms"
    complex_report: "< 500ms"
    full_text_search: "< 100ms"
```

### 21.4 Load Testing Rules for AI

```
1. ALWAYS run load tests before production deployment
2. ALWAYS establish baseline metrics for comparison
3. NEVER skip soak tests — memory leaks only show up over time
4. ALWAYS test with realistic data volumes (not empty database)
5. ALWAYS include authentication in load test scripts
6. ALWAYS monitor database and cache during load tests (not just app)
7. ALWAYS save load test results for historical comparison
8. IF any endpoint exceeds performance budget → optimize before launch
```

---

## 22. Frontend UI/UX Standards

### 22.1 UI Component Library Selection

```yaml
component_library_selection:

  # Rule 1: Default for most projects
  default:
    library: "shadcn/ui"
    styling: "Tailwind CSS"
    reasoning: "Copy-paste components (not dependency). Full control. Accessible by default (built on Radix). AI generates it well."
    when: "Next.js, React, any TypeScript project"

  # Rule 2: Rapid prototyping, admin dashboards
  when:
    project_type: "admin-panel"
    OR:
      priority: "speed-over-customization"
      project_type: "internal-tool"
  then:
    library: "Ant Design (antd)"
    alternative: "MUI (Material UI)"
    reasoning: "Pre-built complex components (tables, forms, charts). Faster to ship. Less custom design needed."

  # Rule 3: Enterprise, strict design system
  when:
    project_type: "enterprise"
    OR:
      design_system: "Material Design"
      client_requirement: "Google-like UI"
  then:
    library: "MUI (Material UI)"
    reasoning: "Follows Material Design spec. Enterprise-ready. Theming system built-in."

  # Rule 4: Maximum flexibility, headless
  when:
    design_requirement: "highly-custom"
    OR:
      need: "headless-components"
  then:
    library: "Radix UI Primitives + Tailwind CSS"
    reasoning: "Unstyled accessible primitives. Full design control. Zero design opinions."

  # Rule 5: Vue projects
  when:
    framework: "Vue"
    OR:
      framework: "Nuxt"
  then:
    library: "PrimeVue or Vuetify"
    reasoning: "Best Vue-native component libraries."

  non_negotiable:
    - "ALWAYS use TypeScript with component libraries"
    - "ALWAYS import only components you use (tree-shaking)"
    - "NEVER mix two component libraries in one project"
    - "ALWAYS check bundle size impact before adding a library"
```

### 22.2 Design System & Visual Standards

```yaml
design_system:

  color_palette:
    rule: "Define a color system in tailwind.config — never use arbitrary colors"
    structure:
      primary: "Brand color — used for CTAs, active states, links"
      secondary: "Supporting color — used for secondary actions"
      accent: "Highlight color — used sparingly for emphasis"
      neutral: "Gray scale — used for text, borders, backgrounds"
      success: "Green tones — confirmations, success states"
      warning: "Amber/yellow tones — warnings, caution states"
      error: "Red tones — errors, destructive actions"
      background: "Page background (light and dark variants)"
      foreground: "Text color (light and dark variants)"
    
    dark_mode:
      rule: "ALWAYS support dark mode from day 1"
      implementation: "Tailwind dark: prefix + CSS variables"
      storage: "Save preference in localStorage + respect system preference"
      transition: "Add transition-colors duration-200 to body for smooth toggle"

  typography:
    rule: "Use a type scale — never random font sizes"
    recommended_scale:
      xs: "0.75rem (12px) — captions, helper text"
      sm: "0.875rem (14px) — secondary text, labels"
      base: "1rem (16px) — body text (NEVER go below this for body)"
      lg: "1.125rem (18px) — lead text, important body"
      xl: "1.25rem (20px) — section headers"
      2xl: "1.5rem (24px) — page sub-headers"
      3xl: "1.875rem (30px) — page headers"
      4xl: "2.25rem (36px) — hero sections"
      5xl: "3rem (48px) — landing page heroes"
    
    font_selection:
      sans: "Inter, Geist, or DM Sans (modern, clean, highly readable)"
      mono: "JetBrains Mono, Fira Code, or Geist Mono (for code blocks)"
      rule: "Maximum 2 fonts per project — 1 sans + 1 mono"
      loading: "Use next/font (Next.js) or @fontsource for self-hosted fonts. NEVER use Google Fonts CDN."

  spacing:
    rule: "Use Tailwind's spacing scale exclusively — never arbitrary values"
    consistency: "Use multiples of 4px (p-1=4px, p-2=8px, p-4=16px, p-8=32px)"
    section_gaps: "Use py-16 to py-24 between major sections"
    component_gaps: "Use gap-4 to gap-8 between components"
    
  border_radius:
    rule: "Pick ONE radius style and stick with it across the entire app"
    options:
      sharp: "rounded-none or rounded-sm (corporate, enterprise)"
      soft: "rounded-md or rounded-lg (modern, friendly — RECOMMENDED)"
      pill: "rounded-full (playful, mobile-first)"
    consistency: "Buttons, cards, inputs, modals — ALL use the same radius style"

  shadows:
    rule: "Use subtle shadows — never harsh drop shadows"
    recommended:
      cards: "shadow-sm or shadow-md"
      modals: "shadow-lg or shadow-xl"
      dropdowns: "shadow-md"
      hover_lift: "hover:shadow-lg transition-shadow"
    dark_mode: "Reduce shadow intensity in dark mode or use border instead"
```

### 22.3 Animation & Motion Standards

```yaml
animation_rules:

  library_selection:
    preferred: "Framer Motion"
    alternative: "CSS transitions + Tailwind animate"
    simple_cases: "Tailwind transition-* classes (for hover, focus, color changes)"
    complex_cases: "Framer Motion (for page transitions, orchestrated animations, layout animations)"

  core_principles:
    - "Motion should have PURPOSE — guide attention, show relationships, provide feedback"
    - "NEVER animate just for decoration"
    - "Respect prefers-reduced-motion media query"
    - "Animations should be FAST (150-300ms for micro, 300-500ms for page transitions)"
    - "Use ease-out for entrances, ease-in for exits"

  timing:
    micro_interactions: "150-200ms (button press, toggle, checkbox)"
    hover_effects: "150-200ms (color change, scale, shadow)"
    content_transitions: "200-300ms (fade in, slide in, accordion)"
    page_transitions: "300-500ms (route changes, modals opening)"
    loading_animations: "repeat infinite (skeleton pulse, spinner)"
    rule: "NEVER exceed 500ms for any UI animation — it feels sluggish"

  required_animations:
    page_load:
      - "Fade in content (opacity 0→1, translateY 10px→0)"
      - "Stagger children elements (50-100ms delay between items)"
    
    button_interactions:
      - "hover: slight scale (scale-105) + shadow increase"
      - "active/press: scale down slightly (scale-95)"
      - "focus: visible ring (ring-2 ring-primary)"
      - "disabled: opacity-50 cursor-not-allowed"
    
    cards:
      - "hover: lift effect (translateY -2px + shadow-lg)"
      - "OR hover: subtle border color change"
      - "click: scale-[0.98] for tactile feedback"
    
    modals_dialogs:
      - "backdrop: fade in (opacity 0→1)"
      - "modal: scale from 95% to 100% + fade in"
      - "close: reverse animation"
    
    page_transitions:
      - "fade + slight slide (opacity + translateY)"
      - "OR crossfade between pages"
    
    loading_states:
      - "Skeleton screens (pulse animation on gray blocks) — NOT spinners"
      - "Shimmer effect for content loading"
      - "Progress bars for known-duration operations"
    
    notifications_toasts:
      - "Slide in from top-right or bottom-right"
      - "Auto-dismiss with progress bar (3-5 seconds)"
      - "Swipe to dismiss on mobile"

    lists:
      - "Stagger animation on mount (each item 50ms delay)"
      - "AnimatePresence for items being added/removed"

  forbidden:
    - "NEVER use bounce animations on text or important content"
    - "NEVER animate width/height directly (use transform: scale instead)"
    - "NEVER block user interaction during animation"
    - "NEVER use animation delays > 1 second"
    - "NEVER animate background gradients continuously (GPU intensive)"

  framer_motion_patterns:
    fade_in: |
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
    stagger_children: |
      <motion.div
        variants={{
          show: { transition: { staggerChildren: 0.05 } }
        }}
        initial="hidden"
        animate="show"
      >
    exit_animation: |
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
        )}
      </AnimatePresence>
```

### 22.4 Interactive UI Patterns (MUST Implement)

```yaml
interactive_patterns:

  buttons:
    primary:
      - "Solid background with primary color"
      - "White/contrast text"
      - "hover: darken 10% + shadow"
      - "active: scale-95"
      - "disabled: opacity-50 + cursor-not-allowed"
      - "loading: show spinner inside button, disable click"
    secondary:
      - "Border/outline style OR muted background"
      - "hover: fill with light primary tint"
    ghost:
      - "No background, no border"
      - "hover: light background appears"
    destructive:
      - "Red/error color"
      - "Confirmation dialog before destructive action"
    icon_buttons:
      - "Minimum touch target: 44x44px"
      - "Tooltip on hover (desktop)"
    
    rule: "EVERY button must have hover, active, focus, disabled, and loading states"

  forms:
    input_fields:
      - "Clear label above input (not placeholder-only)"
      - "Focus ring with primary color"
      - "Error state: red border + error message below"
      - "Success state: green border/checkmark (after validation)"
      - "Helper text in muted color below input when needed"
      - "Placeholder text as hint, NOT as label"
    
    validation:
      - "Inline validation (validate on blur, show error immediately)"
      - "Error messages: specific ('Password must be 8+ characters'), not generic ('Invalid input')"
      - "Shake animation on submit with errors"
      - "Scroll to first error on form submit"
      - "Disable submit button while submitting (show spinner)"
    
    success_feedback:
      - "Toast notification on successful submit"
      - "OR redirect to success page/state"
      - "NEVER just clear the form silently"

  navigation:
    navbar:
      - "Sticky/fixed on scroll"
      - "Active page indicator (underline, bold, or color)"
      - "Mobile: hamburger menu with slide-in animation"
      - "Smooth scroll for anchor links"
    
    sidebar:
      - "Collapsible with animation"
      - "Active item highlighted"
      - "Tooltips when collapsed (icon-only mode)"
    
    breadcrumbs:
      - "For apps with 3+ levels of navigation depth"
      - "Clickable path segments"

  feedback:
    loading:
      - "Skeleton screens for content areas (NOT spinners)"
      - "Inline spinners only for buttons and small actions"
      - "Progress bars for uploads/long operations"
      - "Optimistic UI updates where possible"
    
    empty_states:
      - "Illustration + clear message + CTA button"
      - "NEVER show a blank white page"
      - "Example: 'No projects yet. Create your first project →'"
    
    error_states:
      - "Friendly error message (not technical)"
      - "Retry button"
      - "Link to support/help"
      - "Custom 404/500 pages with navigation back"
    
    success_states:
      - "Green checkmark animation"
      - "Confetti for major achievements (optional, use sparingly)"
      - "Clear next-step CTA"
    
    toasts:
      - "Position: top-right (desktop), bottom-center (mobile)"
      - "Types: success (green), error (red), warning (amber), info (blue)"
      - "Auto-dismiss: 3-5 seconds"
      - "Stackable (max 3 visible)"
      - "Library: sonner or react-hot-toast (for React)"

  tables_lists:
    tables:
      - "Sticky header on scroll"
      - "Hover highlight on rows"
      - "Sortable columns (click header)"
      - "Pagination or infinite scroll"
      - "Empty state when no data"
      - "Loading skeleton (not spinner)"
      - "Responsive: horizontal scroll on mobile OR card layout"
    
    lists:
      - "Stagger animation on load"
      - "Hover effect on list items"
      - "Swipe actions on mobile (edit, delete)"

  modals_dialogs:
    - "Backdrop blur/overlay"
    - "Close on Escape key"
    - "Close on backdrop click"
    - "Focus trap inside modal"
    - "Scale + fade animation"
    - "Confirmation dialogs for destructive actions"
    - "NEVER nest modals (modal inside modal)"

  scroll:
    - "Smooth scroll behavior (scroll-behavior: smooth in CSS)"
    - "Scroll-to-top button (appears after scrolling down)"
    - "Infinite scroll with loading indicator"
    - "Pull-to-refresh on mobile"
    - "Scroll progress indicator (optional, for long content)"
```

### 22.5 Responsive Design Rules

```yaml
responsive_design:

  approach: "Mobile-first (ALWAYS)"
  
  breakpoints:
    sm: "640px — large phones (landscape)"
    md: "768px — tablets"
    lg: "1024px — laptops"
    xl: "1280px — desktops"
    2xl: "1536px — large screens"
  
  rules:
    - "Design for mobile FIRST, then add styles for larger screens"
    - "Use Tailwind responsive prefixes: sm:, md:, lg:, xl:"
    - "Test on: iPhone SE (375px), iPhone 14 (390px), iPad (768px), Desktop (1440px)"
    - "Touch targets: minimum 44x44px on mobile"
    - "No horizontal scroll on any screen size"
    - "Font size minimum 16px on mobile (prevents iOS zoom on input focus)"
    - "Images: use next/image with responsive sizes"
    - "Grid: 1 column mobile → 2 columns tablet → 3-4 columns desktop"

  layout_patterns:
    mobile:
      - "Single column layout"
      - "Bottom navigation bar (for apps)"
      - "Hamburger menu for navigation"
      - "Full-width cards"
      - "Stacked forms"
    tablet:
      - "2-column grid"
      - "Sidebar visible (collapsible)"
      - "Side-by-side forms (label + input)"
    desktop:
      - "3-4 column grid"
      - "Fixed sidebar"
      - "Multi-panel layouts"
      - "Hover interactions (not available on mobile)"

  testing:
    - "Chrome DevTools device emulation"
    - "Real device testing for touch interactions"
    - "Test landscape and portrait on mobile"
    - "Test with keyboard-only navigation"
```

### 22.6 Accessibility (a11y) Standards

```yaml
accessibility:

  level: "WCAG 2.1 Level AA (minimum)"
  
  mandatory_rules:
    semantic_html:
      - "Use <button> for actions, <a> for navigation — never div/span"
      - "Use heading hierarchy (h1 → h2 → h3) — never skip levels"
      - "Use <nav>, <main>, <aside>, <footer> landmarks"
      - "Use <ul>/<ol> for lists"
    
    keyboard:
      - "ALL interactive elements must be keyboard accessible"
      - "Visible focus indicator (focus-visible:ring-2)"
      - "Tab order must be logical (no tabindex > 0)"
      - "Escape closes modals and dropdowns"
      - "Enter/Space activates buttons"
      - "Arrow keys navigate within components (menus, tabs)"
    
    aria:
      - "aria-label for icon-only buttons"
      - "aria-expanded for collapsible sections"
      - "aria-live='polite' for dynamic content updates"
      - "aria-hidden='true' for decorative elements"
      - "role='alert' for error messages"
    
    color:
      - "Contrast ratio: 4.5:1 for normal text, 3:1 for large text"
      - "NEVER convey information with color alone (add icons/text)"
      - "Test with grayscale filter"
    
    images:
      - "ALL images must have alt text"
      - "Decorative images: alt=''"
      - "Informative images: descriptive alt text"
    
    forms:
      - "Every input must have a <label>"
      - "Error messages linked with aria-describedby"
      - "Required fields marked with aria-required"

  testing_tools:
    - "axe DevTools (browser extension)"
    - "Lighthouse accessibility audit"
    - "Screen reader testing (NVDA on Windows, VoiceOver on Mac)"
```

### 22.7 State Management Selection

```yaml
state_management:

  # Rule 1: Simple local state
  when:
    scope: "single-component"
    complexity: "low"
  then:
    solution: "React useState / useReducer"
    reasoning: "No library needed for simple local state"

  # Rule 2: Shared state across few components  
  when:
    scope: "2-5 components sharing state"
    complexity: "medium"
  then:
    solution: "React Context + useReducer"
    reasoning: "Built-in, no dependency. Good for theme, auth, locale."
    warning: "DON'T use Context for frequently updating state (causes re-renders)"

  # Rule 3: Complex client state, many components
  when:
    scope: "app-wide client state"
    complexity: "high"
    OR:
      frequent_updates: true
      multiple_stores: true
  then:
    preferred: "Zustand"
    alternative: "Jotai (atomic state)"
    avoid: "Redux (too much boilerplate unless team already uses it)"
    reasoning: "Zustand is tiny (1KB), simple API, no boilerplate, great DevTools"

  # Rule 4: Server state (API data)
  when:
    type: "server-state"
    data_source: "API"
  then:
    solution: "TanStack Query (React Query)"
    reasoning: "Handles caching, refetching, invalidation, optimistic updates. NEVER manually manage API state with useState."
    rules:
      - "ALWAYS use React Query for API calls"
      - "NEVER store API response in useState"
      - "Use staleTime and cacheTime appropriately"
      - "Use optimistic updates for mutations"

  # Rule 5: Form state
  when:
    type: "form-state"
  then:
    solution: "React Hook Form + Zod (validation)"
    reasoning: "Minimal re-renders. Schema-based validation. TypeScript-first."
    rules:
      - "ALWAYS use react-hook-form for forms with 3+ fields"
      - "ALWAYS use Zod for validation schemas"
      - "NEVER use controlled inputs for large forms (performance)"

  summary:
    local_state: "useState"
    shared_simple: "Context"
    shared_complex: "Zustand"
    server_data: "TanStack Query"
    forms: "React Hook Form + Zod"
    url_state: "nuqs or useSearchParams"
```

### 22.8 Modern UI Patterns (Implement by Default)

```yaml
modern_ui_patterns:

  dark_mode:
    implementation: "Tailwind dark: prefix + next-themes (Next.js)"
    rule: "ALWAYS implement dark mode from day 1 — retrofitting is painful"
    default: "System preference (prefers-color-scheme)"
    toggle: "Sun/moon icon in navbar"
    storage: "localStorage + respect system preference"

  skeleton_loading:
    rule: "ALWAYS use skeleton screens for content loading"
    never: "NEVER show spinner for page/section loading"
    spinner_ok: "Spinners only for: button loading, inline actions, small areas"
    implementation: "Tailwind animate-pulse on gray rectangles matching content layout"

  optimistic_updates:
    rule: "For user-initiated mutations (like, save, delete), update UI immediately"
    rollback: "If server returns error, rollback and show toast"
    implementation: "TanStack Query optimistic update pattern"

  infinite_scroll:
    when: "Lists with 20+ items"
    implementation: "Intersection Observer + TanStack Query useInfiniteQuery"
    fallback: "Show 'Load more' button as fallback"
    rule: "ALWAYS show loading indicator at bottom during fetch"

  search:
    debounce: "300ms debounce on search input"
    feedback: "Show search results count"
    empty: "Show 'No results found' with suggestions"
    highlight: "Highlight matching text in results"
    keyboard: "Cmd+K / Ctrl+K for global search (optional)"

  copy_to_clipboard:
    feedback: "Show 'Copied!' tooltip for 2 seconds"
    animation: "Icon changes from copy to checkmark"

  file_upload:
    drag_drop: "Drag-and-drop zone with visual feedback"
    preview: "Show image preview before upload"
    progress: "Upload progress bar"
    validation: "File type and size validation with clear error"

  data_visualization:
    library: "Recharts (React) or Chart.js"
    rule: "Charts must be responsive and have tooltips"
    colors: "Use app's color palette for chart colors"

  command_palette:
    when: "Apps with 10+ navigation items or actions"
    library: "cmdk (by pacocoursey)"
    trigger: "Cmd+K / Ctrl+K"
    rule: "Include: navigation, actions, theme toggle, search"
```

### 22.9 Frontend Performance Rules

```yaml
frontend_performance:

  core_web_vitals:
    LCP: "< 2.5s (Largest Contentful Paint)"
    FID: "< 100ms (First Input Delay)"
    CLS: "< 0.1 (Cumulative Layout Shift)"
    FCP: "< 1.5s (First Contentful Paint)"
    TTFB: "< 800ms (Time to First Byte)"

  bundle_size:
    initial_load: "< 200KB gzipped"
    per_route_chunk: "< 50KB gzipped"
    total_js: "< 500KB gzipped"
    rule: "Analyze with next/bundle-analyzer or source-map-explorer"
    
  optimization:
    images:
      - "ALWAYS use next/image (Next.js) or optimized images"
      - "Use WebP/AVIF format"
      - "Lazy load below-the-fold images"
      - "Add width/height to prevent CLS"
      - "Use blur placeholder for large images"
    
    code_splitting:
      - "Dynamic imports for heavy components: dynamic(() => import(...))"
      - "Lazy load modals, charts, editors, maps"
      - "Route-based code splitting (automatic in Next.js)"
    
    rendering:
      - "Use React.memo for expensive components"
      - "Use useMemo/useCallback only when measured benefit"
      - "Virtualize long lists (tanstack/react-virtual)"
      - "Debounce/throttle event handlers (scroll, resize, input)"
    
    fonts:
      - "Self-host fonts (next/font or @fontsource)"
      - "Use font-display: swap"
      - "Subset fonts to used characters only"
    
    third_party:
      - "Lazy load analytics, chat widgets, social embeds"
      - "Use Partytown for third-party scripts (optional)"
      - "NEVER load third-party scripts synchronously"

  monitoring:
    - "Use Vercel Analytics or web-vitals library"
    - "Monitor Core Web Vitals in production"
    - "Set up alerts for performance regression"
```

### 22.10 Frontend Pre-Approved Dependencies

```yaml
frontend_dependencies:

  core:
    - "react, react-dom, next"
    - "typescript"
    - "tailwindcss, postcss, autoprefixer"

  ui_components:
    - "shadcn/ui (copy-paste components)"
    - "@radix-ui/* (headless primitives)"
    - "lucide-react (icons)"
    - "class-variance-authority (cva) — component variants"
    - "clsx + tailwind-merge — className merging"

  animation:
    - "framer-motion"
    - "tailwindcss-animate"

  state_data:
    - "@tanstack/react-query (server state)"
    - "zustand (client state, when needed)"
    - "nuqs (URL state)"

  forms:
    - "react-hook-form"
    - "zod (validation)"
    - "@hookform/resolvers"

  utilities:
    - "date-fns (date formatting — NOT moment.js)"
    - "sonner (toast notifications)"
    - "cmdk (command palette)"
    - "next-themes (dark mode)"
    - "sharp (image optimization — server-side)"

  charts:
    - "recharts"

  tables:
    - "@tanstack/react-table"

  banned:
    - "moment.js (use date-fns — moment is 300KB)"
    - "lodash (full package — use individual imports if needed)"
    - "jQuery (never — use React patterns)"
    - "Bootstrap CSS (conflicts with Tailwind)"
    - "styled-components (use Tailwind instead)"
    - "Redux Toolkit (use Zustand — less boilerplate)"
    - "axios (use native fetch — it's built into Next.js with caching)"
```

---

## 23. Backend API Design Patterns

### 23.1 REST API Conventions

```yaml
rest_conventions:

  url_structure:
    rule: "Use nouns (not verbs), plural, lowercase, kebab-case"
    examples:
      good:
        - "GET /api/v1/users"
        - "GET /api/v1/users/:id"
        - "POST /api/v1/users"
        - "PUT /api/v1/users/:id"
        - "DELETE /api/v1/users/:id"
        - "GET /api/v1/users/:id/orders"
        - "GET /api/v1/order-items"
      bad:
        - "GET /api/v1/getUsers"
        - "POST /api/v1/createUser"
        - "GET /api/v1/user_list"
        - "DELETE /api/v1/removeUser/5"

  http_methods:
    GET: "Read — never modify data. Must be idempotent."
    POST: "Create — returns 201 with created resource."
    PUT: "Full update — replace entire resource."
    PATCH: "Partial update — modify specific fields."
    DELETE: "Remove — returns 204 (no content) or 200."

  status_codes:
    success:
      200: "OK — general success (GET, PUT, PATCH)"
      201: "Created — resource created (POST)"
      204: "No Content — successful delete"
    client_errors:
      400: "Bad Request — validation error, malformed input"
      401: "Unauthorized — not authenticated (no/invalid token)"
      403: "Forbidden — authenticated but no permission"
      404: "Not Found — resource doesn't exist"
      409: "Conflict — duplicate resource, version conflict"
      422: "Unprocessable Entity — valid JSON but business logic rejected"
      429: "Too Many Requests — rate limit exceeded"
    server_errors:
      500: "Internal Server Error — unexpected error (never expose details)"
      502: "Bad Gateway — upstream service failed"
      503: "Service Unavailable — overloaded or maintenance"
```

### 23.2 Standard API Error Response Format

```yaml
error_format:
  standard: "RFC 7807 Problem Details (recommended)"
  
  structure:
    type: "URI identifying the error type"
    title: "Short human-readable summary"
    status: "HTTP status code"
    detail: "Human-readable explanation"
    instance: "URI of the specific occurrence"
    errors: "Array of field-level errors (for validation)"
    timestamp: "ISO 8601 timestamp"
    trace_id: "Request trace ID for debugging"

  examples:
    validation_error: |
      {
        "type": "https://api.example.com/errors/validation",
        "title": "Validation Error",
        "status": 422,
        "detail": "One or more fields failed validation.",
        "timestamp": "2026-02-10T12:00:00Z",
        "trace_id": "req_abc123",
        "errors": [
          { "field": "email", "message": "Must be a valid email address" },
          { "field": "password", "message": "Must be at least 8 characters" }
        ]
      }
    
    not_found: |
      {
        "type": "https://api.example.com/errors/not-found",
        "title": "Resource Not Found",
        "status": 404,
        "detail": "User with ID 'xyz' does not exist.",
        "timestamp": "2026-02-10T12:00:00Z",
        "trace_id": "req_def456"
      }
    
    server_error: |
      {
        "type": "https://api.example.com/errors/internal",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred. Please try again later.",
        "timestamp": "2026-02-10T12:00:00Z",
        "trace_id": "req_ghi789"
      }

  rules:
    - "NEVER expose stack traces or internal details in production"
    - "ALWAYS include trace_id for debugging"
    - "ALWAYS use consistent error format across ALL endpoints"
    - "ALWAYS return appropriate HTTP status code (not 200 with error body)"
```

### 23.3 Pagination, Filtering & Sorting

```yaml
pagination:
  preferred: "Cursor-based (for infinite scroll, real-time data)"
  alternative: "Offset-based (for traditional page numbers)"

  cursor_based:
    request: "GET /api/v1/users?cursor=abc123&limit=20"
    response: |
      {
        "data": [...],
        "pagination": {
          "next_cursor": "def456",
          "has_more": true,
          "limit": 20
        }
      }
    when: "Large datasets, real-time feeds, infinite scroll"

  offset_based:
    request: "GET /api/v1/users?page=2&per_page=20"
    response: |
      {
        "data": [...],
        "pagination": {
          "page": 2,
          "per_page": 20,
          "total": 156,
          "total_pages": 8
        }
      }
    when: "Admin dashboards, reports, traditional page navigation"

  defaults:
    per_page: 20
    max_per_page: 100
    rule: "ALWAYS enforce max_per_page — never let client request unlimited"

filtering:
  format: "Query parameters with field names"
  examples:
    - "GET /api/v1/users?status=active"
    - "GET /api/v1/users?role=admin&status=active"
    - "GET /api/v1/orders?created_after=2026-01-01"
    - "GET /api/v1/products?price_min=100&price_max=500"
    - "GET /api/v1/users?search=amaan"

sorting:
  format: "sort=field:direction"
  examples:
    - "GET /api/v1/users?sort=created_at:desc"
    - "GET /api/v1/products?sort=price:asc"
    - "GET /api/v1/users?sort=name:asc,created_at:desc"
  rule: "ALWAYS validate sort fields — never allow sorting on unindexed columns"
```

### 23.4 API Rate Limiting

```yaml
rate_limiting:
  rule: "EVERY public endpoint MUST be rate limited"
  
  tiers:
    public_endpoints: "60 requests/minute per IP"
    authenticated_endpoints: "120 requests/minute per user"
    auth_endpoints: "10 requests/minute per IP (login, register, password reset)"
    upload_endpoints: "10 requests/minute per user"
    admin_endpoints: "300 requests/minute per user"
    webhook_endpoints: "100 requests/minute per source IP"

  headers:
    - "X-RateLimit-Limit: 120"
    - "X-RateLimit-Remaining: 85"
    - "X-RateLimit-Reset: 1707580800"
    - "Retry-After: 30 (only when 429 is returned)"

  implementation:
    fastapi: "slowapi or custom middleware with Redis"
    nestjs: "@nestjs/throttler"
    express: "express-rate-limit + rate-limit-redis"
    spring: "bucket4j or resilience4j"
    go: "golang.org/x/time/rate or tollbooth"

  storage: "Redis (for distributed rate limiting across instances)"
```

---

## 24. Authentication Flow Patterns

### 24.1 JWT Authentication (Default)

```yaml
jwt_auth:
  when: "SPAs, mobile apps, stateless APIs"

  token_pair:
    access_token:
      lifetime: "15 minutes"
      storage: "Memory (JavaScript variable) — NEVER localStorage"
      payload: "user_id, email, role, permissions"
      size_limit: "Keep < 1KB"
    
    refresh_token:
      lifetime: "7 days (30 days for 'remember me')"
      storage: "HTTP-only, Secure, SameSite=Strict cookie"
      rotation: "Issue new refresh token on each use (rotate)"
      family_detection: "If old refresh token is reused → revoke ALL tokens for that user (compromise detected)"

  flow:
    login: |
      1. User sends email + password
      2. Server validates credentials
      3. Server returns access_token (in body) + refresh_token (in cookie)
      4. Client stores access_token in memory
    
    authenticated_request: |
      1. Client sends access_token in Authorization: Bearer header
      2. Server validates token signature + expiry
      3. If valid → process request
      4. If expired → client calls refresh endpoint
    
    refresh: |
      1. Client calls POST /auth/refresh (cookie sent automatically)
      2. Server validates refresh_token
      3. Server issues NEW access_token + NEW refresh_token (rotation)
      4. Old refresh_token is invalidated
    
    logout: |
      1. Client calls POST /auth/logout
      2. Server blacklists refresh_token
      3. Client clears access_token from memory
      4. Server clears refresh_token cookie

  security_rules:
    - "NEVER store access_token in localStorage or sessionStorage"
    - "ALWAYS use HTTP-only cookies for refresh tokens"
    - "ALWAYS rotate refresh tokens on use"
    - "ALWAYS blacklist tokens on logout"
    - "ALWAYS validate token signature with a strong secret (RS256 preferred over HS256)"
    - "NEVER put sensitive data in JWT payload (it's base64, not encrypted)"
    - "ALWAYS check token expiry server-side (don't trust client)"
```

### 24.2 OAuth2 / Social Login

```yaml
oauth2:
  when: "Apps that need Google/GitHub/Apple login"
  
  providers:
    google: "Most common, supports OpenID Connect"
    github: "Developer-focused apps"
    apple: "Required for iOS apps with social login"
    microsoft: "Enterprise apps"

  implementation:
    nextjs: "NextAuth.js (Auth.js) — handles all providers"
    fastapi: "authlib + httpx"
    nestjs: "@nestjs/passport + passport-google-oauth20"
    spring: "Spring Security OAuth2 Client"

  flow: "Authorization Code Flow with PKCE (ALWAYS — never Implicit Flow)"
  
  rules:
    - "ALWAYS use Authorization Code Flow + PKCE"
    - "NEVER use Implicit Flow (deprecated, insecure)"
    - "ALWAYS validate state parameter (CSRF protection)"
    - "ALWAYS link social accounts to internal user record"
    - "ALWAYS allow users to set a password even after social login"
    - "ALWAYS handle account linking (same email, different providers)"
```

### 24.3 Multi-Factor Authentication (MFA)

```yaml
mfa:
  when_required:
    - "Any app handling financial data"
    - "Any app with PII/health data"
    - "Admin panels"
    - "Any compliance requirement (SOC2, HIPAA, PCI)"
  
  methods:
    totp: "Time-based OTP (Google Authenticator, Authy) — RECOMMENDED"
    sms: "SMS OTP — fallback only (SIM swap attacks)"
    email: "Email OTP — acceptable for low-risk apps"
    webauthn: "Hardware key / biometric — highest security"
  
  implementation:
    preferred: "TOTP with QR code setup"
    library_python: "pyotp"
    library_node: "otpauth or speakeasy"
    backup_codes: "Generate 10 backup codes on MFA setup, hash and store them"

  rules:
    - "ALWAYS offer recovery codes when enabling MFA"
    - "ALWAYS hash backup codes (treat like passwords)"
    - "ALWAYS rate-limit MFA attempts (5 attempts, then lockout)"
    - "NEVER send MFA secret in plaintext after initial setup"
```

---

## 25. Git Workflow & Branching Strategy

### 25.1 Branch Strategy

```yaml
git_branching:
  strategy: "GitHub Flow (simplified) for most projects"
  
  branches:
    main:
      - "Production-ready code ONLY"
      - "Protected — no direct pushes"
      - "All changes via Pull Request"
      - "CI must pass before merge"
    
    develop:
      - "Optional — use for projects with staging environment"
      - "Integration branch for features"
      - "Auto-deploys to staging"
    
    feature:
      format: "feature/short-description"
      examples: "feature/user-auth, feature/payment-integration"
      rule: "Branch from main (or develop), merge back via PR"
      lifetime: "Max 1 week — break large features into smaller PRs"
    
    fix:
      format: "fix/short-description"
      examples: "fix/login-redirect, fix/cart-total-calculation"
      rule: "For bug fixes"
    
    hotfix:
      format: "hotfix/short-description"
      examples: "hotfix/security-patch, hotfix/payment-crash"
      rule: "Critical production fixes — branch from main, merge to main + develop"
    
    chore:
      format: "chore/short-description"
      examples: "chore/update-dependencies, chore/ci-pipeline"
      rule: "Non-feature work — config, dependencies, CI/CD"
```

### 25.2 Commit Message Convention

```yaml
commit_convention:
  standard: "Conventional Commits"
  
  format: "<type>(<scope>): <description>"
  
  types:
    feat: "New feature"
    fix: "Bug fix"
    docs: "Documentation only"
    style: "Formatting (no code change)"
    refactor: "Code restructure (no behavior change)"
    perf: "Performance improvement"
    test: "Adding or fixing tests"
    chore: "Build, CI, dependencies, configs"
    ci: "CI/CD pipeline changes"
    revert: "Revert a previous commit"
  
  examples:
    - "feat(auth): add JWT refresh token rotation"
    - "fix(cart): correct total calculation with discounts"
    - "docs(api): update authentication endpoint docs"
    - "refactor(users): extract validation into separate module"
    - "chore(deps): update Next.js to 15.1"
    - "test(orders): add integration tests for checkout flow"
    - "perf(search): add database index for product search"

  rules:
    - "Use imperative mood ('add' not 'added' or 'adds')"
    - "First line max 72 characters"
    - "Add body for complex changes (blank line after subject)"
    - "Reference issue numbers: 'fix(auth): resolve login bug (#42)'"
    - "NEVER use vague messages ('fix stuff', 'update code', 'wip')"
```

### 25.3 Pull Request Rules

```yaml
pull_requests:
  template: |
    ## What does this PR do?
    [Brief description]

    ## Type of change
    - [ ] New feature
    - [ ] Bug fix
    - [ ] Refactoring
    - [ ] Documentation
    - [ ] CI/CD

    ## Checklist
    - [ ] Tests added/updated
    - [ ] Documentation updated
    - [ ] No console.log or debug code
    - [ ] No hardcoded secrets
    - [ ] Linter passes
    - [ ] Self-reviewed the code

  rules:
    - "Max 400 lines changed per PR (break large features into multiple PRs)"
    - "Every PR must have a description"
    - "Every PR must pass CI before merge"
    - "Squash merge to main (clean history)"
    - "Delete branch after merge"
    - "At least 1 review for team projects"
    - "Self-review for solo projects (read your own diff before merge)"
```

### 25.4 .gitignore Essentials

```yaml
gitignore_must_include:
  always:
    - "node_modules/"
    - ".env"
    - ".env.local"
    - ".env.*.local"
    - "__pycache__/"
    - "*.pyc"
    - ".venv/"
    - "dist/"
    - "build/"
    - ".next/"
    - "coverage/"
    - "*.log"
    - ".DS_Store"
    - "Thumbs.db"
    - ".idea/"
    - ".vscode/settings.json"
    - "*.sqlite3"
  
  never_commit:
    - "Secrets, API keys, passwords"
    - "Private keys (.pem, .key)"
    - "Database dumps"
    - "Large binary files"
    - "IDE personal settings"
```

---

## 26. Real-Time Features

### 26.1 Technology Selection

```yaml
realtime_selection:

  # Option 1: WebSocket
  websocket:
    when:
      - "Bi-directional communication needed"
      - "Chat applications"
      - "Collaborative editing (like Google Docs)"
      - "Gaming"
      - "Live dashboards with user interactions"
    library:
      node: "Socket.IO or ws"
      python: "FastAPI WebSocket or Django Channels"
      go: "gorilla/websocket"
    scaling: "Redis Pub/Sub for multi-instance WebSocket"

  # Option 2: Server-Sent Events (SSE)
  sse:
    when:
      - "Server-to-client only (one-way)"
      - "Live notifications"
      - "Real-time feeds (news, social)"
      - "Live progress updates"
      - "Stock tickers"
    advantage: "Works over HTTP, auto-reconnect, simpler than WebSocket"
    limitation: "One-way only (server → client)"

  # Option 3: Polling
  polling:
    when:
      - "Simple cases, low frequency updates"
      - "Checking order status every 30 seconds"
      - "Fallback when WebSocket/SSE not available"
    interval: "10-30 seconds (never < 5 seconds)"
    rule: "Use long-polling or SSE instead if possible"

  # Option 4: Third-party services
  managed:
    pusher: "Easiest to implement, managed WebSocket"
    ably: "Enterprise-grade, global edge network"
    supabase_realtime: "If already using Supabase"
    firebase: "If already in Google ecosystem"
    when: "Don't want to manage WebSocket infrastructure"

  decision_tree:
    bidirectional_needed:
      yes: "WebSocket (Socket.IO)"
      no:
        server_to_client_only:
          yes: "SSE"
          no:
            low_frequency:
              yes: "Polling (10-30s interval)"
              no: "WebSocket"
```

### 26.2 Real-Time Implementation Rules

```yaml
realtime_rules:
  - "ALWAYS authenticate WebSocket connections (verify token on connect)"
  - "ALWAYS implement heartbeat/ping-pong (detect dead connections)"
  - "ALWAYS handle reconnection with exponential backoff"
  - "ALWAYS use rooms/channels to limit message scope"
  - "ALWAYS validate incoming WebSocket messages (same as HTTP input validation)"
  - "ALWAYS rate-limit WebSocket messages per client"
  - "NEVER broadcast sensitive data to all connected clients"
  - "ALWAYS use Redis Pub/Sub for multi-server WebSocket scaling"
  - "ALWAYS implement graceful degradation (fallback to polling if WS fails)"
```

---

## 27. File Storage & CDN Strategy

### 27.1 Storage Provider Selection

```yaml
file_storage:

  # Option 1: S3-compatible (default)
  s3_compatible:
    providers:
      aws_s3: "Default for AWS projects"
      cloudflare_r2: "No egress fees — RECOMMENDED for cost savings"
      minio: "Self-hosted S3-compatible (for on-prem)"
      digitalocean_spaces: "Simple, affordable"
    when: "Any project with file uploads"

  # Option 2: Local filesystem
  local:
    when: "Development only, or single-server deployments"
    warning: "NEVER use local storage in production with multiple servers"

  rules:
    - "ALWAYS use S3-compatible storage in production"
    - "ALWAYS generate unique filenames (UUID + original extension)"
    - "NEVER use user-provided filenames directly (path traversal risk)"
    - "ALWAYS validate file type on server (not just extension — check magic bytes)"
    - "ALWAYS enforce max file size (default: 10MB, configurable)"
    - "ALWAYS scan uploaded files for malware (ClamAV or cloud-based)"
    - "ALWAYS serve files via CDN (not directly from storage)"
    - "ALWAYS set correct Content-Type and Content-Disposition headers"
    - "ALWAYS use pre-signed URLs for private files (expiry: 1 hour)"
```

### 27.2 CDN Strategy

```yaml
cdn:
  preferred: "Cloudflare (free tier is generous)"
  alternatives: ["AWS CloudFront", "Vercel Edge", "Bunny CDN"]

  what_to_cache:
    - "Static assets (CSS, JS, images, fonts)"
    - "User-uploaded images (after processing)"
    - "API responses that rarely change (cache-control headers)"
    - "Public pages (SSG/ISR in Next.js)"

  what_not_to_cache:
    - "Authenticated API responses"
    - "Real-time data"
    - "User-specific content"

  image_optimization:
    - "Auto-convert to WebP/AVIF"
    - "Resize on-the-fly (via CDN or sharp)"
    - "Generate thumbnails on upload"
    - "Use responsive images (srcset)"
    - "Lazy load below-the-fold images"
```

---

## 28. Email & Notification System

### 28.1 Email Provider Selection

```yaml
email_providers:
  transactional:
    preferred: "Resend (modern API, great DX, React Email templates)"
    alternatives:
      - "SendGrid (large scale, established)"
      - "Postmark (best deliverability)"
      - "AWS SES (cheapest at scale, more setup)"
    
  selection:
    small_project: "Resend (free tier: 100 emails/day)"
    medium_project: "Resend or SendGrid"
    enterprise: "AWS SES + custom SMTP"
    
  marketing_emails:
    provider: "Separate from transactional — use Mailchimp, ConvertKit, or Loops"
    rule: "NEVER mix transactional and marketing emails on same domain"
```

### 28.2 Email Types & Templates

```yaml
email_templates:
  required:
    - "Welcome / verify email"
    - "Password reset"
    - "Login notification (new device)"
    - "Invoice / payment receipt"
    - "Account deactivation"
  
  optional:
    - "Weekly digest"
    - "Feature announcement"
    - "Inactivity reminder"
  
  implementation:
    preferred: "React Email (JSX templates — works with Resend)"
    alternative: "MJML (responsive email framework)"
    rule: "NEVER use plain HTML for emails — use a framework that handles email client quirks"
  
  rules:
    - "ALWAYS include unsubscribe link (CAN-SPAM compliance)"
    - "ALWAYS use a queue for sending (never send synchronously in API request)"
    - "ALWAYS include plain-text version alongside HTML"
    - "ALWAYS use SPF, DKIM, DMARC on sending domain"
    - "ALWAYS track delivery, open, bounce rates"
    - "NEVER include sensitive data in email (no passwords, tokens, full credit card)"
```

### 28.3 Push Notification Strategy

```yaml
notifications:
  channels:
    in_app: "Always — database-backed notification feed"
    email: "Important events (order confirmation, password reset)"
    push: "Mobile apps — time-sensitive (new message, delivery update)"
    sms: "Critical only (OTP, account security alerts)"
    whatsapp: "If targeting regions where WhatsApp is primary (Middle East, South Asia)"

  in_app_implementation:
    storage: "PostgreSQL table: notifications (id, user_id, type, title, body, read, created_at)"
    delivery: "SSE or WebSocket for real-time"
    ui: "Bell icon with unread count badge"
    
  rules:
    - "ALWAYS let users control notification preferences per channel"
    - "ALWAYS batch notifications (don't send 10 emails in 1 minute)"
    - "ALWAYS use a queue (BullMQ, Celery) for notification delivery"
    - "ALWAYS have a notification settings page"
    - "NEVER wake users at night (respect timezone)"
```

---

## 29. Database Migration Strategy

### 29.1 Migration Rules

```yaml
database_migrations:
  tool_selection:
    python_sqlalchemy: "Alembic"
    python_django: "Django migrations (built-in)"
    typescript_prisma: "Prisma Migrate"
    typescript_drizzle: "Drizzle Kit"
    typescript_typeorm: "TypeORM migrations"
    go: "golang-migrate or goose"
    java_spring: "Flyway or Liquibase"

  safety_rules:
    - "ALWAYS test migrations on a copy of production data before running on production"
    - "ALWAYS make migrations reversible (include down/rollback)"
    - "ALWAYS back up database before running migrations in production"
    - "NEVER drop a column in the same release that stops using it"
    - "NEVER rename a column directly — add new, migrate data, remove old (3-step)"
    - "NEVER modify a migration that has already been applied"
    - "ALWAYS run migrations in a transaction (if supported)"
    - "ALWAYS review migration SQL before applying to production"
```

### 29.2 Safe Column/Table Changes

```yaml
safe_migration_patterns:

  adding_column:
    safe: true
    rule: "Add with DEFAULT value or as NULLABLE. Never add NOT NULL without default."

  removing_column:
    safe: "Only with 3-step process"
    steps:
      release_1: "Stop reading from the column in code"
      release_2: "Stop writing to the column in code"  
      release_3: "Drop the column in migration"
    rule: "NEVER drop a column that code still references"

  renaming_column:
    safe: "Only with 3-step process"
    steps:
      release_1: "Add new column, write to both old and new"
      release_2: "Migrate data, read from new column only"
      release_3: "Drop old column"
    rule: "NEVER rename directly — it breaks running instances"

  adding_index:
    safe: true
    rule: "Use CREATE INDEX CONCURRENTLY (PostgreSQL) to avoid table lock"

  changing_type:
    safe: "Depends on the change"
    safe_changes: "varchar(50) → varchar(100), int → bigint"
    unsafe_changes: "varchar → int, text → boolean"
    rule: "If unsafe, use 3-step process like renaming"

  adding_table:
    safe: true
    rule: "No issues — just create"

  dropping_table:
    safe: "Only after all code references removed"
    rule: "Verify zero queries hitting the table before dropping"
```

### 29.3 Seed Data

```yaml
seed_data:
  when:
    - "Development environment setup"
    - "Testing (known state)"
    - "Demo environments"
    - "Initial system data (roles, permissions, categories)"

  rules:
    - "ALWAYS separate seed data from migrations"
    - "ALWAYS make seeds idempotent (safe to run multiple times)"
    - "NEVER seed production with fake data"
    - "ALWAYS seed system/reference data in production (roles, permissions, settings)"
    - "ALWAYS use factories for test data (not hardcoded)"
    - "NEVER put real email addresses in seed data"
```

---

## 30. Error Handling Patterns

### 30.1 Backend Error Handling

```yaml
backend_error_handling:

  global_error_handler:
    rule: "EVERY application MUST have a global error handler"
    purpose: "Catch unhandled errors, log them, return safe response"
    
    pattern: |
      1. Catch the error
      2. Identify error type (validation, auth, business logic, unexpected)
      3. Log full error details (stack trace, request context, user ID)
      4. Return safe error response (no internal details)
      5. Send alert if critical (500 errors, rate > threshold)

  error_types:
    validation_error:
      http_code: 422
      log_level: "WARN"
      alert: false
      action: "Return field-level errors"
    
    authentication_error:
      http_code: 401
      log_level: "WARN"
      alert: "If rate > 10/min from same IP (brute force)"
      action: "Return generic 'Invalid credentials'"
    
    authorization_error:
      http_code: 403
      log_level: "WARN"
      alert: "If user tries to access another user's data"
      action: "Return 'Forbidden' — log the attempt"
    
    not_found:
      http_code: 404
      log_level: "DEBUG"
      alert: false
      action: "Return 'Resource not found'"
    
    business_logic_error:
      http_code: 409 or 422
      log_level: "INFO"
      alert: false
      action: "Return specific business error message"
    
    rate_limit:
      http_code: 429
      log_level: "WARN"
      alert: "If same user/IP consistently hits limit"
      action: "Return 'Too many requests' with Retry-After header"
    
    unexpected_error:
      http_code: 500
      log_level: "ERROR"
      alert: true
      action: "Log EVERYTHING, return generic message, alert team"

  rules:
    - "NEVER return stack traces in production responses"
    - "ALWAYS log the full error server-side"
    - "ALWAYS return consistent error format (Section 23.2)"
    - "ALWAYS include trace_id in error responses AND logs"
    - "ALWAYS handle database connection errors gracefully"
    - "ALWAYS handle third-party API failures with circuit breaker pattern"
```

### 30.2 Frontend Error Handling

```yaml
frontend_error_handling:

  react_error_boundary:
    rule: "ALWAYS wrap app in an Error Boundary"
    scope:
      - "Root level (catches everything)"
      - "Per-route level (isolates page crashes)"
      - "Per-widget level (isolates component crashes)"
    fallback: "Show friendly error UI with retry button"

  api_error_handling:
    rule: "ALWAYS handle API errors in a centralized place"
    pattern: |
      1. TanStack Query onError callback (global)
      2. Map HTTP status to user-friendly message
      3. Show toast notification for most errors
      4. Redirect to login for 401
      5. Show inline error for form validation (422)
      6. Show full-page error for 500

  error_messages:
    user_facing:
      - "Something went wrong. Please try again."
      - "Your session has expired. Please log in again."
      - "This action is not allowed."
      - "We couldn't find what you're looking for."
      - "Too many attempts. Please wait a moment."
    rule: "NEVER show technical error messages to users"

  offline_handling:
    - "Detect offline status (navigator.onLine + event listeners)"
    - "Show offline banner"
    - "Queue failed requests for retry"
    - "Show cached data when available"
```

---

## 31. Background Jobs & Task Queues

### 31.1 Queue System Selection

```yaml
job_queue_selection:

  node_typescript:
    preferred: "BullMQ + Redis"
    alternative: "Agenda (MongoDB-based)"
    reasoning: "BullMQ is the standard for Node.js job queues. Redis-backed, reliable."

  python:
    preferred: "Celery + Redis"
    alternative: "Dramatiq, Huey, or ARQ"
    reasoning: "Celery is battle-tested. Supports scheduling, retries, monitoring."

  go:
    preferred: "Asynq (Redis-based)"
    alternative: "Temporal (complex workflows)"

  java:
    preferred: "Spring Batch or Quartz"

  managed:
    aws: "SQS + Lambda"
    gcp: "Cloud Tasks"
    general: "Trigger.dev (modern, TypeScript-native)"
```

### 31.2 Common Job Patterns

```yaml
job_patterns:
  email_sending:
    queue: "email"
    priority: "high"
    retry: 3
    delay: "none"
    timeout: "30 seconds"

  image_processing:
    queue: "media"
    priority: "medium"
    retry: 2
    delay: "none"
    timeout: "2 minutes"

  report_generation:
    queue: "reports"
    priority: "low"
    retry: 1
    delay: "none"
    timeout: "10 minutes"

  scheduled_cleanup:
    queue: "cron"
    schedule: "0 3 * * * (3 AM daily)"
    retry: 1
    timeout: "30 minutes"

  webhook_delivery:
    queue: "webhooks"
    priority: "high"
    retry: 5
    retry_delay: "exponential (1m, 5m, 30m, 2h, 24h)"
    timeout: "30 seconds"
```

### 31.3 Job Queue Rules

```yaml
job_rules:
  - "ALWAYS make jobs idempotent (safe to run multiple times)"
  - "ALWAYS set a timeout for every job"
  - "ALWAYS implement retry with exponential backoff"
  - "ALWAYS implement dead letter queue for permanently failed jobs"
  - "ALWAYS log job start, completion, and failure"
  - "ALWAYS separate queues by priority (high, medium, low)"
  - "ALWAYS monitor queue depth and processing time"
  - "NEVER process heavy jobs synchronously in API requests"
  - "NEVER store large data in the job payload — store a reference (S3 key, DB ID)"
  - "ALWAYS handle graceful shutdown (finish current job before stopping)"
```

---

## 32. Environment Management

### 32.1 Environment Tiers

```yaml
environments:
  local:
    purpose: "Developer's machine"
    database: "Local PostgreSQL or Docker"
    services: "Docker Compose for dependencies"
    config: ".env.local (never committed)"
    deployment: "Manual (npm run dev)"

  development:
    purpose: "Shared dev environment (optional)"
    database: "Shared dev database"
    services: "Deployed to dev server/cloud"
    config: ".env.development"
    deployment: "Auto-deploy on push to develop branch"

  staging:
    purpose: "Pre-production testing"
    database: "Copy of production schema, anonymized data"
    services: "Mirrors production setup exactly"
    config: ".env.staging"
    deployment: "Auto-deploy on PR merge to main"
    rule: "MUST mirror production as closely as possible"

  production:
    purpose: "Live user-facing system"
    database: "Production database"
    services: "Full production infrastructure"
    config: "Managed via secrets manager (Vault, AWS Secrets Manager)"
    deployment: "After staging validation + human approval"
    rule: "NEVER deploy directly — always through CI/CD pipeline"
```

### 32.2 Environment Variable Rules

```yaml
env_variables:
  file_structure:
    ".env.example": "Template with all variables (NO values) — committed to git"
    ".env.local": "Local development values — NEVER committed"
    ".env.test": "Test environment values — may be committed (no secrets)"

  naming_convention:
    format: "UPPER_SNAKE_CASE"
    prefix: "APP_ for app-specific, DB_ for database, REDIS_ for Redis"
    examples:
      - "APP_PORT=3000"
      - "APP_ENV=production"
      - "DB_HOST=localhost"
      - "DB_PORT=5432"
      - "DB_NAME=myapp"
      - "DB_USER=postgres"
      - "DB_PASSWORD=<from-secrets-manager>"
      - "REDIS_URL=redis://localhost:6379"
      - "JWT_SECRET=<from-secrets-manager>"
      - "AWS_S3_BUCKET=myapp-uploads"
      - "SMTP_HOST=smtp.resend.com"
      - "SMTP_API_KEY=<from-secrets-manager>"

  validation:
    rule: "ALWAYS validate env variables at startup — fail fast if missing"
    tool_node: "zod + dotenv"
    tool_python: "pydantic-settings"
    pattern: |
      1. Define schema with all required variables
      2. Validate on app startup
      3. If any missing → crash immediately with clear error message
      4. NEVER use process.env directly — use validated config object

  rules:
    - "NEVER commit .env files with real values"
    - "ALWAYS have .env.example with ALL variable names"
    - "ALWAYS validate env variables at startup"
    - "ALWAYS use a secrets manager in production (not .env files)"
    - "NEVER log env variable values (log names only)"
    - "ALWAYS use different values per environment (especially secrets)"
    - "ALWAYS rotate secrets regularly (JWT secrets, API keys)"
```

### 32.3 Configuration Management

```yaml
config_management:
  
  secrets_in_production:
    preferred: "HashiCorp Vault"
    alternatives:
      - "AWS Secrets Manager"
      - "GCP Secret Manager"
      - "Azure Key Vault"
      - "Doppler (managed, multi-cloud)"
    rule: "NEVER use .env files in production — always a secrets manager"

  feature_differences:
    development:
      logging: "DEBUG level, console output"
      error_detail: "Full stack traces"
      rate_limiting: "Disabled or lenient"
      email: "Redirect all to developer's email"
      payments: "Sandbox/test mode"
      ssl: "Optional"
    
    staging:
      logging: "INFO level, structured JSON"
      error_detail: "Full stack traces (internal only)"
      rate_limiting: "Same as production"
      email: "Redirect all to test mailbox"
      payments: "Sandbox/test mode"
      ssl: "Required"
    
    production:
      logging: "INFO level, structured JSON, shipped to log aggregator"
      error_detail: "NEVER expose stack traces"
      rate_limiting: "Enforced"
      email: "Real delivery"
      payments: "Live mode"
      ssl: "Required, enforced, HSTS enabled"
```

---

## 33. Command Reference

### 33.1 A-SDLC Commands

These commands can be given to any AI assistant that has loaded this document:

| Command | Description | Phase |
|---------|-------------|-------|
| `start project` / `bootstrap` | Begin full project creation from scratch | Phase 1-4 |
| `discover` | Run Phase 1 discovery questions | Phase 1 |
| `design` | Create architecture and tech stack | Phase 2 |
| `contracts` | Generate coding contracts | Phase 3 |
| `scaffold` | Generate project structure and configs | Phase 4 |
| `build [feature]` | Implement a specific feature | Phase 5 |
| `validate` | Run all validation checks | Phase 6 |
| `deploy staging` | Deploy to staging environment | Phase 7 |
| `deploy production` | Deploy to production (with approval) | Phase 7 |
| `status` | Show current phase and progress | Any |
| `checkpoint` | Save current progress summary | Any |
| `handoff` | Generate session handoff document | Any |
| `tech stack` | Show or re-evaluate tech stack | Phase 2 |
| `security review` | Run security review on current code | Phase 6 |
| `compliance check [standard]` | Run compliance checklist (GDPR/PCI/SOC2/HIPAA) | Phase 6 |
| `rollback` | Initiate rollback procedure | Phase 7-8 |
| `incident` | Start incident response procedure | Phase 8 |

### 33.2 Combined Usage with masterSDLC.md

| masterSDLC.md Command | A-SDLC Enhancement |
|-----------------------|-------------------|
| `brainstorm` | A-SDLC adds tech feasibility analysis + AI-ready requirements |
| `prd` / `PRD banao` | A-SDLC adds AI coding contracts + tech stack selection |
| `trd` / `TRD banao` | A-SDLC adds file ownership + module contracts |
| `security check` | A-SDLC adds automated compliance engine |
| `generate files` | A-SDLC uses project templates + bootstrap automation |
| `test cases` | A-SDLC adds self-correction loop integration |
| `deploy guide` | A-SDLC adds rollback automation + monitoring setup |

---

## Final Notes

### This Document Is:
- **Universal**: Works for any project, any language, any scale
- **Deterministic**: Decisions follow rules, not opinions
- **Self-correcting**: AI fixes its own mistakes within defined limits
- **Security-first**: Security cannot be overridden by convenience
- **AI-native**: Designed specifically for AI-driven development

### How to Use:
1. Feed this document + `masterSDLC.md` to your AI IDE
2. Say `start project` or describe your idea
3. Let the AI walk through the phases
4. Approve critical decisions when asked
5. Review the output at each phase gate
6. Deploy with confidence

### Maintenance:
| Section | Update Frequency | Trigger |
|---------|-----------------|---------|
| Tech Stack Rules (Section 4) | Quarterly | New framework releases |
| Approved Dependencies (Section 5.4) | Monthly | Security advisories |
| Compliance Checklists (Section 11) | Bi-annually | Regulatory changes |
| Infrastructure Stack (Section 8) | Quarterly | New tool releases |
| Prompt Library (Section 10) | As needed | New patterns discovered |

---

**VERSION:** 2.0
**CREATED:** 2026-02-10
**COMPANION:** masterSDLC.md v1.0
**TARGET:** AI-Native Autonomous Development
**MAINTAINED BY:** AI CTO + Human Oversight

---

## Document Complete

You now have a complete A-SDLC framework that transforms any AI into an autonomous, security-first software factory:

- AI Role Hierarchy & Control Plane
- Phase-Gated Execution (no skipping steps)
- Deterministic Tech Stack Selection (no guessing)
- AI Coding Contracts (no hallucination)
- IDE-Specific Playbooks (Cursor, Claude, Antigravity, Copilot)
- Self-Correction Loops (auto-fix within limits)
- Golden Infrastructure Stack (opinionated defaults with flexibility)
- One-Command Project Bootstrap (scaffolding automation)
- AI Prompt Library (secure code generation templates)
- Compliance Automation (GDPR, PCI-DSS, SOC 2, HIPAA)
- Monitoring & Observability (pre-configured dashboards and alerts)
- Disaster Recovery & Rollback (automated protection)
- Token & Context Management (efficient AI IDE usage)
- Universal Project Type Support (any project, any tech)

**Feed this to any AI. Build anything. Securely. Autonomously.**
