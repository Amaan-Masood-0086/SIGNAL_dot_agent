# SIGNAL — Project Audit aur Next Steps

**Audit date:** 9 September 2026  
**Branch reviewed:** `feat/admin-onboarding-child-assignment`  
**Scope:** Backend/frontend source, migrations, tests, existing project documentation, `PROJECT_OVERVIEW.md` aur `doc/SIGNAL_Full_Product_A_to_Z.md` ka comparison.

## Overall assessment

SIGNAL ka screening engine kaafi developed hai, lekin complete care-management product abhi nahi bana. Next milestone **screening se recorded action aur outcome tak poora flow** hona chahiye.

`PROGRESS.md` ka “98% complete” full product ki accurate picture nahi deta; woh purane Phase-1 tickets ka status hai. Existing architecture ko dobara banane ki zaroorat nazar nahi aayi. Main work existing features ko reliably connect aur complete karna hai.

Yeh source-code audit aur limited test verification hai, production certification ya clinical validation nahi. Neeche static findings ko live-reproduced defects samajhna theek nahi hoga jahan runtime verification pending likhi hai.

## 1. Abhi kya bana hua hai

| Hissa | Current implementation |
|---|---|
| Child registration | Confirmed DOB / estimated age, profiles, archive/restore |
| Screening conversation | Voice/text, adaptive questions, five-turn limit |
| Reasoning | Observation → joint speech/hearing reasoning → deterministic grading → explanation |
| Evidence | Citation validation, saved reasoning basis, reference changes ka indication |
| Case history | Previous sessions ke flags reasoning mein use hote hain |
| Admin | Institutions/staff/children onboarding, roles, deactivation, assignment, credentials, usage, audit |
| Tenant security | Separate privileged/tenant DB connections aur RLS enforcement checks |
| Referral | Backend create/read/update hai; usable caretaker frontend workflow missing |
| Safeguarding | Separate escalation record banta hai; downstream handling incomplete |
| Production access | Password verification abhi nahi; synthetic demo login |

## 2. Important audit findings

### A01 — Referral loop caretaker ke liye complete nahi

Product ka central promise hai: concern identify hua, kisi ko responsibility mili, action hua aur us ka record bana.

Backend mein referral endpoints hain, lekin frontend mein referral form, pending-referrals list, review workflow ya clinician handoff surface nahi mili. `responsible_person` aur `review_date` optional hain; referral un dono ke baghair ban sakta hai.

“Escalated” date ke hisaab se calculate hota hai; automatic notification/delivery mechanism nahi mila. Clinician ne concern confirm kiya, rule out kiya ya further assessment manga—iska structured outcome model bhi missing hai.

**Next:** Referral creation/confirmation, responsible person, review date, pending/overdue views, clinician handoff aur structured outcome capture ka complete workflow.

**Evidence:** [Referral endpoints](../../backend/app/api/v1/endpoints/referrals.py), [referral schemas](../../backend/app/schemas/referral.py), [referral service](../../backend/app/services/referral_service.py).

### A02 — Safeguarding record aur operational response mein gap

Code abuse/neglect signal ko developmental flags se alag rakhta hai. Lekin service downstream process ko explicitly stub kehti hai. Recipient, acknowledgement, resolution aur overdue handling ka operational flow nahi mila.

UI “being handled” ka impression deti hai; actual implementation filhaal escalation row banati hai. Wording ko actual delivery/handling state se align karna zaroori hai.

**Next:** Approved safeguarding protocol ke mutabiq recipient, acknowledgement, escalation aur resolution workflow; truthful UI status.

**Evidence:** [Safeguarding service](../../backend/app/services/safeguarding_service.py), [session conversation](../../frontend/src/components/features/session-chat/SessionConversation.tsx).

### A03 — Authentication aur account deactivation incomplete

Login any password accept karta hai. Admin privilege DB se verify hoti hai, lekin ordinary authentication dependency signed token ko accept karti hai.

Active-account guard kuch writes par hai, sab par nahi. Child creation, referral writes aur session complete/resume mein woh guard missing hai. Deactivated account ka existing valid token kuch actions kar sakta hai.

**Verification:** Code-level finding; live reproduction database unavailable hone ki wajah se nahi ki.

**Next:** Real credential verification, consistent active-account enforcement, session/token revocation aur role-transition tests.

**Evidence:** [Auth](../../backend/app/api/v1/endpoints/auth.py), [access dependencies](../../backend/app/api/deps.py), [children](../../backend/app/api/v1/endpoints/children.py), [sessions](../../backend/app/api/v1/endpoints/sessions.py), [referrals](../../backend/app/api/v1/endpoints/referrals.py).

### A04 — Assignment responsibility hai, access control nahi

Admin child ko caretaker assign kar sakta hai, lekin same institution ke doosre caretakers abhi bhi usay access kar sakte hain. Migration explicitly kehti hai ke assignment responsibility ke liye hai, permission ke liye nahi.

**Next:** “Assigned staff + shift cover + supervisor” ka clear access model decide aur implement karein. Sirf assigned user ko access dena covering caretaker ka workflow tod sakta hai.

**Evidence:** [Assignment migration](../../backend/alembic/versions/0007_child_assignment.py), [admin assignment endpoint](../../backend/app/api/v1/endpoints/admin.py), [caretaker roster scope](../../backend/app/api/v1/endpoints/children.py).

### A05 — Audit trail mein concurrency aur hash coverage risks

Audit writer last sequence read karke `+1` karta hai. Sequence unique hai, magar allocation ke aas paas locking nahi mili. Do concurrent requests same next number choose kar sakti hain, jis se request transaction fail ho sakti hai.

Hash payload mein `timestamp` aur `institution_id` included nahi hain; un fields ki tampering existing hash verification se detect nahi hogi.

**Verification:** Static findings; parallel DB reproduction pending.

**Next:** Transaction-safe chain append strategy, required audit fields ki hash coverage aur concurrent-write tests.

**Evidence:** [Audit writer/verifier](../../backend/app/services/audit.py), [audit model](../../backend/app/models/audit_log.py).

### A06 — Session recovery aur retry behaviour incomplete

Follow-up questions reload par restore hote hain, lekin final result component state mein hai aur session page usay reload nahi karti. Backend final grade ke baad session automatically terminal state mein bhi nahi le jata.

Session roster/resume entry point frontend mein nahi mila. Existing URL reopen karna aur shift change par pending session discover karna different capabilities hain. Concurrent submissions/retries ke liye session locking/idempotency bhi missing nazar aayi.

**Verification:** Source-level findings; live multi-tab/retry reproduction pending.

**Next:** Persisted terminal outcome, reload recovery, discoverable pending sessions aur duplicate/concurrent request handling.

**Evidence:** [Session UI](../../frontend/src/components/features/session-chat/SessionConversation.tsx), [session page](../../frontend/app/dashboard/sessions/[id]/page.tsx), [reasoning endpoint](../../backend/app/api/v1/endpoints/reasoning.py), [session endpoints](../../backend/app/api/v1/endpoints/sessions.py).

### A07 — Estimated-age handling ke edge cases

Estimated age ka lower bound use hota hai, lekin estimate ke baad guzra hua waqt add nahi hota. `24–30 months` wala child baad ki screening mein bhi 24 months evaluate ho sakta hai.

Intake validation range format/order aur future DOB ko adequately validate nahi karti.

**Next:** Age estimate ki reference date aur time progression define karein; range syntax/order, future DOB aur screening age-scope validation cover karein. Clinical evaluation policy domain team se confirm honi chahiye.

**Evidence:** [Age resolution](../../backend/app/services/risk_pipeline.py), [child schemas](../../backend/app/schemas/child.py).

### A08 — Final explanation language preference disconnected

Final explanation call mein selected `response_language` forward nahi ho rahi. Explanation agent ko caretaker transcript bhi nahi milta. Is liye follow-up Urdu mein hona final explanation Urdu mein hone ki guarantee nahi hai. Server-authored fallback messages bhi English mein hain.

**Next:** Explicit language preference final explanation tak forward karein, auto-language context define karein aur fallback text ki language coverage test karein.

**Evidence:** [Pipeline explanation call](../../backend/app/services/risk_pipeline.py), [explanation agent](../../backend/app/services/pipeline_agents.py).

### A09 — Clinical grading sign-off pending

R14/T6 divergence abhi open hai: dataset MODERATE expect karta hai, deterministic counting rule HIGH produce karta hai. Test isay known `xfail` ke taur par record karta hai.

Deterministic grading reproducibility deti hai; clinical correctness apne aap prove nahi karti. Ayesha/Sami ko expected outcomes aur concern-triggering KB rows approve karni hongi. `SL-RF-022` aur `HEAR-RF-014` mein broad caretaker-concern triggers review ke candidates hain; audit unki clinical validity decide nahi karta.

**Next:** Written clinical decision, approved scenario expectations aur us ke mutabiq rule/dataset updates.

**Evidence:** [Dataset contract tests](../../backend/tests/test_feat05_dataset_contract.py), [knowledge base](../../.ai/brain/knowledge-base-source/signal_knowledge_base_v2.csv).

## 3. Documentation drift

| Document claim | Current code / audit observation |
|---|---|
| `PROJECT_OVERVIEW.md`: admin children register nahi kar sakta | Admin child-creation endpoint aur frontend form maujood hain |
| No deletion path | Admin empty child records delete kar sakta hai; history walay records ke liye archive path hai |
| Full-product document: RLS fix one-line environment correction hai | Current implementation separate DB paths aur fail-closed role verification rakhti hai |
| Model tiering described | Current adapter ek configured model ko tiers ke liye use karta hai |
| `PROGRESS.md`: 98% complete | Purane ticket scope ka claim; full operational product completion nahi |
| Test counts/progress details | Documents mein counts aur migration references inconsistent/purane hain |

**Action:** README, overview, progress aur full-product vision ko ek current implementation matrix ke saath reconcile karein. Vision, implemented features aur verified operational behaviour ko clearly distinguish karein.

## 4. Recommended roadmap

| Order | Work | Completion criteria |
|---|---|---|
| 1 | Current baseline verify + critical correctness fixes | PostgreSQL suite chale; audit concurrency, session reload/retry, age validation aur language forwarding covered hon |
| 2 | Referral + outcome workflow | Flag → confirmed referral → responsible person/date → follow-up → recorded clinician outcome end-to-end chale |
| 3 | Safeguarding operational flow | Named recipient, acknowledgement, escalation status aur resolution record approved handling protocol se match kare |
| 4 | Pilot access/security | Real login, account revocation, agreed assignment/cover permissions, persisted consent aur retention/hosting decisions implemented hon |
| 5 | Clinical/provider evaluation | Approved Urdu/English scenarios real provider par test hon; correctness, failure rate, latency aur cost measured hon |
| 6 | Supervised pilot | Operational ownership aur clinical approvals ke saath agreed pilot scope ready ho |

### Immediate next sprint

**Current reliability fixes aur referral/outcome flow** par focus karein.

1. PostgreSQL available karke full baseline suite aur actual migration state verify karein.
2. Audit append concurrency, session persistence/retry aur inconsistent active-account guards fix karein.
3. Age input validation aur final explanation language forwarding complete karein.
4. Caretaker ke liye referral create/confirm aur pending-referrals workflow banayein.
5. Responsible person, review date aur structured outcome capture implement karein.
6. Main caretaker journey ke browser tests add karein: registration → screening → reload/resume → result → referral → outcome.

New domains, photo input aur 0–18 expansion ko is milestone ke baad rakhein. OpenCode-inspired design reference use karte waqt caretaker ki Urdu readability aur simple workflow ko priority dein.

## 5. Proposed ownership

Yeh division full-product document ki team mapping par based recommendation hai; koi task externally assign ya message nahi kiya gaya.

| Owner | Recommended responsibility |
|---|---|
| Amaan / application team | Application flow, frontend/backend integration, referral/outcome experience aur testing |
| Akasha / security team | Authentication, access enforcement, audit hardening aur deployment security |
| Ayesha / Sami | Clinical expected outcomes, R14 decision, safeguarding protocol aur pilot approval requirements |
| Joint product decision | Consent, retention, shift-cover access, hosting/data residency aur pilot scope |

## 6. Verification actually performed

| Check | Result |
|---|---|
| Frontend unit tests | **25 passed** across three test files |
| Frontend lint | Completed without reported errors |
| TypeScript | `tsc --noEmit --incremental false` completed successfully |
| Selected backend tests, latest run | **115 passed, 1 deselected, 1 known xfailed, 14 setup errors** |
| Backend setup errors | PostgreSQL-dependent tests could not initialize because `SIGNAL_TEST_DATABASE_URL` was unavailable for the run |
| Docker availability | Docker engine unavailable, including outside-sandbox status check |
| Full backend / RLS suite | Not verified in this audit |
| Production frontend build | Not run in this audit |
| Live browser journey | Not verified in this audit |
| Real-provider latency/quality | Not measured in this audit |
| Current remote CI status | Not independently verified; repository contains a CI workflow |

Latest selected backend run covered grading, LLM resilience/retry, output-budget contracts, pipeline agents, synthetic matching and dataset contracts. The setup errors are environment blockers, not evidence of application assertions failing. The known xfail is R14/T6. Historical “all tests passing” statements in older documentation were not treated as fresh verification.

The audit did not change application code, production data or clinical rules. This Markdown file records the findings and recommended next steps.

## 7. Source documents

- [PROJECT_OVERVIEW.md](../product/PROJECT_OVERVIEW.md)
- [SIGNAL_Full_Product_A_to_Z.md](SIGNAL_Full_Product_A_to_Z.md)
- [README.md](../../README.md)
- [PROGRESS.md](../../.ai/brain/PROGRESS.md)
- [Existing remediation backlog](../../.ai/audit/REMEDIATION_BACKLOG.md)
- [CI workflow](../../.github/workflows/ci.yml)

