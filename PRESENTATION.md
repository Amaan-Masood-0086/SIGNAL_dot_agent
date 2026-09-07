# SIGNAL — Presentation Deck

**Developmental screening for children in institutional care — every observation documented, every flag explained.**

| | |
|---|---|
| **Team lead** | Sami |
| **Members** | Ayesha · Amaan |
| **Repository** | https://github.com/Amaan-Masood-0086/SIGNAL_dot_agent |
| **Status** | Phase 1 · synthetic data only · not cleared for clinical use |

---

## Slide 1 — Title

**SIGNAL**

Turns what a caretaker notices — *"he doesn't turn around when I clap behind him"* —
into a graded, citation-backed screening record that routes a child to a clinician,
and leaves a tamper-evident trail proving the institution noticed and acted.

> It is a **screening aid, not a diagnostic tool**. It never produces a diagnosis.

---

## Slide 2 — The problem, and who it affects

**Who:** children aged 0–6 in orphanages and institutional care, and the caretakers responsible for them.

Speech, language and hearing delays are most treatable when caught early. In institutional care two things make that hard:

1. **Nobody owns the observation.** A caretaker notices something, mentions it, and it is gone. No record → nothing happens → nothing can be *shown* to have happened.
2. **Most children have no confirmed date of birth.** Every milestone chart assumes you know the child's age. Here you usually do not.

An undocumented concern is not protection — it is **documented negligence**.

---

## Slide 3 — The solution, and the audience it serves

A caretaker speaks or types a plain-language observation. SIGNAL:

- extracts the developmental signals,
- retrieves matching milestones and red flags from a curated clinical knowledge base,
- asks adaptive follow-up questions when evidence is thin,
- computes a **deterministic grade** (not the model's opinion),
- writes a flag with a full reasoning trail, and routes the child to a clinician.

**Audience:** institutional caretakers (primary users), clinicians (receive the referral + evidence), institution administrators (oversight + audit).

---

## Slide 4 — The need it addresses and the impact it makes

| Need | How SIGNAL meets it |
|---|---|
| Early detection of speech / language / hearing delay | Structured screening from everyday observations |
| Age unknown for most children | Dual age model — confirmed DOB **or** estimated range; estimated age auto-downgrades age-dependent grades instead of guessing |
| Proof the institution acted | Hash-chained, append-only audit trail — records **reads as well as writes** |
| Trust from clinicians | Every flag carries the exact knowledge-base rows behind it, snapshotted at the moment of grading |

**Impact:** the concern becomes a record with a recorded response — the thing an institution can actually be held to.

---

## Slide 5 — The innovation

- **Deterministic grade, not an LLM verdict.** The model extracts signals and asks questions; a pure `grade()` function decides HIGH / MODERATE / LOW-monitor / INSUFFICIENT_INFORMATION from rules (ADR-06).
- **Joint hearing + language reasoning.** Hearing loss and language delay present almost identically, so the knowledge base is retrieved for both domains together; the domain is decided only *after* the joint check.
- **Reproducible reasoning trail.** The trail is a write-time snapshot — a clinician six months later reads the exact wording the decision was made on, and is told if the reference has changed since.
- **Age modelled as uncertainty, not a number.** Estimated age evaluates at the younger bound and rides `age_uncertain` through every result.
- **Safety by construction.** Caretaker text is fenced as *data* in every prompt; the LLM never receives a name, ID or institution.

---

## Slide 6 — The technology behind it

| Layer | Choice |
|---|---|
| **Backend** | FastAPI · SQLAlchemy 2 · Alembic · Python 3.12 |
| **Database** | PostgreSQL 16 with **row-level security** for tenant isolation |
| **Frontend** | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind 4 |
| **Auth** | RS256 JWT in an HttpOnly cookie — never in localStorage |
| **AI pipeline** | Direct multi-call agent design (no LangChain) — observation → reasoning → explanation, strict JSON contracts |
| **LLM** | Any OpenAI-compatible endpoint (tested against DeepSeek); deterministic keyless synthetic reasoner for demos |
| **Speech-to-text** | Provider seam (Azure Speech / Knowlez) — voice degrades to text, never blocks |
| **Credentials** | Fernet-encrypted at rest, write-only admin API (last 4 chars ever shown) |
| **CI** | pytest · bandit · pip-audit · npm audit · gitleaks on every PR |

---

## Slide 7 — Security model

| Control | Where |
|---|---|
| Tenant isolation | Postgres RLS — enforced by the **database**, not a remembered `WHERE` clause |
| Least privilege | App connects as `signal_app` — no superuser, no `BYPASSRLS`, no `DELETE` grant |
| Audit trail | Hash-chained, append-only; "who opened this child's record" is answerable |
| IDOR | Uniform `403` for "missing" and "another institution" — existence never leaks |
| CSRF | Origin check on every state-changing route, explicit allowlist, never a wildcard |
| CSP | Per-request nonce; no `unsafe-inline` for scripts |
| Prompt injection | Caretaker text fenced as data; system prompt forbids treating it as instructions |
| PII in prompts | LLM gets age context + observation text — never a name, ID or institution |

Built to OWASP Web / API / LLM Top 10 and a STRIDE threat model (`.ai/brain/THREAT_MODEL*.md`).

---

## Slide 8 — Feasibility: what we have actually built

- **13-feature Phase-1 backlog complete** (FEAT-01 … FEAT-13) + RBAC / admin console.
- **440 backend tests passing** (1 skipped, 1 documented xfail) against **real PostgreSQL** — SQLite is never a fallback because RLS is an acceptance criterion.
- **25 frontend tests**; typecheck / lint / build clean.
- Curated **94-row clinical knowledge base** (ASHA, CDC "Learn the Signs", NIDCD, JCIH 2019, MacArthur-Bates CDI norms, late-talker literature).
- End-to-end verified: login → intake → voice/text session → reasoning loop → graded flag → referral → audit chain intact.
- Runs locally today: `docker compose up -d db`, seeded synthetic tenant + admin, `npm run dev`.

---

## Slide 9 — The R14 divergence (honesty slide)

One acceptance case (`T6`) is deliberately marked `xfail` rather than patched.

The clinical dataset expects `MODERATE`; the literal counting rule computes `HIGH`. The three cited rows — "says *what?* often", "sits close to the TV", "recurrent ear infections" — are **one clinical picture** (otitis media with effusion), not three independent findings.

Resolving it is a **clinical decision**, so it is documented and blocked, not silently fixed. If that test ever starts passing, the divergence was resolved.

---

## Slide 10 — Known limitations (nothing hidden)

- **Password verification not implemented** — gated to `synthetic_only`; the single reason this build must not be exposed publicly (FEAT-12 scope).
- **No consent model** and **no retention / erasure policy** — need legal decisions before code.
- Access is **institution-scoped, not relationship-based**.
- Rate limiting is **in-process** (Redis is the documented path for multi-instance).
- Provider latency (~45s per LLM call on DeepSeek) is under investigation — measured, not guessed.

---

## Slide 11 — Roadmap

1. R14 clinical sign-off (Ayesha / Sami) → flag clustering for correlated evidence.
2. Real-LLM smoke test once provider keys land; model tiering after a timed latency measurement.
3. FEAT-12 password verification → consent model → retention policy.
4. Relationship-based access (scope caretakers to assigned children).
5. Track B hardening: Redis rate limiting, KMS/Vault for the credential master key.

---

## Slide 12 — Team & close

| Role | Name |
|---|---|
| Team lead | **Sami** |
| Member | **Ayesha** |
| Member | **Amaan** |

**SIGNAL** — the observation becomes a record; the record has a response; the response can be proven.
