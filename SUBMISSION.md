# Hackathon submission — copy-paste sheet

Everything the portal asks for, ready to paste. Team: **Sami** (lead) · **Ayesha** · **Amaan**.

---

## 1. Public GitHub repository

```
https://github.com/Amaan-Masood-0086/SIGNAL_dot_agent
```

Default branch: `main`. No secrets committed — `.env` and `.env.*` are gitignored,
`.env.example` carries placeholders, and `gitleaks` runs clean.

---

## 2. Project summary (portal field — 200–1,500 characters)

> Paste the block below. It is 1,172 characters — inside the 200–1,500 limit.

SIGNAL is a developmental screening companion for children aged 0–6 in institutional care in Pakistan — orphanages, shelters and welfare homes.

A caretaker describes something they noticed about a child, in Urdu or English, by voice or by typing: "he doesn't turn around when I clap behind him." SIGNAL asks a few adaptive follow-up questions, then produces a confidence-graded concern with a plain-language explanation and a cited clinical basis, filed into a tamper-evident record a clinician can review.

Two things matter more than the model. The grade is deterministic — the LLM extracts signals and asks questions, but a rules function decides HIGH / MODERATE / LOW-monitor / INSUFFICIENT. And most children here have no confirmed date of birth, so age is modelled as either a confirmed DOB or an estimated range, with age-dependent grades downgraded automatically rather than guessed.

It is a screening aid, not a diagnostic tool, and never produces a diagnosis.

Built: FastAPI + PostgreSQL 16 with row-level security, Next.js 16, a 94-row curated clinical knowledge base (ASHA, CDC, NIDCD, JCIH), a hash-chained audit trail, and 523 tests against real Postgres.

---

## 3. Presentation

Slides live in [`PRESENTATION.md`](PRESENTATION.md) — export to PDF or PPTX before uploading
(the portal does not accept a Slides link).

---

## Verified numbers (do not quote anything else)

Measured on 2026-09-07 against real PostgreSQL, after the admin-onboarding merge.

| Suite | Result |
|---|---|
| Backend | **498 tests** — 496 passed · 1 skipped · 1 xfailed |
| Frontend | **25 passed** |
| **Total** | **523** |

The skip is the deployed-tenant-URL guard (passes when `SIGNAL_TEST_TENANT_DATABASE_URL` is set).
The xfail is the documented **R14 divergence** — dataset T6 expects MODERATE, ADR-06's literal
counting rule computes HIGH. It is blocked pending clinical sign-off rather than silently patched.

Earlier figures in circulation are stale: README previously said 417, and an earlier brief said 429.
Both predate the admin onboarding, lifecycle, LLM-retry and synthetic-reasoner test suites.

---

## Names on the slides

Registered team only: **Sami**, **Ayesha**, **Amaan**.

`Akasha Azhar (AI CTO/CISO)` appears in `.ai/brain/` ADRs and the project brief as the internal
architecture and security decision authority. That is an accurate internal record and stays there —
but it does not go on the submission slides, which show the registered team.
