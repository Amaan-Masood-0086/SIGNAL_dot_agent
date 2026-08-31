# ADR-08: Dual Identity for Knowledge-Base Entries — UUID Primary Key plus Human-Readable citation_ref

**Status:** Accepted
**Date:** 2026-08-31
**Affects:** `milestones` table, `flags.reasoning_trail` citation format, FEAT-04 loader, FEAT-05 reasoning-trail output

## Context

The knowledge base (FEAT-04) ships with stable, human-curated identifiers — `SL-RF-009`, `HEAR-RF-014`, `HEAR-RISK-01` — that clinicians and the domain owners (Ayesha/Sami) use to talk about specific entries. These `citation_ref`s appear in the source CSV, in clinical review conversations, and in any future revision history of the knowledge base.

TRD §4 MUST #8 simultaneously requires every row's primary key to be a UUID v4 (generated application-side) — the house rule that keeps all SIGNAL tables uniform, keeps foreign keys stable under content edits, and avoids sequential-id enumeration.

The two requirements collide in one place: `flags.reasoning_trail`. ADR-03 and ADR-06 require every grade to enumerate the exact knowledge-base entries that produced it. A trail citing `a3f1c9e2-7b4d-4e8a-...` is technically complete and clinically useless — a clinician reviewing a flag cannot look that UUID up in the published knowledge base, cannot discuss it with the domain owners, and cannot verify the citation against the source documents. A trail citing `HEAR-RF-014` is verifiable in seconds.

## Decision

1. **`milestones.id` stays UUID v4** (TRD §4 MUST #8, unchanged) and remains the primary key and the target of any internal foreign keys.

2. **Add `milestones.citation_ref`** — `String(32)`, NOT NULL, UNIQUE, indexed (`uq_milestones_citation_ref` / `ix_milestones_citation_ref`). It holds the human-readable identifier from the source dataset (`SL-M-001`, `SL-RF-009`, `HEAR-RF-014`, `HEAR-RISK-01`).

3. **The loader upserts on `citation_ref`**, not on the UUID. The UUID is generated once at first insert and never changes; a re-run or a content correction reuses the existing row's UUID. `citation_ref` is therefore the stable *content* identity, the UUID the stable *row* identity.

4. **`flags.reasoning_trail` cites `citation_ref`, not the UUID** (refines ADR-03's "cite the milestone_id(s)"). Every graded output enumerates the citation_refs that produced it (ADR-06 sub-rule 3). The UUID remains reachable from the trail by lookup if machine-joining is ever needed, but the clinical surface shows `HEAR-RF-014`.

## Consequences

- **Positive:** reasoning trails are clinician-reviewable and verifiable against the published knowledge base — the exact property the non-diagnostic CDS regulatory positioning (ADR-03, ADR-07) depends on. Knowledge-base content corrections do not invalidate old flags: the UUID FK-style reference is untouched, and the citation_ref is stable by curation policy. The unique index makes loader idempotency a database guarantee, not an application hope.
- **Negative / accepted trade-off:** two identity columns where one would suffice in a greenfield design; a small integrity obligation that every knowledge-base revision keeps citation_refs stable and unique (a curated-dataset invariant the domain owners already maintain).
- **Renaming note:** if an entry is ever split or renumbered in a future dataset revision, the migration of citation_refs is a deliberate, logged data operation — never a silent renumber, since historical reasoning trails cite the old refs.
