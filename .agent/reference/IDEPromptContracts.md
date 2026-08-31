---
description: IDEPromptContracts — Prompt contracts for Cursor/Antigravity/Claude/GPT. Rule files, memory discipline, context packing, deterministic agent behavior.
---

# IDE Prompt Contracts & Agent Memory Discipline

## Purpose

This doc provides **copy‑paste prompt contracts** and **rule files** so any IDE agent (Cursor, Antigravity, Claude, GPT, Copilot) behaves like a disciplined **software engineer**, not a random code generator.

It also defines the **agent memory protocol**: where the project brain lives, how it is updated, and how to avoid hallucinations.

Companion docs:
- `A-SDLC.md`
- `masterSDLC.md`
- domain modules (`masterWebSDLC.md`, `masterMobileSDLC.md`, `masterBackendSDLC.md`, `masterCloudSDLC.md`, `masterDataSDLC.md`)
- governance (`masterReleaseGovernance.md`)

---

## 1. Universal Prompt Contract (Paste into any agent)

**SYSTEM CONTRACT (MUST):**
- You must follow the SDLC gates. You may not skip phases.
- You must not guess missing requirements. Ask or create a documented assumption list.
- You must keep artifacts in `.ai/brain/` and keep them updated.
- You must run tests/scans before declaring completion.
- You must produce professional documentation for every major step.

**WORKFLOW CONTRACT (MUST):**
1. Create/update `.ai/brain/PROJECT_BRIEF.md`
2. Create/update `.ai/brain/TRD.md`
3. Create/update `.ai/brain/THREAT_MODEL.md`
4. Create ADRs for decisions
5. Implement code
6. Validate (lint/type/test/security/perf)
7. Produce docs + release notes
8. Provide next actions

---

## 2. Context Packing Rules

When feeding context to an AI:
- Always include:
  - `PROJECT_BRIEF`
  - `TRD`
  - current `TASK.md`
  - `THREAT_MODEL`
  - relevant module docs (web/mobile/backend/cloud/data)
- Include only:
  - code for the module being edited
  - failing logs / stack traces

Avoid:
- huge unrelated code dumps
- duplicate content (wastes tokens)

---

## 3. “Agent Memory” Discipline

### 3.1 Required Folder Structure

```
.ai/
  brain/
    PROJECT_BRIEF.md
    TRD.md
    THREAT_MODEL.md
    RISK_REGISTER.md
    TEST_PLAN.md
    RUNBOOK.md
    RELEASE_NOTES.md
    ADR/
      ADR_001_....md
  reports/
    gate6_report.md
```

### 3.2 Memory Update Rules (MUST)

- After each gate, update:
  - `RISK_REGISTER` (new risks, status)
  - `RUNBOOK` (new operational steps)
  - `RELEASE_NOTES` (what changed)
- ADR required for:
  - data model
  - auth model
  - hosting model
  - major libraries/framework changes
  - security tradeoffs

---

## 4. Cursor Rules (Two Options)

Because tooling evolves, ship both:

### 4.1 Root `.cursorrules` (fallback)

Create a file `.cursorrules` with:

```
You are an AI engineer operating under A-SDLC + masterSDLC.
MUST follow phase gates.
MUST create/update .ai/brain artifacts.
MUST run lint/typecheck/tests/security scans before completion.
MUST not invent requirements; list assumptions.
MUST implement object-level authorization checks and IDOR tests for any resource endpoint.
MUST keep secrets out of code and logs.
MUST output professional docs in /docs when features change.
```

### 4.2 `.cursor/rules/*.md` (preferred modular rules)

Create files like:
- `.cursor/rules/00_factory.md`
- `.cursor/rules/10_security.md`
- `.cursor/rules/20_docs.md`

Each file contains focused rules (see template zip included).

---

## 5. Claude / GPT “Project Instructions” File

Create `AGENTS.md` at repo root:

- Short overview of project
- Running commands
- Gate requirements
- Do/Don’t list
- Where artifacts live
- How to write docs and release notes

This file is broadly supported by many tools and is safe even if the IDE ignores it.

---

## 6. Antigravity / Other IDEs

If IDE supports “workspace rules”, paste the Universal Prompt Contract and add:

- “Always show plan before code”
- “Never modify more than 3 files per commit unless necessary”
- “Every PR must include tests or a documented reason”

---

## 7. Professional Documentation Rule

Any change that impacts:
- user behavior
- security model
- API
- infrastructure
- data model

…MUST update:
- `docs/` pages
- `RUNBOOK.md`
- `RELEASE_NOTES.md`

---

## 8. Default “Start Project” Prompt

Copy-paste:

```
You are AI CTO + Tech Lead + Security Engineer.
Load: masterSDLC + A-SDLC + relevant domain modules.
Goal: convert idea into PROJECT_BRIEF, PRD, TRD, THREAT_MODEL, ADRs, implementation plan, and code skeleton.
Do not write production code until TRD and threat model pass Gate 4.
```
