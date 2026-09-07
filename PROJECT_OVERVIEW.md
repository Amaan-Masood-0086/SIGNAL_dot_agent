# SIGNAL — What this project is, and why

> Orientation document. Read this first if you are new to SIGNAL and want to understand
> *what it does and why it exists* before touching the code.
>
> For setup, tests and repository layout see [`README.md`](README.md).
> For the formal decision record see [`.ai/brain/`](.ai/brain/).

---

## 1. What this is, in one paragraph

SIGNAL is a **developmental screening companion** for children aged 0–6 living in
institutional care in Pakistan — orphanages, shelters, welfare homes. An untrained
caretaker describes, in Urdu or English, by voice or by typing, something they noticed
about a child. SIGNAL asks a small number of adaptive follow-up questions, then produces
a **confidence-graded concern with a plain-language explanation and a cited clinical
basis**, and files it into a tamper-evident record that a clinician can review.

It screens two domains only: **speech/language** and **hearing**.

It is a **screening aid, not a diagnostic tool.** It never produces a diagnosis, and the
architecture is built to make that structurally true rather than a disclaimer — see §6.

---

## 2. Why it exists

### The children who get missed are not the obvious ones

Institutional caretakers manage dozens of children with no training in developmental
norms and no continuity — staff rotate, and no single adult watches one child across
years. The children most often missed are not the most severely affected. They are the
**quiet, non-disruptive ones**: the child who does not respond when called from behind,
who says fewer words than the others, who never causes any trouble.

This is a structural gap caused by understaffing and lack of training. It is not a lack
of care.

### Two things make it hard to close

**1. Nobody owns the observation.**
A caretaker notices something, mentions it to a colleague, and it is gone. There is no
record, so nothing happens — and, just as importantly, nothing can later be *shown* to
have happened.

**2. Most of these children have no confirmed date of birth.**
Every developmental milestone chart in existence assumes you know the child's age. Here,
usually, you do not. A tool that demands a DOB is a tool that cannot be used at all.

### What an institution is actually buying

Early speech, language and hearing delays are most treatable when caught early, so the
clinical case is real. But the thing that makes an institution adopt this is the second
half: **a documented concern with a recorded response.**

An undocumented concern is not protection. It is documented negligence waiting to be
discovered. SIGNAL's audit trail — hash-chained and append-only — exists to prove the
institution noticed and acted.

---

## 3. What actually happens when someone uses it

A caretaker opens a child's profile and starts an **observation session** (voice or text).

```
  caretaker says / types something they noticed
              │
              ▼
     Observation Agent          extracts observable signals only
              │                 ("no response to loud sounds")
              │                 never interpretations ("possible hearing loss")
              ▼
      knowledge base            94 curated milestone / red-flag rows,
              │                 speech-language AND hearing retrieved TOGETHER
              ▼
    Risk Reasoning Agent        may cite ONLY those rows. May ask ONE follow-up
              │                 question if the answer would change the outcome.
              │                 Hard stop at 5 caretaker turns.
              ▼
        grade()                 ← deterministic Python, NOT the model
              │
              ▼
   HIGH · MODERATE · LOW-monitor · INSUFFICIENT INFORMATION
              │
              ▼
    Explanation Agent           rewrites it warmly, in the caretaker's own language,
              │                 with no diagnostic label
              ▼
     flag + reasoning trail     every citation_ref that produced the grade,
                                snapshotted with its exact wording at that moment
```

Concretely, the shape of a real exchange:

> **Caretaker:** "He doesn't talk much and doesn't seem to listen."
> **SIGNAL:** "Does he respond when you call him from behind, where he can't see you?"
> **Caretaker:** "No, not really."
> **SIGNAL:** *(HIGH · Hearing)* "What you described should be checked by a clinician
> soon. This is a screening result, not a diagnosis. Basis: HEAR-RF-008, HEAR-RF-013."

The follow-up question is the point. It is chosen because its answer **discriminates**
between two explanations — and delayed speech is the single most important clue to
possible hearing loss. A child whose hearing loss is misread as a speech problem gets
years of the wrong help.

---

## 4. Use cases — who uses it, and for what

### The caretaker (primary user)

The only person who talks to SIGNAL. Typically has no clinical training, may not read
English comfortably, and is mid-shift with other children to look after.

- Registers a child — with a confirmed DOB **or** an estimated age range, never forced
  to guess.
- Opens a session and describes what they noticed, by voice or typing. Both produce an
  identical record; voice is a convenience, never a requirement.
- Answers up to four follow-up questions.
- Receives a graded result and an explanation **in the language they wrote in**.
- Can stop mid-session and resume later — shifts get interrupted, and the context
  survives.

### The clinician (downstream recipient)

Never logs in. Receives a referral and needs to answer one question: *why does this
system think there is a concern?*

That is what the **reasoning trail** is for. Every flag carries the exact knowledge-base
entries behind it — the reference code, what that entry actually says, and where it came
from. The wording is frozen at the moment of grading, so a clinician reading a flag six
months later sees the basis the decision was actually made on, and is told explicitly if
the reference has been revised since.

### The institution

Gets the record. A concern raised, a referral opened with a named responsible person and
a review date, and an escalation if that review date passes. Every step written to an
append-only, hash-chained audit log that can be verified end-to-end and reports the exact
position where tampering first occurred.

### The system administrator

A NextaSol/dev-level role, not a member of any institution that delivers care. Manages
provider credentials, staff roles, the audit log and cost reporting. Deliberately has
**no** ability to register children or run screenings — admins oversee care, they do not
deliver it.

---

## 5. Two things that come up in every conversation

### "What if we don't know the child's age?"

That case is the normal case, so it is modelled directly rather than worked around. A
child is stored as **either** a confirmed date of birth **or** an estimated range —
never both, never a quietly assumed midpoint.

When the age is estimated, screening evaluates at the **younger** bound of the range, and
a borderline delay is graded **down** — because a 30-month-old measured against
24-month expectations produces false alarms, and over-referral in a system with scarce
clinicians is its own harm. Age-independent red flags (a child losing words they used to
have; a caretaker who is worried about hearing) are **unchanged** — those do not become
less concerning because the birthday is uncertain.

### "What if the caretaker doesn't know enough to answer?"

There are four possible outcomes, and none of them is "no concern":

| Grade | Means |
|---|---|
| **HIGH** | See a clinician soon |
| **MODERATE** | Have it checked |
| **LOW — monitor** | Near the expected range; recheck in about three months |
| **INSUFFICIENT INFORMATION** | Not enough to grade — repeat with someone who knows the child daily |

`INSUFFICIENT INFORMATION` is **not** a reassuring result, and the system is built so it
can never be rounded up into one. A caretaker who started last week and barely knows the
child gets this outcome, correctly — and is told what to do about it.

---

## 6. The design decisions that define the product

These are the choices that make the difference between a chatbot and a clinical
instrument. Each has a full decision record in `.ai/brain/`.

**The grade is code, not the model.** The LLM extracts signals, cites evidence and asks
follow-up questions. It never picks the grade. A deterministic Python function does,
from written rules — so the same evidence always produces the same outcome, and the
outcome is auditable without asking a model why.

**The model may only cite what it was given.** The full in-scope knowledge base is
injected into the prompt, and every citation the model returns is validated server-side
against exactly that set. A clinical claim recalled from training data is rejected
outright, not shown with a caveat.

**Speech and hearing are always checked together.** There is no way to query one domain
alone — the interface for it does not exist. Hearing loss presenting as language delay is
the single misattribution this product exists to prevent, so it is prevented structurally.

**No diagnostic labels, ever.** "DLD", "language disorder", "autism" and similar terms
are scrubbed from model output with a safe server-authored replacement. Naming a
*treatable possibility* ("consistent with glue ear, which a clinician can check for") is
allowed; naming a condition is not.

**Abuse and neglect are not developmental flags.** Safeguarding signals route out of the
screening pathway entirely, into a separate table via a separate service with no shared
write path. A concern about how a child is being treated is not a milestone.

**A referral cannot auto-populate.** It requires an explicit caretaker confirmation step,
enforced at the service layer — not just a checkbox in the UI.

**Every institution's data is isolated by the database, not by the code.** The
application connects as an unprivileged role under Postgres row-level security, so a
handler that forgets its filter returns nothing rather than another institution's
children.

---

## 7. What it deliberately does not do

- **No diagnosis.** Ever. It routes to a clinician.
- **Only two domains** — speech/language and hearing. Not autism, ADHD, vision or motor.
- **Only ages 0–6.** Rows for older children exist in the dataset and are excluded from
  every query.
- **No photo input, no offline mode, no donor reporting feed** — all explicitly out of
  Phase 1 scope.
- **No real children's data.** The build runs under a hard `ENVIRONMENT=synthetic_only`
  gate enforced at the application layer, and refuses to mint a login token outside it.

---

## 8. Where the project actually stands

**Built and tested:** the entire Phase-1 feature backlog — voice and text capture,
the adaptive reasoning loop, graded flags with cited trails, case memory across
sessions, save/resume, referrals with escalation, the safeguarding pathway, role-based
access, the admin console, and the audit trail. 429 backend tests run against real
PostgreSQL (never SQLite — row-level security cannot be validated on it), plus 17
frontend unit tests.

**Not built, on purpose:** password verification. Phase-1 login is a stub that accepts
any password, because implementing it would break the seeded demo accounts before the
demo. This is the single most important thing to know before pointing this at anything
real.

**Open, waiting on a decision rather than on engineering:**

| Item | Blocked on |
|---|---|
| One clinical grading divergence (`R14`) | Clinical sign-off — deliberately pinned as a known divergence, not guessed at |
| Consent model | A legal/clinical decision. Voice consent is a UI checkbox today and is not persisted |
| Retention & erasure policy | A policy decision. There is no deletion path — children are *archived*, never deleted |
| Relationship-based access | Today every staff member at an institution can see every child there |
| Response latency | ~45s per model call against the current provider; needs one measurement before optimising |

The full ranked list, with effort estimates, is in
[`.ai/audit/REMEDIATION_BACKLOG.md`](.ai/audit/REMEDIATION_BACKLOG.md).

---

## 9. If you only remember three things

1. **It screens; it does not diagnose.** Every architectural decision defends that line.
2. **The record is the product.** A grade nobody can review, six months later, is worth
   nothing — which is why the reasoning trail and the audit chain are first-class
   features, not compliance decoration.
3. **The hard case is the normal case.** No confirmed date of birth, an untrained
   observer, an interrupted shift, a caretaker who reads Urdu. The system is designed
   around those conditions rather than degraded to cope with them.

---

## Further reading

| Document | What it holds |
|---|---|
| [`README.md`](README.md) | Setup, running locally, tests, repository layout |
| [`.ai/brain/PROJECT_BRIEF_SIGNAL_2026-08-28.md`](.ai/brain/PROJECT_BRIEF_SIGNAL_2026-08-28.md) | Formal scope, users, open items |
| [`.ai/brain/TRD_SIGNAL_2026-08-28.md`](.ai/brain/TRD_SIGNAL_2026-08-28.md) | API contracts and data model |
| [`.ai/brain/ADR_*.md`](.ai/brain/) | Every architectural decision, with its reasoning |
| [`.ai/brain/THREAT_MODEL_SIGNAL_2026-08-28.md`](.ai/brain/THREAT_MODEL_SIGNAL_2026-08-28.md) | Security model and trust boundaries |
| [`.ai/brain/PROGRESS.md`](.ai/brain/PROGRESS.md) | Current state, session log, exact stopping point |
| [`.ai/audit/AUDIT_REPORT.md`](.ai/audit/AUDIT_REPORT.md) | Principal-engineer code audit and findings |
