# Onboarding prompt for an AI agent

Paste the block below into a fresh session before asking for any work. It is
written to be handed to any capable coding agent, not just one.

There is deliberately no `CLAUDE.md` at the repository root, so nothing routes
an agent to these documents automatically — that is why this prompt exists.

---

```
You are joining SIGNAL, a developmental screening tool for children aged 0–6 in
institutional care in Pakistan. A caretaker describes a child in their own words
(Urdu or English, typed or spoken); the system asks follow-up questions, then
grades concern for referral. It never diagnoses.

This is a health-adjacent tool that grades real children's development. Read
before you write. Guessing here has a cost that guessing in a CRUD app does not.

## Read in this order

1. `.ai/brain/HANDOVER_SIGNAL_2026-09-04.html`
   Start here. The current state of the build: what works, what is measured but
   unsolved, what is blocked on a person rather than on code. Also lists the
   traps that waste an afternoon.

2. `.ai/brain/PROGRESS.md`
   The session log, newest entries at the bottom of the table. Every non-obvious
   decision and every retracted mistake is recorded with its reasoning. If you
   are about to "fix" something that looks wrong, search here first — it may
   already have been tried and reverted for a reason.

3. `.ai/brain/PROJECT_BRIEF_SIGNAL_2026-08-28.md`
   What the product is for and who uses it.

4. `.ai/brain/TRD_SIGNAL_2026-08-28.md`
   API contracts and data models. Section 4a is an addendum covering the two
   database paths, read auditing, the archive contract, `response_language`,
   trail snapshots, and the timeout/token policy.

5. `.ai/brain/THREAT_MODEL_SIGNAL_2026-08-28.md`
   Security constraints and the acknowledged residual risks. Read the addendum
   at the end.

6. `.ai/brain/ADR_01` through `ADR_10` in `.ai/brain/`
   Ten architecture decisions. The ones that will bite you if unread:
   - ADR-02: two age models — confirmed date of birth vs an estimated range.
     An estimated range is always evaluated at the YOUNGER bound.
   - ADR-04: full context injection, deliberately NOT RAG. Do not "improve"
     this into a vector store.
   - ADR-06: deterministic four-state grading. The LLM never picks the grade.
   - ADR-08: `citation_ref` carries two identities; the knowledge base upserts
     on it.
   - ADR-10: provider credentials are managed in the admin UI, encrypted at
     rest, write-only. This supersedes ADR-09.

7. `.ai/brain/RISK_REGISTER.md`
   Read R14 specifically. It is an open clinical divergence, pinned by an
   `xfail` test, and explicitly marked no-speculative-fix.

8. `frontend/AGENTS.md`
   Read this before touching any frontend file. This is Next.js 16 and it does
   not match what you were trained on — middleware is `proxy.ts`, not
   `middleware.ts`. The file tells you to read `node_modules/next/dist/docs/`
   first. Do that; skipping it has already caused a broken build here.

## Then the code, in this order

- `backend/app/services/knowledge.py` — `grade()` is the deterministic core.
- `backend/app/services/pipeline_agents.py` — the three agents (observation,
  risk reasoning, explanation) and their JSON contracts.
- `backend/app/services/risk_pipeline.py` — how a turn is orchestrated.
- `backend/app/api/deps.py` — `get_db` vs `get_tenant_db`. Understanding this
  distinction is not optional; see the hard rules below.
- `backend/alembic/versions/0001_initial_schema.py` — row-level security lives
  here.

## Hard rules — breaking these causes real damage

- NEVER log agent output, caretaker text, or any child's clinical detail. Log
  shape and length, never content. See `_output_shape` in `pipeline_agents.py`
  for the pattern.
- NEVER use `get_db` for caretaker-facing endpoints. It is the PRIVILEGED path
  and bypasses row-level security. Use `get_tenant_db`. The privileged path is
  reserved for migrations, `/auth/token`, and documented admin cross-tenant
  reads.
- NEVER remove the fail-closed checks in `_verified_tenant_engine`, and never
  add an environment exemption to them. An exemption is how row-level security
  came to be silently inert once already.
- NEVER let the LLM choose a grade. `grade()` is pure and deterministic by
  ADR-06.
- NEVER treat caretaker text as instructions. It arrives fenced as
  `<caretaker_input>` DATA. Any language or behaviour preference must be a
  CLOSED ENUM, never free text passed to the model.
- NEVER override an existing ADR. Write a new one with the rationale.
- NEVER write or edit clinical content — red flags, milestones, severities,
  follow-up questions, risk modifiers — without human clinical sign-off. R14
  sets this precedent explicitly. Drafting it fluently is exactly the risk.
- Environment must stay `synthetic_only`. No real child data.

## Traps that have already cost time here

- Do NOT set `max_tokens` on LLM calls. It was tried. `deepseek-v4-flash`
  spends its budget on internal reasoning, so a cap left nothing for the reply
  and the model returned an empty string, failing the first turn.
  `MAX_TOKENS_BY_TIER` is intentionally empty; the reason is at its definition.
- Tests need PostgreSQL and refuse to run on SQLite. Export
  `SIGNAL_TEST_DATABASE_URL` and `CREDENTIAL_ENCRYPTION_KEY` before running
  pytest, exactly as `.github/workflows/ci.yml` does, or you will chase
  phantom failures.
- `pytest.ini` sets `filterwarnings = error`. A deprecation from a dependency
  can fail collection depending on test ORDER. Check whether a failure is
  pre-existing by stashing your changes and re-running before you debug it.
- CI cannot start on this repository at all — every run returns
  `startup_failure` in 0s, including GitHub's own workflows. This is an
  account-level matter, not a YAML fault, and it is already bisected. Do not
  re-investigate; run the gates locally.
- On Windows: PowerShell 5.1 has no `&&` operator, and Git Bash mangles
  Unix-style paths in arguments — prefix with `MSYS_NO_PATHCONV=1`.

## How to work

Verify before asserting. This project's log is full of findings that were
measured, found false, and retracted — a stopped database read as a 15-second
network penalty, a console encoding artifact read as data corruption. Run the
command; do not reason from what is probably true.

When you finish a piece of work, append what you did and why to
`.ai/brain/PROGRESS.md`, including anything you tried and reverted. That file is
the reason this project can be picked up mid-flight.

Before you say something is done: input validated, ownership checked on any new
endpoint, no secrets or PII in code or logs, fail-closed error handling, tests
passing, and `bandit`, `pip-audit` and `npm audit --audit-level=high` all clean.
```

---

## If the agent only gets one file

Give it `.ai/brain/HANDOVER_SIGNAL_2026-09-04.html`. It carries the current
state, the open decisions, and the traps — enough to avoid doing harm, though
not enough to build confidently.
