# SIGNAL knowledge base v3 — research and clinical review release

**Release:** `signal-kb-v3.0.0-review.1` · **Prepared:** 9 September 2026  
**88 entries · 41 primary-source references · all 94 legacy entries mapped**

## Is release ka matlab

Yeh nayi, editable knowledge base hai: birth se **18th birthday se pehle** tak product coverage, seven planned domains aur separate safety/safeguarding context. Clinical observations source-grounded hain; questions, evidence groups, product age bands aur action enums SIGNAL ke proposed implementation decisions hain.

**Status: research draft, clinical review pending. Live app abhi v2 use karti hai.** v3 ko existing importer se load nahi karna: current DB enums, prompts aur grading engine seven domains, review state aur separate urgency ko interpret nahi karte. Koi database import ya clinical-rule activation is update mein nahi hui.

“Har age covered” ka matlab har month par ek naya medical norm ya tamam pediatric diseases covered hona nahi. Preschool mein sourced milestones hain; school-age/adolescent content functional participation aur referral concerns par based hai. Yeh complete pediatric textbook, diagnostic instrument ya prescribing database nahi hai.

## Files aur editing

| File | Purpose |
|---|---|
| [knowledge_base.json](knowledge_base.json) | Canonical entries: age rules, observation, English/Roman-Urdu question, sources, evidence group, action, review metadata |
| [sources.json](sources.json) | Exact primary URLs, section locator, limitations aur access date |
| [legacy_mapping.json](legacy_mapping.json) | Har v2 citation ka proposed treatment; automatic replacement disabled |
| [REVIEW_INDEX.csv](REVIEW_INDEX.csv) | Spreadsheet-friendly identifiers, scope, sources aur review fields; clinical prose ka second source of truth nahi |
| [CLINICAL_AND_TECHNICAL_GUIDE.md](CLINICAL_AND_TECHNICAL_GUIDE.md) | Interpretation, clinical terminology, limits aur integration contract |
| [CHANGELOG.md](CHANGELOG.md) | Fixed technical gaps, proposed content corrections aur unresolved clinical decisions |

Clinical content edit karne ke liye `knowledge_base.json` use karein. Source registry aur mapping ko saath update karein. Existing published IDs ka meaning silently replace na karein; new revision aur mapping record karein. Review index derived convenience file hai, runtime input nahi.

Har row `needs_clinical_review` hai. Roman-Urdu wording bhi draft translation hai; English source ko Urdu/Pakistani norms ki validation samajhna ghalat hoga. Review fields ko khud se “approved” karne se release activate nahi ho sakti: validator draft-only hai.

## Age aur domain coverage

| Age | Content aur limitations |
|---|---|
| Birth–<2 months | Hearing-screen history, ordinary sound response, care context aur safety; newborn ko later milestone par fail nahi karte |
| 2–<12 months | Sourced 2/4/6/9-month communication, hearing, social aur movement observations |
| 12–<24 months | 12/15/18-month observations, early relationships aur hearing context |
| 24–<36 months | 24/30-month language and movement observations; multilingual language assessment context |
| 36–<60 months | Preschool communication, play, motor aur trained vision-screen interpretation |
| 60–<72 months | Five-year observations plus functional concerns; no automatic ADHD diagnosis |
| 72–<120 months | School participation, comprehension, listening, vision, motor, relationships aur attention |
| 120–<180 months | Increasing educational/social demands, young person's own account aur mental-health context |
| 180–<216 months | Adolescent communication, participation, relationships, attention aur transition support |
| 216 months onward | Outside this release; adult-service transition, no silent extrapolation |

| Domain | Entries |
|---|---:|
| Speech_Language | 27 |
| Hearing | 12 |
| Vision | 6 |
| Motor | 17 |
| Social_Communication | 12 |
| Attention | 5 |
| Attachment | 4 |
| Context | 2 |
| Safety | 2 |
| Safeguarding | 1 |

Context rows do not imply a disorder. Infant attention content explicitly prevents inappropriate diagnostic inference. Attachment content records relationship observations; it does not label RAD/DSED. Acute motor recommendations sourced from NICE under-16 guidance stop at 192 months; this is an explicit source limit, not a claim that older adolescents cannot have emergencies.

## Validator aur tests

From `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts/validate_knowledge_v3.py
.\.venv\Scripts\python.exe scripts/validate_knowledge_v3.py --age-months 25
.\.venv\Scripts\python.exe -m pytest tests/test_knowledge_v3.py tests/test_grading.py -o addopts= -q -ra -p no:cacheprovider
```

On Linux/macOS use the environment's `python` executable. These checks need no database, provider key or paid LLM call. The age preview lists review candidates only: it does not detect symptoms, infer absence or produce a grade.

Verified during this update: **64 tests passed** across the new integrity/semantics tests and existing grading tests. Full PostgreSQL integration and clinical accuracy were not validated in this update.

## Live integration se pehle required work

1. Domain reviewers verify each clinical claim, source scope, action urgency, age threshold and translation. Primary publisher hona local validation ka substitute nahi.
2. Resolve R14 and approve an explicit scoring policy. Evidence groups alone do not decide HIGH versus MODERATE.
3. Implement versioned KB storage, review/activation gates, expanded enums and routes. Keep old citation snapshots readable.
4. Add structured age-reference date, documented prematurity context, evidence states and source/model/rule versions to the application data flow.
5. Add urgent/safeguarding paths that cannot be delayed by the conversation cap. Map recipient, acknowledgement and escalation to verified local services.
6. Run expert-labelled synthetic scenarios, Urdu/English tests, age-boundary cases and PostgreSQL migration tests; compare v2/v3 outputs without overwriting historical flags.
7. Activate only an approved subset after the matching application support is delivered. Consent, retention and pilot approval remain separate requirements.

## Additional acute safety disclosure

`V3-SAFE-002` (severe breathing difficulty/unresponsiveness) is currently sourced only for ages 0–60 months. This is a coverage limit, not a claim that older children cannot have emergencies. Do not activate this acute pathway for ages 60–216 months until a qualified reviewer supplies an age-appropriate source or explicit fallback.

## Source basis

Milestone surveillance is distinct from validated screening; CDC and ASHA both make that distinction. [CDC milestones](https://www.cdc.gov/act-early/milestones/index.html), [ASHA milestones](https://www.asha.org/public/developmental-milestones/).

For clinical concern/referral context this release uses [NICE OME guidance](https://www.nice.org.uk/guidance/ng233/chapter/Recommendations), [AAPOS vision screening](https://www.aapos.org/syndicated/vision-screening), [ASHA multilingual assessment](https://www.asha.org/practice-portal/professional-issues/multilingual-service-delivery/) and the other row-linked references in `sources.json`. UK/US recommendations are not represented as Pakistani law or locally validated norms.
