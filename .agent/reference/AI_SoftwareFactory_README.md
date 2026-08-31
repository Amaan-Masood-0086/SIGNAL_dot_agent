---
description: AI_SoftwareFactory_README — Operator guide for running projects with masterSDLC + A-SDLC + domain modules. Includes copy/paste bootstrap prompt.
---

# AI Software Factory — Operator Guide (Human-in-the-Loop)

## 0) The Goal

You (Human) provide:
- product vision
- approvals at gates
- any unclear requirement clarifications

AI agents provide:
- requirements docs
- architecture
- code + tests
- security + compliance checks
- CI/CD + deployments
- runbooks + monitoring

---

## 1) Which Files to Feed to the AI

### Always (Required)
- `masterSDLC.md` (security foundation)
- `A-SDLC.md` (AI orchestration and phase gates)

### Add One Domain Module
- **Web app:** `masterWebSDLC.md`
- **Mobile app:** `masterMobileSDLC.md`

### Optional
- `NotionProjectOS.md` (Notion Project OS templates)

---

## 2) Copy/Paste Bootstrap Prompt (Use This in Any AI / IDE)

```markdown
You are operating under the A‑SDLC framework.

RULES:
1) Read and obey: masterSDLC + A‑SDLC + the relevant domain module (web/mobile).
2) Do NOT skip phases. Identify current phase and proceed only if the previous gate is passed.
3) Create and maintain `.ai/brain/` with: PROJECT_BRIEF, TRD, THREAT_MODEL, ADRs, TEST_PLAN, RISK_REGISTER, RUNBOOK, RELEASE_NOTES.
4) For every code change: implement → tests → lint/typecheck → security scan → commit message.
5) Security rules are non‑negotiable.

START NOW:
Phase 1 (DISCOVER):
- Ask the mandatory discovery questions.
- Produce `PROJECT_BRIEF_[ProjectName]_[Date].md`
- Produce competitor analysis (3–5 competitors) + differentiation plan
- Output a phase gate report for Gate 1.
Stop after Gate 1 and wait for approval.
```

---

## 3) Repo Conventions (Recommended)

```
/.ai/brain/                 # AI memory + artifacts
/docs/                      # public docs for humans
/infrastructure/            # IaC (DevOps-owned)
/scripts/                   # CI/dev scripts
/apps/web or /web           # web app (if monorepo)
/apps/mobile or /mobile     # mobile app (if monorepo)
/services/api or /api       # backend
```

---

## 4) What “Done” Means (Minimum)

- All features built + tested
- CI green
- Security scans clean (no Critical/High)
- Observability in place (logs/metrics/alerts)
- Deployable with rollback plan
- Documentation updated

---

## End
