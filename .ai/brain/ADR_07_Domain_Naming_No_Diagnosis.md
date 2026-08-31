# ADR-07: Domain Renamed to "Speech_Language"; No Diagnostic Labels in Output

**Status:** Accepted — pending clinical sign-off from Ayesha/Sami
**Date:** 2026-08-30
**Affects:** `milestones.domain`, `flags.domain`, all agent output text, ADR-05 (which used the old naming)

## Context

Every artifact up to this point used "DLD" (Developmental Language Disorder) as a domain name — in the schema, in the ADRs, in the knowledge base, and in the test conversations. A scientific validation pass identified this as scientifically indefensible for SIGNAL's target population, for two independent reasons:

1. **DLD requires persistence.** CATALISE-2 (Bishop, Snowling, Thompson, Greenhalgh et al., 2017) defines DLD as a language disorder *unlikely to resolve without support*. That judgement generally cannot be made under 3–4 years, because roughly 70–80% of children identified as "late talkers" resolve their expressive delays by school age without therapy. SIGNAL's Phase 1 age band is 0–6 years, so the majority of children it screens are in exactly the range where the label cannot be justified. Applying "DLD" to a 12–36 month old would be an unwarranted diagnosis of a condition most of them do not have.

2. **DLD explicitly excludes hearing loss.** CATALISE reserves "DLD" for language disorder *not* associated with a known biomedical condition, explicitly excluding sensorineural hearing loss (among others). SIGNAL cannot rule out hearing loss — it has no audiometry, and per ADR-05 hearing is a live differential on every language observation. A tool that has not excluded hearing loss is definitionally disqualified from using the term.

Separately, SIGNAL's entire regulatory positioning (source product document §11; ADR-03) rests on being a non-diagnostic screening and triage aid. Emitting a named clinical diagnosis directly contradicts that positioning — it is the single clearest way the product could be reclassified as a regulated device.

## Decision

1. **The domain is renamed from `DLD` to `Speech_Language`** everywhere — `milestones.domain`, `flags.domain`, knowledge base `citation_ref` prefixes (`DLD-*` → `SL-*`), agent prompts, and all UI text.

2. **The system never emits a diagnostic label.** Not "DLD", not "language disorder", not any named condition. Output names the *observation* and grades *urgency*:
   - ✅ "Expressive language below expectation for age" + grade + cited basis + route to clinician
   - ❌ "DLD", "language disorder", "probable autism", any diagnosis
   This holds regardless of how confident the grading logic is, and regardless of the child's age.

3. **Naming a treatable possibility is permitted and encouraged where the pattern is clear** — for example, naming OME (glue ear) as a possible cause when the presentation is ear-pulling plus intermittent responsiveness plus recurrent infections. This is not a diagnosis; it is prompting the correct clinical work-up (otoscopy/tympanometry). The distinction: SIGNAL may say "this pattern is consistent with X, which a clinician can check for," never "this child has X."

## Consequences

- **Positive:** Removes the clearest regulatory-reclassification risk in the product. Aligns the output with what the tool can actually justify — an observation graded for urgency, not a clinical conclusion. Also removes an internal contradiction: ADR-05 requires hearing to be a live differential on every language observation, which is incompatible with using a label that presupposes hearing loss has been excluded.
- **Negative / accepted trade-off:** "Speech_Language" is less punchy than "DLD" in a pitch or demo. That is a presentation cost, not a product cost — and the defensibility gained is exactly the differentiator the product claims over competitors (transparent, clinician-reviewable reasoning rather than an opaque AI verdict).
- **Migration required:** `milestones` and `flags` both carry a `domain` column. FEAT-04 has not been built yet, so the milestones table can adopt the new naming directly. `flags.domain` was defined in TRD §3 with `{DLD, Hearing}` — this must be updated before FEAT-05, and any existing enum/constraint migrated.
- **ADR-05 supersession note:** ADR-05 (cross-domain reasoning) refers throughout to "DLD and Hearing". Its substance is unchanged — read every occurrence of "DLD" there as "Speech_Language".
- **Clinical sign-off outstanding:** as with ADR-06, this correction came from a validation pass rather than from Ayesha or Sami directly, and should be confirmed by them.
