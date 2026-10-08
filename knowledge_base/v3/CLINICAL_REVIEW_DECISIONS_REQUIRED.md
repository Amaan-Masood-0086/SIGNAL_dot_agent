# Required external clinical decisions

Status: NOT APPROVED. Prepared 2026-09-11. This file does not resolve R14 or authorize activation.

## R14: the decision that cannot be inferred from a source citation

Legacy T6 records ear-pulling, repeated requests for repetition and sitting close to the television. Its three moderate hearing references (`HEAR-RF-009`, `HEAR-RF-010`, `HEAR-RF-016`) trigger HIGH under ADR-06's count rule, while the dataset expects MODERATE. The existing strict expected-failure test must remain until an authorized reviewer approves an explicit rule and its expected cases.

NICE NG233 identifies hearing difficulty, language delay and ear discomfort as possible OME presentations, and recommends formal assessment when OME is suspected. Assessment includes examination, hearing testing and tympanometry; coexisting causes of hearing loss must be considered. These recommendations do not define SIGNAL's HIGH/MODERATE scoring labels. The three-month reassessment recommendation concerns established OME with hearing loss, not an automatic waiting period for an unassessed caretaker report. [NICE NG233, sections 1.2–1.3](https://www.nice.org.uk/guidance/ng233/chapter/Recommendations).

Access note: direct page retrieval returned HTTP 403; the publisher's indexed recommendations were available and checked. This is not a complete independent clinical review.

Reviewer must supply:

1. The correct action/urgency for T6, distinguishing suspected presentation from confirmed diagnosis.
2. Whether correlated findings should be combined and the precise evidence groups, exceptions and rationale.
3. Treatment of missing discriminating information and independent concerning findings.
4. Expected outputs for T6, each finding alone, duplicate findings, additional independent findings, age uncertainty and insufficient information.
5. An approved, versioned scoring-policy document. A blanket instruction to make T6 green is insufficient.

No OME-specific downgrade or severity cap has been implemented.

## Ten legacy items requiring individual dispositions

For every row, record retain/rewrite/exclude, exact replacement wording, applicable age semantics, precise primary-source locator, non-equivalence limitations and follow-up interpretation. These questions concern the legacy claims; they are not new medical recommendations.

| Legacy ID | Claim needing review | Required decision |
|---|---|---|
| SL-M-003 | Different cries for different needs | Is this usable as a scored milestone, or contextual observation only? |
| SL-M-010 | Understanding “no” and “bye-bye” | Confirm exact age/source and distinguish the two observations. |
| HEAR-M-011 | Understanding “no” | Resolve duplication with language evidence and hearing interpretation. |
| HEAR-M-013 | Pointing to named objects | Confirm age applicability and whether this is hearing evidence. |
| SL-M-025 | Asking questions | Specify the actual question types and supported threshold. |
| SL-M-030 | Answering “why/how” | Verify the claimed 60–72-month scope and normative interpretation. |
| SL-RF-014 | Echoed speech without spontaneous language | Define context, follow-up and non-diagnostic interpretation. |
| SL-RF-020 | Word-finding/comprehension difficulty | Review preschool wording separately from school-age candidates. |
| HEAR-RF-011 | Watching the speaker's mouth | Review whether/how to capture this without inferring compensation. |
| HEAR-RF-012 | Voice volume differing from peers | Validate the age boundary and specificity of the observation. |

Current candidate mappings remain in `legacy_mapping.json`; none is an automatic replacement. No item above is marked approved by this document.

## Review receipt and integration boundary

`backend/app/services/knowledge_approval.py` verifies an external Ed25519-signed review receipt against a deployment-owner-supplied trusted reviewer key and exact release/entry fingerprints. Clinical and translation decisions are separate. Unknown keys, future dates, altered content, duplicate entries and missing legacy decisions are rejected.

The reviewer identity/credentials, review document, scoring policy and R14 decision document must be supplied externally. Test-only generated keys and synthetic receipts are not clinical approvals. The repository contains no real reviewer signing key or approved receipt.

A successful receipt returns only the reviewed evidence subset, still with `runtime_enabled: false`. It is not a medical grade. Approved scoring-policy implementation, expert-labelled regression evaluation and explicit deployment approval are still required before the live pipeline can change.
