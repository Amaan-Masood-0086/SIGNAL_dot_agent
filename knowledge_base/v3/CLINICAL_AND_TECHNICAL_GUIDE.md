# Clinical interpretation and technical contract

**Research draft, 9 September 2026.** This guide describes the v3 review package and requirements for future integration, not features already running in the web app.

## 1. Observation, screening, diagnosis and action

- **Observation:** a concrete behaviour or documented test result, with observer, context and date.
- **Developmental surveillance:** repeated observation/history over time. A milestone checklist helps structure a conversation.
- **Validated screening:** an instrument evaluated for its intended age, language and population. The SIGNAL row collection is not such an instrument.
- **Diagnosis:** a clinician's assessment, not an LLM label or a count of matched rows.
- **Action:** obtaining appropriate review may be warranted even when diagnostic confidence is low.

Keep three separate outputs in a future engine: `evidence_sufficiency`, `screening_grade` under a signed rule version, and `action_urgency`. Do not convert “needs prompt assessment” into “confirmed disease.” The current v3 schema deliberately has `clinical_grade: null`.

CDC's milestone wording describes skills achieved by most children (75% or more), not a “75th percentile vocabulary score.” Imported average word counts must not become automatic failure thresholds. [CDC two-month checklist and definitions](https://www.cdc.gov/act-early/milestones/2-months.html).

## 2. Age semantics

- All product ages are months; lower bounds inclusive, upper bounds exclusive. At 216 months the child leaves this release's scope.
- `by_age`: an explicit milestone threshold; the review candidate remains available after that birthday until its declared upper bound. A 24-month item is not restricted to exactly month 24.
- `age_band`: descriptive eligibility, often a product organisation choice, not a new developmental norm.
- `any_age`: full product interval. It never means all human ages.
- `threshold_months`: only for sourced milestone observations, never guessed for attention, attachment or adolescent functioning.
- If an estimated interval crosses a threshold, return `age_uncertain`; do not secretly choose a midpoint or assert the skill is delayed.

Future child data should store an age estimate as numeric lower/upper bounds **and a reference date**. The review helper advances both bounds by completed calendar months. It does not backfill existing children or change `RiskPipeline.resolve_age_context`.

Documented prematurity can require adjusted developmental age in early childhood. Keep chronological age for acute-care routing and documented developmental age for milestone interpretation. Gestational age cannot be inferred from appearance or unknown birth history. [AAP prematurity guidance](https://www.healthychildren.org/English/ages-stages/baby/preemie/Pages/Preemie-Milestones.aspx).

## 3. Evidence quality and correlated observations

The future evidence contract should distinguish `present`, `absent_after_observation`, `not_observed`, `unknown`, `not_applicable`, `conflicting_reports` and `previously_present_now_lost`. A model must not turn “I started this shift yesterday” into a negative milestone result.

Record caregiver familiarity, observation opportunities, recent illness, sleep, language access, sensory access and existing accommodations. These are contextual fields, not points in a clinical score.

Each v3 entry has an `evidence_group`. Related fluctuating-listening observations share one group. The helper deduplicates citations and groups explicit evidence, but **does not claim groups are independent and does not resolve R14**. Repeated descriptions of the same observation must not multiply its weight.

Caregiver concern is meaningful and should lead to clarification or assessment. It is not proof of impairment. A previous hearing-screen pass does not rule out a new problem. [CDC childhood hearing guidance](https://www.cdc.gov/hearing-loss-children/about/index.html).

## 4. Language and institutional context

Record all languages and communication modes, including sign and augmentative/alternative communication (AAC). Consider skills across those languages, exposure and access. Code-switching, dialect differences and limited English experience are not automatically disorders. [ASHA multilingual service delivery](https://www.asha.org/practice-portal/professional-issues/multilingual-service-delivery/).

The questions in this release are newly authored prompts, not licensed screening items. Roman-Urdu text is an unvalidated translation draft. Translation review should include clinical meaning, respectful terminology and caretaker comprehension; a model-generated translation is not linguistic validation.

Institutional residence, placement change or limited familiarity does not establish attachment pathology. Review requires developmental and care history, appropriate expertise and the child's context. Never provoke distress, stage separation or encourage a child to leave with a stranger to obtain an observation. [NICE attachment assessment](https://www.nice.org.uk/guidance/NG26/chapter/recommendations), [AACAP attachment information](https://www.aacap.org/AACAP/Families_and_Youth/Facts_for_Families/FFF-Guide/Attachment-Disorders-085.aspx).

## 5. Clinical terminology for implementers

These terms support referral records and professional review; they do not authorise the caretaker or app to perform the examination.

| Term | Meaning and system implication |
|---|---|
| OAE | Otoacoustic emissions: an ear-response measurement used in hearing screening. Record the professional report, not an app-generated pass. |
| ABR | Auditory brainstem response: measured auditory pathway responses. A trained service interprets results. |
| Audiology | Professional assessment of hearing; ordinary response to a voice cannot replace it. |
| OME | Middle-ear fluid without acute infection; observations alone cannot establish it. |
| Tympanometry | Middle-ear function assessment; not a stand-alone measure of all hearing ability. |
| Visual acuity | Measured ability to resolve detail; each eye, test conditions and reliability matter. |
| Photoscreening | Instrument-based professional vision screening, not diagnosis from an uploaded casual photograph. |
| Regression | Loss of a previously demonstrated skill; distinguish loss from never acquiring it. |
| Expressive/receptive language | Communicating language versus understanding it; investigate both and hearing access. |
| Functional impairment | Difficulty participating in actual daily activities; not just being different from peers. |

Hearing-screening terms and follow-up context: [NIDCD newborn hearing](https://www.nidcd.nih.gov/health/your-babys-hearing-screening-and-next-steps). OME assessment context: [NICE NG233](https://www.nice.org.uk/guidance/ng233/chapter/Recommendations). Vision testing context: [AAPOS](https://www.aapos.org/syndicated/vision-screening). Language assessment context: [ASHA](https://www.asha.org/practice-portal/clinical-topics/spoken-language-disorders/).

## 6. Urgent and safeguarding pathways

`immediate_medical`, `urgent_medical` and `prompt_medical` are proposed action-routing categories, not calibrated probabilities or a universal service deadline. They require local clinical review and an operational recipient.

Acute concerns cannot wait for five caretaker turns, complete milestone evidence or a routine follow-up date. The package includes sudden hearing change, sudden vision loss, selected neurological warning signs and separate safeguarding context. It is not an exhaustive emergency triage system. The NICE motor source is under 16, and the acute-illness source is under 5; those limits are preserved.

Never reassure about a current urgent concern because age is estimated or a past screen was normal. Never claim the concern “has been handled” merely because a row was saved. A future implementation must record delivery, acknowledgement and responsibility.

For suspected abuse/neglect, record the account accurately and use approved non-leading communication and local safeguarding procedures. This KB does not establish Pakistani reporting law or supply an unverified emergency number. [NICE child abuse and neglect guidance](https://www.nice.org.uk/guidance/ng76/chapter/recommendations).

## 7. Medical information intentionally not invented

There are no medication doses, treatment regimens, automatic laboratory panels, diagnostic probability claims or made-up norms for every year of age. Lab/newborn metabolic-screen integration remains a separate clinician-led product phase. The package does not reproduce proprietary ASQ, M-CHAT or other instrument items or scoring algorithms.

For school-age and adolescent users, actual communication, learning access, sensory concerns, relationships and daily participation are the focus. Attention concerns require developmental context and multiple settings; rating scales or observation alone do not establish ADHD. [NICE NG87](https://www.nice.org.uk/guidance/ng87/chapter/recommendations). Mental-health concerns require a separate competent pathway. [WHO adolescent mental health](https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health).

## 8. Versioned integration and review requirements

Before runtime use, a reviewed release needs:

1. Named reviewer and review date per clinical change; approved translation and local applicability record.
2. Signed grading-rule version and approved action routes. Clinical sign-off and engineering tests are separate gates.
3. Stable IDs, content digest and source references snapshotted with every result. Historical v2 flags must keep their original basis.
4. Structured evidence states and age-reference handling in prompts and schemas.
5. Cross-domain retrieval across all enabled, approved domains; source scope filtering and no silent expansion beyond age limits.
6. A release activation transaction with rollback, old-row retirement semantics and deployment verification. Legacy upsert alone does not remove obsolete rows.
7. Expert-labelled evaluation, clinically important false-negative/false-positive analysis, referral outcomes and local language validation. Unit-test success must not be presented as sensitivity or specificity.

The existing `grade()` and R14 xfail remain unchanged. The new review package is not loaded by `DEFAULT_CSV_PATH`, and its JSON/CSV metadata cannot be silently stripped by the hardened v2 importer.
