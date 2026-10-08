# SIGNAL — Full Product Vision (Complete Reference, A to Z)
*1 September 2026 — reflects source product doc v2 + everything decided since*

## A. One-Line Concept

SIGNAL turns a caretaker's spoken description of a child into a structured, explained, confidence-graded flag that routes to a real clinician — built for one untrained caretaker managing many children, with no training required.

## B. The Problem It Solves

- Institutional caretakers (orphanages, shelters) manage dozens of children with no training in developmental norms and no continuity — staff rotate, no one adult watches one child for years.
- The children most often missed are the quiet, non-disruptive ones, not the most severely affected.
- This is a structural/staffing gap, not a caretaker-competence problem.

## C. Market & Beachhead

Real institutional population in Pakistan is tens of thousands of children (not the often-cited 4.2M "orphans" figure, which is a different, much broader UNICEF definition). Key operators: Alkhidmat Aghosh (~1,800 children), SOS Children's Villages, Edhi Foundation, Punjab Child Protection & Welfare Bureau, Sindh Child Protection Authority.

Expansion path: institutional care → under-resourced community clinics/LHW programmes → schools → export markets (Gulf, South Asia, Africa).

## D. Age Groups (Full Range — Eventually 0–18)

| Band | Notes |
|---|---|
| Infants/toddlers (0–3) | Common intake, especially abandoned infants |
| Preschool (4–6) | Phase 1 target band; government Bait-ul-Mal homes |
| School age (6–12) | Phase 2 target; entry age for Punjab's Children's Homes |
| Adolescents (12–18+) | Later phase; Children's Homes and SOS Youth Homes |

## E. All 7 Screening Domains (Priority Order, Full Vision)

| # | Domain | Why it's prioritised |
|---|---|---|
| 1 | Speech/Language delay | Most common, most-missed condition; renamed from "DLD" to avoid an unwarranted diagnostic label under age 4 (ADR-07) |
| 2 | DSED/RAD (attachment disorders) | 20–30x more common in institutional care than the general population — the strongest defensible moat; no competitor screens for this |
| 3 | Hearing impairment (incl. OME/glue ear) | Common, observation-screenable, and decisively treatable |
| 4 | Uncorrected vision/refractive error | Leading cause of childhood vision impairment, massively under-detected, fixable with spectacles |
| 5 | Autism-related social/behavioural signals | Requires sustained one-on-one interaction — hard in group care |
| 6 | ADHD / attention patterns | Documented to be missed specifically in quiet children |
| 7 | Gross motor delay | Supporting observation-screenable domain |

Phase 1 covers only #1 and #3 (Speech/Language + Hearing). The rest are Phase 2+.

## F. Complete Feature List (All Phases Combined)

| Feature | Phase |
|---|---|
| Voice input (Urdu/English) + text fallback | Phase 1 |
| Smart adaptive follow-up questioning | Phase 1 |
| Confidence-graded flag (4-state: High/Moderate/Low-monitor/Insufficient-info) + plain-language explanation | Phase 1 |
| Cited reasoning trail (exact knowledge-base row behind every flag) | Phase 1 |
| Child profile/registration + estimated-age handling (confirmed DOB vs. estimated range) | Phase 1 |
| Per-child case memory + multi-session continuity | Phase 1 |
| Session save/resume (interrupted shifts) | Phase 1 |
| Loop-closing referral record (responsible person, review date, escalation) | Phase 1 |
| Separate safeguarding-escalation pathway (abuse/neglect ≠ developmental flag) | Phase 1 |
| Encryption, role-based access, tamper-evident audit log | Phase 1 |
| Photo input (supporting visual cues only) | Phase 2 |
| DSED/RAD, vision, autism, ADHD domains added | Phase 2 |
| Age range extended to 6–12 | Phase 2 |
| In-the-moment guidance activity for caretakers | Phase 2 |
| Three-agent architecture formalised (Observation/Risk-Reasoning/Explanation as distinct services) | Phase 2 |
| Institution dashboard (open vs. closed flags) | Phase 4 |
| Donor/compliance reporting feed | Phase 4 |
| Formal referral-partner network | Phase 4 |
| Multi-tenant SaaS + offline/low-connectivity mode | Phase 4 |
| **Outcome tracking** (did the clinician confirm or rule out the flag?) — identified as the single biggest missing product capability | Not yet scoped — flagged as high-value addition |
| Lab/blood-screening integration (e.g. congenital hypothyroidism, PKU) | Phase 5, contingent on hospital partnerships |

## G. System Architecture (Full)

- Input layer: voice (Azure STT, ur-PK) + text — voice input never has AI-generated voice output (text-only output, by design)
- Reasoning pipeline: Observation → Risk Reasoning → Explanation, direct multi-call (not LangChain), full-context knowledge injection (not RAG/embeddings) at Phase 1 scale
- Cross-domain rule: Risk Reasoning must check ALL in-scope domains jointly, never domain-isolated — symptom overlap (e.g. hearing loss and language delay share the same surface symptom) makes isolated reasoning unsafe
- Case memory: PostgreSQL, Row-Level Security enforced at the database ROLE level (not just app-code) — audited and found to have a real gap where the app was connecting as a superuser bypassing RLS; fix is a one-line `.env` correction
- Deterministic grading function (not left to the LLM to invent per-call) — modelled on M-CHAT-R/F, ASQ-3, and PEDS
- Tamper-evident, hash-chained audit log — the technical basis of the entire liability-protection business argument
- Provider-agnostic LLM wrapper with model tiering (cheap model for extraction, strongest model for reasoning, mid-tier for explanation)

## H. Business Model — Who Pays and Why

| Tier | Payer | Why they buy |
|---|---|---|
| Primary | Donors, INGOs, grant funders (Alkhidmat, SOS, UNICEF, Save the Children, GSMA) | Want needs surfaced — demonstrates impact, directs resources |
| Secondary | Government child-protection bodies (Punjab CP&WB, Sindh CPA) | Compliance and welfare-monitoring mandates |
| Tertiary | Export SaaS (Gulf, South Asia, Africa) + B2B licensing to clinics/hospitals | Margin; cross-subsidises the domestic social mission |

Key structural point: the institution is the USER, but the payer sits deliberately outside it (donors/grants), because the institution both consents to screening and could be exposed by what it surfaces — a conflict of interest that can be reduced, not eliminated.

Why institutions actually say yes: liability protection via a documented response process (not documented awareness alone — a flag with no recorded action is documented negligence, not protection), donor/grant reporting material, government compliance, and staff burnout relief.

## I. Consent, Safeguarding & Regulatory

- Guardianship for institutionalised children runs through the Guardians and Wards Act 1890 — the institution consenting to screen children it is itself responsible for is a structural conflict needing independent ethics oversight.
- Mandatory-reporting duty (if screening surfaces abuse/neglect signals rather than a developmental concern) must be designed in before any real-data pilot — still an open item with Ayesha/Sami.
- Regulatory target: the US FDA's non-device Clinical Decision Support carve-out (Cures Act §520(o)(1)(E)) — requires transparent, professional-reviewable reasoning, never an opaque score or a diagnosis. This is why the system never outputs a diagnostic label (ADR-07) and every flag must cite its exact basis (ADR-03).
- Pakistan: DRAP (Medical Devices Rules 2017) review needed before any commercial/clinical launch — tracked, not a Phase 1 blocker.
- All Phase 1 data — hackathon and real build — must be synthetic. Hard technical gate, not policy only.

## J. Clinical Validation Path (the real long-term moat)

Not a patent — validation. Benchmark SIGNAL's sensitivity/specificity against a validated instrument (ASQ-3 or MDAT) in a real institutional pilot with clinical oversight, 100–300 children, 1–2 partner institutions, output a published paper. This is what makes the product credible to serious donors and defensible against "an LLM can't do clinical work."

The knowledge base itself — not the app — is the real asset: curated, sourced, versioned clinical content (currently 94 rows across 2 domains, sourced to CATALISE, ASHA, JCIH 2019, Hearing Health Foundation). Any team can rebuild the app in three months; a clinically-curated, expert-signed knowledge base cannot be rebuilt that fast.

## K. Team & Roles

| Role | Owner |
|---|---|
| Domain framing, clinical/scientific grounding, knowledge-base curation, product narrative | Ayesha |
| Clinical grounding, research validation, evidence base | Sami |
| Application build: agent pipeline, STT integration, case memory, web interface | NextaSol (Amaan) |
| Security architecture, data protection, audit and access control | NextaSol (Akasha) |

## L. Roadmap

| Phase | Focus |
|---|---|
| 1 | Hackathon/MVP: 2 domains (Speech/Language + Hearing), ages 0–6, voice+text, adaptive follow-up, confidence-graded flag, case memory, referral loop, safeguarding routing, security baseline. Currently code-complete, pending real-LLM verification and clinical sign-off on the corrected knowledge base. |
| 2 | Depth: add DSED/RAD (the moat), vision, autism, ADHD; extend to ages 6–12; three-agent architecture split; photo input. |
| 3 | Validated pilot: ethics approval, consent/safeguarding protocol, one named institution (Alkhidmat Aghosh primary target), 100–300 children, sensitivity/specificity study, publication. |
| 4 | Commercial: multi-tenant SaaS, RBAC at institution level, donor/compliance dashboards, offline mode, formal referral-partner network, DRAP pathway confirmed. |
| 5 | Expansion: community clinics/LHW programmes, schools, Gulf/South Asia/Africa export, lab/blood-screening integration. |

## M. Competitive Landscape (Why Nothing Else Fits This Use Case)

Every existing tool (ASQ-3, M-CHAT-R/F, Canvas Dx, Gabify/Neurolens, INDIGO/MDAT, Primero/CPIMS+) assumes either a trained professional administers it, or the user already knows the child well over time. None is built for an untrained caretaker meeting a rotating group of children with no shared history — the exact daily condition of institutional caretaking. Gabify (India) is the closest competitor and is moving toward institutional deployments — treat as a live threat, not a distant one.

## N. Key Open Decisions (Business, Not Engineering)

- Engagement structure with Ayesha/Sami — paid contract work vs. milestone-vested equity vs. joint venture vs. licensing.
- IP assignment — to a single jointly-owned entity, never personal joint ownership, with a written interim note before further co-development.
- Hosting and data residency — not yet decided.
- Clinical sign-off from Ayesha/Sami on the scientific corrections made to the v1 knowledge base (currently "best available, not clinically approved").
- The R14/T6 grading tension (OME pattern: rules compute HIGH, dataset expects MODERATE) — a clinical judgement call, deliberately left unresolved in code pending their decision.
