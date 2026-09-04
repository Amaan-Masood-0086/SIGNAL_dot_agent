# SIGNAL

**Developmental screening for children in institutional care — every observation documented, every flag explained.**

SIGNAL turns what a caretaker notices ("he doesn't turn around when I clap behind him")
into a graded, citation-backed screening record that routes a child to a clinician — and
leaves a tamper-evident trail proving the institution noticed and acted.

It is a **screening aid, not a diagnostic tool**. It never produces a diagnosis.

> ⚠️ **Synthetic data only.** This build runs under `ENVIRONMENT=synthetic_only` and
> refuses to mint tokens outside it. Password verification is deliberately not yet
> implemented (see [Known limitations](#known-limitations)). Do not put real children's
> data in it.

---

## What problem this solves

Speech, language and hearing delays are most treatable when caught early. In institutional
care two things make that hard:

1. **Nobody owns the observation.** A caretaker notices something, mentions it, and it is
   gone. There is no record, so nothing happens and nothing can be shown to have happened.
2. **Most children have no confirmed date of birth.** Every milestone chart assumes you
   know the child's age. Here you usually do not.

SIGNAL is built around both. Observations become records. Age is modelled as *either* a
confirmed DOB *or* an estimated range — and when it is estimated, every age-dependent
grade is downgraded automatically rather than guessed at.

The thing an institution actually buys is the second half: **a documented concern with a
recorded response**. An undocumented concern is not protection — it is documented
negligence.

---

## How a screening works

```
caretaker observation  ──►  observation agent   (extracts signals)
   (voice or text)             │
                              ▼
                        knowledge base          (94 curated milestone / red-flag rows,
                              │                  Speech_Language + Hearing, retrieved
                              ▼                  JOINTLY — hearing loss and language
                        reasoning agent          delay present identically)
                              │
                              ▼
                   deterministic grade()         ◄── ADR-06 rules, not the model
                              │
                              ▼
        HIGH · MODERATE · LOW-monitor · INSUFFICIENT_INFORMATION
                              │
                              ▼
                   flag + reasoning trail        (every citation_ref that produced the
                                                  grade, snapshotted at write time)
```

Two properties matter more than the model:

- **The grade is deterministic.** The LLM extracts signals and asks follow-up questions;
  it does not decide the grade. `grade()` does, from rules.
- **Every flag carries its basis.** The reasoning trail records the exact knowledge-base
  rows behind the grade, with their text as it was *at the time of grading* — so a
  clinician reviewing it six months later reads the wording the decision was actually
  made on, and is told if the reference has changed since.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI · SQLAlchemy 2 · Alembic · Python 3.12 |
| Database | PostgreSQL 16 with **row-level security** for tenant isolation |
| Frontend | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind 4 |
| Auth | RS256 JWT in an HttpOnly cookie — never in localStorage |
| Speech-to-text | Provider seam (Azure Speech / Knowlez) — voice degrades to text, never blocks |
| LLM | Any OpenAI-compatible endpoint (tested against DeepSeek) |

---

## Running it locally

**Prerequisites:** Docker, Python 3.12, Node 22.

```bash
# 1. Database
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv && .venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.lock.txt

# Secrets. Either copy the template and fill it in by hand:
cp .env.example .env
# ...or generate a complete throwaway set for a local synthetic run
# (RS256 keypair + Fernet key + both database URLs). It refuses to
# overwrite an existing .env:
python scripts/write_dev_env.py

alembic upgrade head                                 # also creates the signal_app role
python scripts/ingest_knowledge_base.py              # REQUIRED — see note below
python scripts/seed_synthetic_tenant.py
python scripts/seed_admin.py --email root@signal.example
uvicorn app.main:app --port 8002

# 3. Frontend
cd ../frontend
npm ci
cp .env.example .env.local                           # BACKEND_URL=http://localhost:8002
npm run dev
```

Open **http://localhost:3000**.

`ingest_knowledge_base.py` is not optional. The milestones and red flags live in
the database, not in code, and `alembic upgrade head` creates the table empty —
so without this step every screening returns "not enough information" and the
product does nothing. It reads
`.ai/brain/knowledge-base-source/signal_knowledge_base_v2.csv`, is idempotent
(upsert on `citation_ref`, ADR-08), and runs under the privileged role because
`signal_app` has SELECT-only on that table.

### Moving to another machine

The repository carries everything except secrets and data: both are excluded on
purpose. Run the steps above on the new machine, then be aware of two things.

`CREDENTIAL_ENCRYPTION_KEY` is a **new** key unless you copy the old one across,
and provider credentials are encrypted at rest with it (ADR-10). A new key does
not corrupt anything, but previously stored provider keys become undecryptable —
so re-enter the LLM and STT keys through the admin console. There is no export
path for them by design: the surface is write-only, and only the last four
characters are ever displayed again.

The database itself does not travel with the repository. `docker compose`
provisions an empty Postgres and the seed scripts rebuild the knowledge base, a
synthetic tenant and an admin account, which is enough for a full working
system. Real screening records, if any exist, need a `pg_dump`.

### Required environment values

| Variable | Notes |
|---|---|
| `DATABASE_URL` | Privileged path — migrations, login, admin cross-institution reads |
| `TENANT_DATABASE_URL` | **Unprivileged** `signal_app` role, so RLS actually binds |
| `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` | RS256 PEM pair |
| `CREDENTIAL_ENCRYPTION_KEY` | Fernet key. No default on purpose — the credential surface fails closed |
| `APP_ALLOWED_ORIGINS` | Frontend only. Extra trusted origins when served behind a proxy or dev tunnel |

Provider API keys are **not** set here. They are stored through the admin console,
encrypted at rest, and are write-only: once saved only the last four characters are ever
shown again.

---

## Tests

```bash
# Backend — needs real Postgres. SQLite is never a fallback: row-level
# security is an acceptance criterion and is Postgres-only.
./scripts/run_backend_tests.ps1        # 417 passed · 1 skipped · 1 xfailed

# Frontend
cd frontend && npm test                # 17 passed
```

One test is a permanent `xfail` and that is deliberate — see
[The R14 divergence](#the-r14-divergence).

CI (`.github/workflows/ci.yml`) additionally runs `bandit`, `pip-audit`,
`npm audit --audit-level=high` and `gitleaks` on every pull request.

---

## Security model

| Control | Where |
|---|---|
| Tenant isolation | Postgres RLS, enforced by the **database**, not by remembering a `WHERE` clause |
| Least privilege | App connects as `signal_app` — no superuser, no `BYPASSRLS`, no `DELETE` grant |
| Audit trail | Hash-chained, append-only. Records **reads as well as writes** — "who opened this child's record" is answerable |
| Credentials at rest | Fernet-encrypted, write-only API contract |
| IDOR | Uniform `403` for both "missing" and "another institution" — existence never leaks |
| CSRF | Origin check on every state-changing route, explicit allowlist, never a wildcard |
| CSP | Per-request nonce; no `unsafe-inline` for scripts |
| Prompt injection | Caretaker text is fenced as data; the system prompt forbids treating it as instructions |
| PII in prompts | The LLM receives age context and the observation text — never a name, ID or institution |

Row-level security is verified from the hostile direction: `test_tenant_session_rls.py`
runs queries **with no application filter at all** and asserts the database still refuses
another institution's rows.

---

## Repository layout

```
backend/
  app/
    api/v1/endpoints/     route handlers
    services/             knowledge base, risk pipeline, agents, audit, credentials
    models/ schemas/      SQLAlchemy models · Pydantic contracts
  alembic/versions/       migrations (RLS lives in 0001)
  tests/                  419 tests, Postgres-backed
frontend/
  app/                    App Router pages + same-origin API proxies
  src/components/         UI primitives and feature surfaces
  src/lib/                API clients, RBAC, screening grade model
.ai/
  brain/                  PROJECT_BRIEF, TRD, ADRs, THREAT_MODEL, PROGRESS
  brain/knowledge-base-source/   the clinical CSVs
  audit/                  deep-code-audit report + remediation backlog
```

The knowledge base is the asset, not the app. `signal_knowledge_base_v2.csv` holds 94
curated rows sourced from ASHA, CDC "Learn the Signs", NIDCD, JCIH 2019, MacArthur-Bates
CDI norms and the late-talker literature (Rescorla, Paul, Coplan & Gleason, Flipsen).

---

## The R14 divergence

One acceptance case (`T6`) is marked `xfail` rather than fixed. The clinical dataset
expects `MODERATE`; ADR-06's literal counting rule computes `HIGH`.

Both are defensible, and the disagreement is informative: the three cited rows —
"says *what?* often", "sits close to the TV", "recurrent ear infections" — are not three
independent findings. They are one clinical picture (otitis media with effusion). The
counting rule treats correlated evidence as independent.

Resolving it is a clinical decision, so it is **documented and blocked rather than
silently patched**. If that test ever starts passing, the divergence was resolved and the
marker should be removed.

---

## Known limitations

Honest list. None of these are hidden in the code.

- **Password verification is not implemented.** Any password is accepted; the role comes
  from the database row for the given email. Gated to `synthetic_only`. This is FEAT-12
  scope and is the single reason this build must not be exposed publicly.
- **No consent model.** Recording consent exists in the voice UI but is not persisted, and
  there is no processing-consent record. Needs a legal decision before code.
- **No retention or erasure policy.** Children can be *archived* (reversible, reason
  required, nothing destroyed) but never deleted. What happens after archiving is an
  unresolved policy question, deliberately left open.
- **Access is institution-scoped, not relationship-based.** Any caretaker in an
  institution sees every child in it; clinical practice would scope to assigned children.
- **Rate limiting is in-process.** Correct for one instance; Redis is the documented path
  for more.
- **"Any caretaker concern" is a HIGH red flag at any age**, which is nearly always true
  by construction in a tool people only open when worried. See `.ai/audit/AUDIT_REPORT.md`.

---

## Documentation

- `.ai/brain/PROJECT_BRIEF*.md` — what is being built and why
- `.ai/brain/TRD*.md` — API contracts and data model
- `.ai/brain/THREAT_MODEL*.md` — STRIDE analysis and the RBAC matrix
- `.ai/brain/ADR_*.md` — architecture decisions (ADR-02 dual age, ADR-05 joint
  hearing/language reasoning, ADR-06 grading, ADR-10 credential storage)
- `.ai/audit/AUDIT_REPORT.md` — principal-engineer audit with findings and remediation status

---

## Status

Phase 1, synthetic data only. Not cleared for clinical use, and not for deployment
outside a local development environment until password verification (FEAT-12) lands and
the consent and retention questions above have answers.
