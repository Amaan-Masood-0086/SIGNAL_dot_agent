# SIGNAL — Deep Code Audit

> **STATUS 2026-09-02 (post-remediation):** F1, F2 (throttle), F3, F4, F7, F8,
> F10, F11 are **FIXED and covered by tests**. F5 (consent), F6 (retention /
> erasure), relationship-based access, and full password verification remain
> open — each needs a clinical or legal decision before code, not more code.
> Backend suite after the fixes: **385 passed, 1 skipped, 1 xfailed (R14)** — 387 collected.
> See `REMEDIATION_BACKLOG.md` for what is left and why.

**Date:** 2026-09-02 · **Mode:** STANDARD · **HEAD:** `c8a4dfe` (working tree dirty)
**Auditor:** principal-engineer review, static analysis + live probing of the running dev stack
**Fix policy applied:** report-only (uncommitted changes present — no auto-fix permitted)

---

## 1. Executive summary (Roman Urdu)

SIGNAL ek **clinical decision-support** product hai — orphanage ke bachchon ki speech,
language aur hearing screening. Iska core engineering **acha hai, aur kuch jagah
misaali hai**: har flag ke saath cited knowledge-base basis jata hai, grading logic 13
real conversations ke dataset se test hoti hai, aur ek known clinical divergence (R14)
ko chhupane ke bajaye `xfail` marker ke saath dastavez kiya gaya hai. Yeh us discipline
ki nishani hai jo zyadatar startups mein nahi hoti.

Lekin **ek structural khaami baqi sab par bhaari hai**: database mein tenant isolation
(Row-Level Security) poori tarah **bana hua, forced, aur tested hai — magar chalti hui
app usay bypass kar rahi hai**, kyunki app `signal` role se connect karti hai jo
superuser hai aur `BYPASSRLS` rakhta hai. Matlab jo do-parti suraksha design ki gayi
thi, us ki DB waali parat **abhi zinda nahi hai**. Aaj data leak nahi ho raha kyunki
application code khud `WHERE institution_id = ...` lagata hai — lekin us ek parat mein
ek bhi bug, ya ek SQL injection, ab poore system ka data khol dega, sirf ek institution
ka nahi.

Doosri baat jo clinical product ke liye ahem hai: **audit log sirf likhna record karta
hai, parhna nahi.** Saat endpoints bachchon ka health data return karte hain aur ek bhi
log nahi hota — admin ka cross-institution roster bhi nahi. Product ki apni dalil yeh
hai ke "documented response hi liability protection hai", lekin "is bachche ka record
kisne dekha?" ka jawab abhi mumkin nahi.

**Go / No-go:** Pilot ke liye **conditional go** — P1 list theek karne ke baad. Aaj
public internet par nahi jaana chahiye, kyunki password verification abhi stub hai
(koi bhi password chalta hai) aur wo tunnel abhi Public hai.

**Remediation estimate:** P1 set ≈ **3–5 din**. P1+P2 ≈ **2–3 hafte**.

---

## 2. Three structural defects

### S1 — Defence-in-depth built, then bypassed at the connection string
`0001_initial_schema.py` RLS ko `ENABLE` **aur** `FORCE` karta hai, ek unprivileged
`signal_app` role banata hai, `audit_log` par sirf `INSERT,SELECT` deta hai
(append-only), aur `tests/integration/test_postgres_rls.py` sabit karta hai ke yeh sab
kaam karta hai. Phir `backend/.env` app ko `signal` role se joड़ deta hai —
`rolsuper=true, rolbypassrls=true`. `FORCE ROW LEVEL SECURITY` sirf **table-owner** ki
chhoot khatam karta hai; `BYPASSRLS` superuser phir bhi bypass karta hai.

Iska natija sirf tenant isolation nahi: `audit_log` ka append-only DB-level guarantee
bhi inert hai, aur `children` par `DELETE` na dene wali grant bhi.

**Ajeeb baat:** `config.py:31` ka default **sahi hai** (`signal_app`). Sirf `.env`
usay override kar raha hai.

### S2 — The audit trail records writes, not reads
15 audited actions, sab writes. Koi read audit nahi. Clinical domain mein "who viewed
this record" ek compliance-forced requirement hai, feature nahi.

### S3 — Nothing enforces the project's own Definition of Done
`CLAUDE.md` pip-audit, bandit, npm audit, gitleaks, trivy aur pinned versions maangta
hai. Repo mein **koi CI nahi** (`.github/workflows` absent), koi scanner configured
nahi, aur `requirements.txt` ka har package `>=` floating hai. Rules likhe hain, lagu
koi nahi karta.

---

## 3. Top findings by business impact

| # | Finding | Sev | Impact | Confidence |
|---|---|---|---|---|
| F1 | RLS inert at runtime — app connects as superuser with BYPASSRLS | P1 | Critical | Confirmed |
| F2 | Auth accepts any password; no rate limit, no lockout on `/auth/token` | P1 | Critical | Confirmed |
| F3 | No read-access audit on 7 endpoints returning child health data | P1 | High | Confirmed |
| F4 | No CI, no security scanning, backend deps unpinned | P1 | High | Confirmed |
| F5 | Reasoning trails not reproducible — no KB version recorded per flag | P1 | High | Confirmed |
| F6 | No consent model and no erasure/retention path for child data | P2 | High | Confirmed |

---

## 4. Findings detail

### F1 · RLS is inert at runtime — P1 · Critical · Confirmed
**Where:** `backend/.env:2`, `backend/app/api/deps.py:92-110`, `alembic/versions/0001_initial_schema.py:279-296`

Live proof:
```
role=signal      super=True  bypassrls=True   <- app connects as this
role=signal_app  super=False bypassrls=False  <- intended role, exists, correct grants
children  rls_enabled=True rls_forced=True owner=signal
```
`app/` mein `SET ROLE signal_app` ya `set_config('app.institution_id', ...)` kahin nahi.

**Failure scenario:** kisi bhi list/detail handler mein `WHERE institution_id` chhoot
jaye (ya ek SQLi ho), to blast radius poora database hai — sirf ek institution nahi.
Aaj yeh isliye nahi phata kyunki har handler khud filter karta hai; wo ek insani
discipline hai, enforced boundary nahi.

**Fix:** `DATABASE_URL` ko `signal_app` par le jao, aur `get_db` mein per-request
`set_config('app.institution_id', <jwt claim>, false)` set karo. Rukawat: `get_db`
ke paas abhi staff context nahi — dependency order badalni padegi. Effort: **1–2 din**
(migration nahi chahiye, role aur grants pehle se mojood hain).

### F2 · Authentication is a stub with no rate limit — P1 · Critical · Confirmed
**Where:** `backend/app/api/v1/endpoints/auth.py`

Password field accept hota hai aur **verify kabhi nahi hota** (FEAT-12 scope, docstring
mein saaf likha hai). Role email se milta hai — jo `root@signal.example` likhega usay
admin token milega. `/auth/token` par koi rate limiter nahi (baaki 5 surfaces par hai),
koi lockout nahi.

`ENVIRONMENT=synthetic_only` gate isay production se rokta hai — yeh acha rail hai.
Lekin **aaj wo dev tunnel Public visibility par khula hai**, to yeh gap abhi live hai.

**Fix (aaj):** tunnel Private karo. **Fix (asli):** FEAT-12 — argon2id/bcrypt, lockout,
`/auth/token` par 5 req/5 min. Effort: **2–3 din**.

### F3 · Reads are never audited — P1 · High · Confirmed
**Where:** `children.py:75,106` · `flags.py:69,82,114` · `sessions.py:121,224` · `admin.py:179`

15 audited actions, sab writes (`child.create`, `session.create`, `flag.create`…).
Read endpoints — including admin ka cross-institution roster — koi trail nahi chhodte.

**Fix:** `AuditService` already mojood hai; read handlers par `action="child.read"`
waghera add karo. Sochne ki baat: list endpoints par volume — per-record vs per-query
logging ka faisla karna hoga. Effort: **1 din** + retention policy ka faisla.

### F4 · No CI and unpinned backend dependencies — P1 · High · Confirmed
`.github/workflows` absent. `requirements.txt` ka har entry `>=` (e.g. `fastapi>=0.115`)
— koi lockfile, koi hashes nahi. Frontend behtar hai: `package-lock.json` committed hai,
halanke `package.json` mein `^` ranges hain.

Do installs alag alag din par alag dependency tree denge — ek clinical product mein.
**Fix:** `pip-compile`/`uv lock` se pinned requirements, phir GitHub Actions mein
pip-audit + bandit + npm audit + gitleaks. Effort: **1 din**.

### F5 · No consent model, no erasure path — P2 · High · Confirmed (absence)
Backend mein lafz "consent" kahin nahi (mic consent sirf frontend UI checkbox hai, kahin
persist nahi hota). Koi `DELETE` endpoint nahi siwaye credential soft-delete ke.
Clinical retention vs erasure rights ka koi documented resolution nahi.

Yeh **absence** findings hain — code inhe dikha nahi sakta, sirf domain matrix se milte
hain. Effort: design decision pehle, phir **3–5 din**.

### F6 · Access is institution-scoped, not relationship-based — P2 · Medium · Confirmed
Institution ka har caretaker us institution ke **har** bachche ka record dekh sakta hai.
Clinical standard "assigned clinician" hai. 200-bachchon ke institution mein yeh
minimum-necessary access nahi.

### F7 · Header gaps — P2 · Medium · Confirmed
Live response par verify kiya: `X-Content-Type-Options`, `Referrer-Policy`,
`Permissions-Policy`, `X-Frame-Options`, `HSTS` **maujood hain** (`next.config.ts` sahi
kaam kar raha hai). Lekin:
- **`Content-Security-Policy` list mein hai hi nahi** — `CLAUDE.md` isay maangta hai
- **`X-Powered-By: Next.js`** leak ho raha hai
- **Backend API koi security header nahi bhejta**, aur `server: uvicorn` leak karta hai
- Backend responses par `Cache-Control` nahi — PHI JSON ke liye `private, no-store` chahiye

Effort: **2 ghante**.

### F8 · Per-request engine creation — P2 · Medium · Confirmed
`deps.py:102` har request par naya `Engine` banata hai aur dispose karta hai — koi
pooling nahi, har request par naya TCP+auth handshake. Docstring isay "skeleton-grade"
maanta hai. Load par yeh pehli cheez hai jo tootegi.

*(Audit ke dauran maine ek 15-second connection penalty measure ki thi — wo Postgres
container down hone ka artifact tha, code ka defect nahi. Container healthy hone par
`localhost` 0.025s hai. Finding withdraw.)*

### F9 · Free-text PHI reaches a third-party LLM — P2 · Medium · Likely
Prompt construction **acha hai**: `pipeline_agents.py:153` sirf age context aur fenced
observation text bhejta hai — **na naam, na ID, na institution**. Prompt-injection
fencing bhi maujood hai (OWASP LLM01).

Risk yeh hai ke caretaker free text mein naam likh de ("Ahmed doesn't turn…") — wo
seedha third-party LLM (DeepSeek) ko chala jayega. Koi redaction layer nahi, aur koi
data-processing agreement documented nahi.

### F10 · `frontend/.env.example` is gitignored — P3 · Low · Confirmed
`frontend/.gitignore` mein `.env*` hai, jo template ko bhi ignore kar deta hai. Sirf
`backend/.env.example` committed hai. Naye developer ko frontend ka koi env template
nahi milta — including wo `APP_ALLOWED_ORIGINS` jo abhi add hui.
**Fix:** `!.env.example` add karo. Effort: **2 minute**.

### F11 · Reasoning trails are not reproducible across knowledge-base changes — P1 · High · Confirmed
**Where:** `flags` table (no KB version column) · `scripts/ingest_knowledge_base.py`
(upsert keyed on `citation_ref`) · `services/knowledge.py`

`flags` sirf `reasoning_trail` (citation refs) store karta hai — **kaunsa knowledge-base
version tha, yeh kahin record nahi hota.** Ingest `citation_ref` par upsert karta hai, to
agar kisi milestone ka `description` badla, to **chhe mahine purana flag ab aaj ka matn
dikhayega** — wo nahi jo us waqt us grade ki bunyad bana tha.

Domain matrix isay do jagah maangta hai: *"Version pinning of reference data"* (SAF) aur
*"Provenance recorded per result"* (TS).

**Kyun yeh product ke liye normal se zyada ahem hai:** SIGNAL ki poori regulatory aur
liability dalil yeh hai ke har flag ki bunyad **reviewable aur documented** hai. Agar wo
bunyad baad mein khamoshi se badal sakti hai, to "documented response" ki qeemat kam ho
jati hai — aur audit log ka hash chain bhi isay nahi pakadta, kyunki chain flag row par
hai, us milestone text par nahi jise wo cite karta hai.

**Fix:** `flags` par `kb_version` (ya per-entry snapshot of the cited text) record karo,
aur ingest ko append-only versioned banao — `citation_ref` par overwrite ke bajaye naya
version row. Effort: **2–3 din**. Yeh sirf compliance nahi — yeh product ka asset hai.

---

## 5. What this codebase does well

Audit mein yeh likhna zaroori hai, kyunki yeh dohrane laayak hai:

- **Reasoning trail with cited basis** — har flag knowledge-base rows se judi hai
  (`citation_ref` + description + source). Regulatory CDS carve-out isi par tika hai.
- **Clinical logic tested against a real dataset** — 13 caretaker conversations
  end-to-end, contract-pinned. Clinical arithmetic ka untested hona P1 hota; yahan nahi.
- **R14 divergence handled honestly** — dataset aur ADR-06 ke conflict ko `xfail` marker
  se document kiya, speculative fix nahi kiya. Yeh senior behaviour hai.
- **Hash-chained audit log** with an integrity endpoint.
- **Write-only credential storage** (Fernet, masked suffix only in responses).
- **Uniform 403** on flags/children — missing aur foreign mein farq nahi (IDOR T2).
- **De-identified LLM prompts** + prompt-injection fencing.
- **366 backend tests**, 26 auth/authz ko chhoote hain.

---

## 6. Coverage — what I did and did not read

**Read completely (Tier 1):** `api/deps.py`, sab endpoint modules, `core/rate_limit.py`,
`core/config.py`, `services/provider_checks.py`, `services/stt.py`, `services/llm.py`,
`services/pipeline_agents.py` (prompt paths), `alembic/versions/0001`, frontend auth +
CSRF + session + admin proxies.

**Read core paths (Tier 2):** `risk_pipeline.py`, `knowledge.py`, frontend dashboard,
session and admin surfaces.

**Sampled only (Tier 3):** test suite (structure and targets, not every assertion),
migrations 0002–0005.

**Did not read (Tier 4):** `node_modules`, `.venv`, `.next` build output, lockfiles.

**Live probing:** running dev stack par headers, auth, DB roles, RLS status aur
connection timing verify ki.

**Not verified:** actual runtime tenant leakage (dev DB mein sirf ek institution ke
children hain, isliye leak demonstrate nahi kiya ja sakta — mechanism sabit hai, exploit
nahi). Frontend ka koi automated test maujood hi nahi, to UI regressions ke liye koi
safety net nahi hai.
