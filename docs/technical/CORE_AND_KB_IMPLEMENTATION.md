# Core workflow and knowledge base implementation

## First implementation slice — 2026-09-11

### Core: saved screening recovery

- Session pages now fetch persisted session flags through the existing authenticated backend endpoint and validate the response with the existing schema.
- Reload restores saved grades, explanations and evidence snapshots, including knowledge-base drift notices. It does not rerun the model or reconstruct missing clinical fields.
- A session with saved flags does not offer another screening input. The session can still be completed using its existing control.
- If flags cannot be loaded, the route error boundary handles the failure instead of showing an apparently blank screening history.
- Up to 100 flags are displayed; larger totals are disclosed. This is not full pagination.
- The regression test screens a synthetic observation, reloads, verifies original evidence and confirms no new screening request is made.

### Knowledge base: content-bound review manifest

Run from `backend/`:

```powershell
.venv/Scripts/python.exe scripts/validate_knowledge_v3.py --review-manifest
```

The read-only command prints a deterministic release fingerprint and per-entry fingerprints bound to the entry plus its cited source metadata. It includes complete evidence snapshots, 88 pending clinical/translation reviews, 10 legacy-specific reviews and the unresolved R14 decision. Changes to source limitations invalidate the fingerprints of affected entries.

These hashes detect content changes; they are not signatures, reviewer authentication or clinical approval. No database writes, runtime activation, new medical claims or grading changes occur. The manifest is preparation for version-aware integration, not that integration itself.

## Second implementation slice — 2026-09-11

- Added an institution-scoped, paginated referral queue with flag/status/overdue filters and audit logging. Same-flag create requests serialize on a database row lock and reject an existing open referral.
- Added caretaker referral confirmation, responsible person/review date forms, original evidence, overdue display, status updates and reloadable follow-up pages. These record coordination; they do not send a clinician notification.
- Added persisted reasoning-response snapshots, including follow-up questions, insufficient-information and safeguarding outcomes, plus an authenticated saved-result endpoint.
- Reasoning requests can carry a UUID retry key. Same-key/same-input retries replay the stored response; changed input with the same key is rejected. The browser retains its key across a failed request retry. No cross-reload draft persistence is claimed.
- Session writes serialize turn allocation with reasoning; closed conclusions reject additional turns. Save-only sessions now enforce the five-turn cap. Archived children cannot start new sessions through the backend.
- Added an offline signed-review verification boundary for version-bound clinical/translation evidence subsets. No genuine clinical receipt or approved scoring policy has been supplied, so live V3 grading remains disabled.

The new core integration test runs observation → follow-up → cited result → response recovery/retry → referral → overdue queue → pending capacity → closure → saved history against PostgreSQL with a scripted provider. Browser tests exercise the real Next pages/BFF against an in-memory backend fixture. Neither establishes real-provider clinical accuracy.

The redesign-existing-projects skill guided consistent forms, explicit confirmation, preserved inputs after failure and mobile review.

### Second-slice verification

- Full backend regression run exited successfully against a disposable PostgreSQL 16 instance. R14 remains one documented expected failure. One deployment-specific tenant-URL check was skipped because no deployed tenant URL was supplied; the isolated database RLS tests ran.
- All 7 browser tests passed, including referral lifecycle and mobile follow-up layout. All 25 frontend unit tests passed. Lint and production build passed.
- All 53 focused knowledge-base integrity/approval/review-dashboard tests passed. Synthetic signing keys exist only in tests and confer no real clinical approval.
- The existing project database rejected the old runner's credentials. Its credentials/data were not changed; testing used a separate loopback-bound PostgreSQL instance on port 55439 and a fresh workspace-local pytest temp directory.

## Remaining gates — do not call both tracks complete

- Obtain qualified external clinical and translation decisions, including the ten legacy items and R14. See `knowledge_base/v3/CLINICAL_REVIEW_DECISIONS_REQUIRED.md`.
- Implement and evaluate the actual approved scoring policy before changing the live V3 runtime. The signed-review boundary is not a grading engine.
- Historical non-flag outcomes created before response snapshots cannot be reconstructed reliably. New outcomes are saved; no retrospective invention or backfill occurred.
- Safeguarding workflow ownership/notification and real-provider evaluations still require further work and agreed protocols.
- The live backend must be restarted to expose new endpoints if it is not running with auto-reload. No clinical deployment or authentication change was made.

## First-slice verification (historical)

Verification for this slice: 44 knowledge-base tests passed; both targeted browser tests passed against synthetic fixtures; frontend lint and production build passed. No full PostgreSQL or live-provider evaluation was run in this slice.


## Unchanged boundaries

V3 remains a research draft. R14 remains unresolved. The authentication stub and synthetic-data restriction remain. No deployment or production activation is part of this slice.

## Third implementation slice — versioning and preview sandbox — 2026-09-11

- `knowledge_releases` stores content-addressed, immutable manifest snapshots. Capturing the same hash is idempotent; snapshots cannot be edited in place.
- Admins can list snapshots, compare entry-level added/removed/changed citations, and create a rollback plan. Rollback deliberately does not activate runtime content; it produces a review candidate.
- `/api/v1/admin/knowledge/preview` is a deterministic, read-only V3 sandbox. It filters synthetic observations by age/domain, returns candidate observations, bilingual follow-ups and cited sources, and explicitly returns `clinical_grade: null` and `runtime_enabled: false`.
- Admin UI: **KB preview sandbox** under Administration. It is an inspection tool only; no session, history, referral or live scoring data is written.

Apply migration `0009_knowledge_releases` before using snapshot persistence. Clinical sign-off, translation decisions, R14 resolution and an approved scoring policy are still required before any V3 runtime activation.
