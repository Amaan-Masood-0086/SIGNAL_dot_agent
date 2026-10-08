# Verified engineering status

This supersedes conversational claims that D1–D10 were complete. A model,
column, primitive or passing unit test alone does not finish a product ticket.

## Implemented in this pass

- Migration 0012: optional numeric estimated-age bounds, reference date and
  documented prematurity context. Create/read API persists these fields.
  Structured estimates advance by completed calendar months in the existing
  reasoning pipeline. Legacy free-text ages remain unchanged; no fabricated
  reference dates or gestational ages were backfilled.
- Explicit evidence-state validation including unknown and conflicting reports.
  Absence requires documented observation opportunity. This contract is not yet
  wired into the LLM extraction/persistence path.
- Migration 0013: immutable stored releases enforced by PostgreSQL triggers,
  including UPDATE, DELETE and TRUNCATE. Capture serializes duplicate requests.
- Migration 0014: content-addressed revision storage for all ten V3 domains,
  separate from live V2 milestones. Capture stores all draft entries; a runtime
  query requires both approved status and enabled state. No approval/activation
  endpoint is exposed. Signed approval integration and active-release switching
  remain outstanding.
- A tested urgent-routing primitive ignores turn caps for externally confirmed,
  approved, age-appropriate matches; recipient/escalation configuration required.
  It is NOT connected to live screening or a symptom matcher yet (D8 incomplete).
- Global audit chain allocation serializes concurrent writers. Existing hash
  format preserved. Retention/partition operations remain outstanding.
- Deprecated startup hook replaced with FastAPI lifespan handling.
- CI now runs full PostgreSQL backend tests and frontend unit tests in addition
  to lint/build. CI scanners and hosted pipeline execution remain outstanding.

## Remaining ticket acceptance work

- D1: remove synthetic startup exemption and verify deployed role/grants.
- D2: endpoint coverage audit and retention/partition policy implementation.
- D3: bind actual release/entry revisions at retrieval time; current v2-active
  label and trail hash are not a complete historical KB revision system.
- D4: secret/CVE scanning, reproducible lock installation and hosted CI proof.
- D5: header tests passed; deployment header verification still needed.
- D6: verified signed subset approval, active-release pointer and recorded switch.
- D7: full milestone/flag domain migration plus structural non-developmental
  grading exclusions; draft revision table support alone does not complete it.
- D8: connect urgent matching, persistence, acknowledgement and frontend interrupt
  before ordinary cap/provider checks. Clinical source gaps F1/F4 stay unresolved.
- D9: frontend intake controls and structured evidence extraction/persistence.
- D10: outcome UI, required close-time choice and outcome aggregates.
- Urdu: full language pass pending. Two earlier meaning-changing edits were
  corrected: an action-word example does not require a complete sentence, and
  following an adult's words/gesture is not the child's own gesturing.

V3 remains a draft and is not used by caretaker grading. No clinical approval
has been claimed or generated.

## Verification this pass

Full backend pytest suite completed successfully against a fresh PostgreSQL
database. One known R14 expected failure and one deployment-specific tenant URL
skip remain. Migrations 0012–0014 applied to the local development database.
No live V3 activation was performed. Backend restarted on loopback port 8002.
