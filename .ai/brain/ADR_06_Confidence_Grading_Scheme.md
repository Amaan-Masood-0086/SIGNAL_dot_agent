# ADR-06: Four-State Confidence Grading Scheme

**Status:** Accepted — pending clinical sign-off from Ayesha/Sami
**Date:** 2026-08-30
**Supersedes:** nothing (this logic did not previously exist in any artifact)

## Context

The delivered knowledge base and every prior artifact specified that SIGNAL outputs a "confidence-graded flag" with Low/Moderate/High levels — but **no artifact ever defined how a set of observations becomes a grade.** How many red flags of what severity produce which level was never written down anywhere. The `severity_if_absent` column was present in the schema but empty for every row.

This meant the Risk Reasoning Agent could not actually grade anything: it would have had to invent its own weighting on every call, producing inconsistent, unreproducible, and unauditable output. A scientific validation pass identified this as the single largest missing component of the product.

Validated screening instruments solve this with published, deterministic rules: M-CHAT-R/F uses score bands (0–2 low, 3–7 medium with a follow-up interview, 8–20 high with immediate referral); ASQ-3 uses three zones including an explicit "monitoring zone" between typical and refer; PEDS sorts parent concerns into risk paths. All share one design principle — deliberately high sensitivity, tiered by urgency, with a follow-up stage that prunes false positives without filtering any child out.

## Decision

A four-state grading scheme, modelled on the above:

| Grade | Trigger | Action |
|---|---|---|
| **HIGH** | Any ONE confirmed HIGH-severity red flag, OR ≥2 confirmed MODERATE red flags within the same domain | Urgent clinician referral |
| **MODERATE** | One confirmed MODERATE red flag, OR a milestone missed at the 75th-percentile threshold plus one supporting observation, OR persistent caretaker worry not meeting a HIGH flag | Routine referral / short-interval recheck |
| **LOW — monitor & recheck** | A single milestone at or just past the edge of normal WITH protective indicators present | Recheck in ~3 months |
| **INSUFFICIENT_INFORMATION** | Caretaker cannot answer the key discriminating items, or has known the child too briefly to judge reliably | Cannot grade — re-administer when a caretaker with sustained daily contact is available |

**Core computation:** `grade = max(highest single-flag severity, count-based rule)`.

**Weighting:** red flags outweigh missed milestones. A red flag is something that should *never* be present (regression, no response to sound); a missed milestone is something *not yet* present, which carries far more normal variation.

**Binding sub-rules:**

1. **Never discharge a borderline case.** There is no "no concern, done" outcome for a child at the edge of normal — the floor is LOW/monitor. This mirrors ASQ-3's monitoring zone and preserves the high-sensitivity design principle: over-refer rather than miss a treatable child.
2. **Never default to LOW when information is missing.** Missing information is `INSUFFICIENT_INFORMATION`, a distinct state — not a weak version of "fine."
3. **Auditability.** Every grade must enumerate the exact `citation_ref`s that produced it. This is the same requirement as ADR-03, now extended from "cite the basis" to "cite the basis *and* show the rule that combined them."
4. **Estimated age modifies grading** (extends ADR-02): evaluate milestones against the *younger* bound of the estimated range before flagging a delay (conservative against over-referral); a borderline delay under age uncertainty grades *down* to monitor; but age-independent red flags — regression, no response to sound, any caretaker hearing concern — grade **unchanged**. "Age uncertain" must be surfaced explicitly in every output.
5. **Always-HIGH regardless of anything else:** any caretaker concern about hearing, speech or language (JCIH 2019 — family concern warrants immediate referral); regression/loss of acquired skills at any age; no babbling by 12 months; no words by 16 months; no two-word phrases by 24 months; no response to sound.
6. **"Passed newborn hearing screening" must not lower a current hearing concern** — roughly 20–30% of childhood hearing loss is late-onset or progressive, and JCIH 2019 requires continued surveillance regardless of newborn screening outcome.
7. **Risk modifiers raise, never lower.** Family history of deafness or parental consanguinity raises a hearing grade (materially relevant in Pakistan, where both consanguinity rates and congenital hearing-loss prevalence are elevated). No modifier may reduce a grade.

## Consequences

- **Positive:** The agent can now produce reproducible, defensible grades. The same observations always produce the same grade, and the rule that produced it can be shown to a clinician — which is what the non-diagnostic CDS regulatory positioning requires. The scheme is explicitly modelled on instruments with published sensitivity/specificity, so the design can be defended by precedent rather than by assertion.
- **Negative / accepted trade-off:** Deliberately high sensitivity means over-referral relative to a specificity-optimised design. This is the correct trade-off for a screening tool where the cost of a miss (an untreated, treatable condition in a child nobody else is watching) far exceeds the cost of an unnecessary clinician review — and it matches how every validated instrument in this space is tuned.
- **Follow-up required:** Cutoffs should be re-tuned once real outcome data exists showing over- or under-referral rates, exactly as ASQ-3 selected its 2-SD cutoff empirically. That is a Phase 3 (validated pilot) activity, not a Phase 1 one.
- **Clinical sign-off outstanding:** this scheme was derived from published instrument design during a validation pass, not authored by Ayesha or Sami. It should be confirmed by them before the demo.

## Open Sub-Question — Found During FEAT-05 Dataset Audit (2026-08-31)

**The count-based rule conflicts with the OME carve-out on a real test case.** Conversation T6 (`signal_test_conversations_v2.csv`) — ear-pulling, says "what?" often, sits close to TV — confirms three MODERATE-severity Hearing red flags (`HEAR-RF-009`, `HEAR-RF-010`, `HEAR-RF-016`). Applying this ADR's literal count rule ("≥2 confirmed MODERATE red flags within the same domain → HIGH") forces a HIGH grade. But the delivered dataset expects **MODERATE**, and `signal_grading_rules_v2.csv`'s own notes say the OME pattern belongs at MODERATE "because the cause is treatable" — so the dataset and the rules CSV agree with each other, and both diverge from this ADR's literal count logic.

Two candidate resolutions, neither implemented yet:
1. **Same-pattern carve-out:** multiple red flags that are manifestations of one identified underlying pattern (OME) count as one finding for grading purposes, not N independent findings.
2. **Explicit OME exception:** hard-code that the specific OME-pattern combination caps at MODERATE regardless of flag count, because the underlying hearing loss it produces is typically mild-to-moderate and fluctuating (not the profile a severe/urgent count-stacking rule was designed to catch).

**Do not implement either speculatively.** FEAT-05 should implement `grade()` exactly as this ADR's literal rule states, and T6 should be marked as a documented known-divergence (expected value pending clinical confirmation) rather than silently adjusted either direction. This question goes to Ayesha/Sami alongside the rest of this ADR's sign-off — see `knowledge-base-source` Open Questions.
