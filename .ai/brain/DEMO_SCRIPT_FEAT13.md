# SIGNAL — Demo Script (FEAT-13)

**Maps 1:1 to PROJECT_BRIEF §11 success criteria:**
*"A caretaker can speak a description in Urdu or English, be asked at least one adaptive follow-up question that materially changes the output, receive an explained confidence-graded flag with a cited reasoning trail, and have that flag plus its loop-closing referral record persist to the child's case record — visible to a different session on a later date, proving continuity."*

## 0. Setup (2 min, before recording)

```powershell
# DB + data
docker compose up -d db                                    # or scripts\start_db_container.ps1
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\ingest_knowledge_base.py   # 94 rows (idempotent)
.\.venv\Scripts\python.exe scripts\seed_admin.py --email root@signal.example
.\.venv\Scripts\python.exe scripts\seed_synthetic_tenant.py

# Optional (real LLM; without keys the deterministic synthetic reasoner runs):
#   add LLM_PROVIDER / LLM_API_KEY / LLM_MODEL to backend\.env
#   then verify: .\.venv\Scripts\python.exe scripts\smoke_feat05_llm.py

# Start (backend on 8002; frontend reads BACKEND_URL=http://localhost:8002)
uvicorn app.main:app --port 8002 --no-server-header
cd ..\frontend; npm run build; npm start
```

## Act 1 — Intake (proves ADR-02 dual-age)

1. Log in: `synthetic-staff@signal.example` (any password — Phase-1 stub).
2. Dashboard → **Register a child**: "Ayan", **Estimated age** mode, range `8-10 months`, note "intake worker estimate".
   *Point at the amber banner: estimated age downgrades age-dependent checks — ADR-02.*

## Act 2 — Session 1: voice/text screening + adaptive loop (the §11 core)

3. Open a **text session** (or voice if Azure STT is configured — same flow).
4. In **"Ask SIGNAL about what you noticed"** type:
   `He doesn't turn around even when I clap loudly behind him`
5. SIGNAL asks a **follow-up question** (e.g. reaction to a door slam). Answer:
   `No, he doesn't seem to notice`
   *Narrate: the follow-up materially changed the outcome — without the answer the loop cannot confirm the red flag (FEAT-06 acceptance is pinned by tests).*
6. Conclusion card appears: **HIGH — Hearing**, plain-language explanation, citation chips (e.g. `HEAR-RF-003`), **"Age is an estimate"** badge.
   *Narrate ADR-07: no diagnosis is named — observation + urgency + route to clinician.*

## Act 3 — Loop-closing referral (FEAT-10)

7. Create the referral for the flag (API):
   `POST /api/v1/flags/{flag_id}/referral` with `{"caretaker_confirmed": true, "responsible_person": "Sister Ayesha", "review_date": "<+2 weeks>"}`
   *Narrate: without `caretaker_confirmed: true` the server refuses (409) — a referral can never auto-populate.*
8. (Optional flourish) set `review_date` in the past → `GET /api/v1/referrals/{id}` shows `escalated: true`.

## Act 4 — Session 2, later date: continuity (FEAT-07)

9. Start a **second session** for Ayan. Type a new observation
   (`Still doesn't react to sounds`) and ask SIGNAL again.
10. Open dev tools / API response: the reasoning ran with **CASE MEMORY** —
    the prior session's flag rides in the agent context, and the result
    carries `prior_flags`. The child profile's **Screening history** card now
    lists BOTH results; expand **"Why — the cited basis"** on the flag:
    description + source of every citation (clinician-reviewable, ADR-03/08).

## Act 5 — Admin panel tour (RBAC ticket)

11. Log in as `root@signal.example` (seeded admin).
12. `GET /api/v1/admin/staff` — cross-institution staff directory; deactivate/reactivate (soft delete, audit-logged).
13. `GET /api/v1/audit_log` (filters) + `GET /api/v1/audit_log/integrity` → **"chain_intact": true** — the liability-protection story.
14. `GET /api/v1/admin/providers` — configured/not-configured cards, **no key values anywhere** (ADR-09); `POST /admin/providers/stt/test` if Azure is configured.
15. `GET /api/v1/admin/usage` + `GET /api/v1/usage/me` — cost-DoS visibility (every STT/LLM call logged).
16. Negative proof for the judges: with the caretaker token, `GET /api/v1/audit_log` → **403**.

## Evidence capture (hackathon grading note)

- Screen-record Acts 1–5 (any capture tool) — the video deliverable.
- Keep the terminal visible during setup to show the test suite line:
  `scripts\run_backend_tests.ps1` → **294 tests: 293 passed, 1 xfailed (R14 known divergence, reason printed)**.
- Save one `GET /audit_log` page and the `/integrity` response as screenshots.
- Qoder-usage evidence: this repo's `.ai/brain/PROGRESS.md` session log documents every ticket built agent-assisted, TDD-style.

## Known caveats to say out loud (honesty beats overclaiming)

- T6 (OME): pipeline grades HIGH per ADR-06's literal rule; dataset says MODERATE — R14 pending clinical sign-off (visible in every test run).
- Without LLM keys the demo runs on the deterministic synthetic reasoner (demo-grade scenario matching, documented limitation).
- Phase 1 is synthetic-data-only by a hard environment gate — no real child data path exists.
