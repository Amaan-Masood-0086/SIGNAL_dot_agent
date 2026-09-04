# SIGNAL — Remediation Backlog

## Status after the 2026-09-02 remediation pass

| # | Item | Status |
|---|---|---|
| R1 | Activate RLS at runtime | ✅ done — tenant path on `signal_app`, `set_config` per transaction, 5 proof tests |
| R2 | Login throttle | ✅ partial — 5/5min per account. Password verification still FEAT-12 |
| R3 | Pin deps + CI gate | ✅ done — pinned + `requirements.lock.txt` + `.github/workflows/ci.yml` |
| R4 | Header hygiene | ✅ done — nonce CSP, no `X-Powered-By`, backend headers + `no-store` |
| R5 | Audit reads | ✅ done — `child.read`, `flag.read`, `flag.list`, `admin.children_list` |
| R9 | Connection pooling | ✅ done — engines cached per URL, per-request dispose removed |
| R11 | `.env.example` trackable | ✅ done |
| F11 | Trail reproducibility | ✅ done — snapshot authoritative, drift surfaced in API + UI |
| R6 | Consent model | ⛔ open — needs a legal/clinical decision first |
| R7 | Retention + erasure | ⛔ open — needs a policy decision first |
| R8 | Relationship-based access | ⛔ open — schema + product decision |
| R2b | Password hashing (FEAT-12) | ⛔ open — deliberately phase-gated; would break the seeded demo accounts |
| R12 | App Dockerfile | ⛔ open |
| R13 | Frontend tests | ⛔ open — still zero |


Ranked. Har item ticket-ready hai: kya, kahan, kyun, kitna.
Sequence deliberately chosen — R1 pehle isliye ke wo baqi sab ka blast radius kam karta hai.

---

## Sprint 1 — "Stop the bleeding" (≈ 3–5 din)

### R1 · Activate row-level security at runtime — P1
**Files:** `backend/.env`, `backend/app/api/deps.py:92`
**Why:** DB-level tenant isolation bana hua aur tested hai lekin app superuser se connect
karke usay bypass karti hai. Aaj isolation sirf application `WHERE` clauses par hai.

**Steps**
1. `DATABASE_URL` → `postgresql+psycopg://signal_app:...@localhost:5432/signal_dev`
   (`config.py:31` ka default pehle se yahi hai; sirf `.env` override hata do)
2. `get_db` ko per-request `SET LOCAL app.institution_id` chahiye. Rukawat: `get_db`
   ke paas staff context nahi hai — JWT decode `get_current_verified_staff` mein hota hai
   jo khud `get_db` par depend karta hai. **Circular dependency todni padegi**: JWT claims
   ko ek chhote `get_token_claims` dependency mein alag karo (DB-free), phir `get_db` usay
   consume kare.
3. Migrations ab bhi `signal` (owner) se chalein — sirf app runtime badle.
4. **Regression test:** ek test jo do institutions banaye aur sabit kare ke institution A
   ka token B ke rows nahi dekh sakta **jab application filter jaanbujh kar hata diya jaye**.
   Yeh wo test hai jo aaj mojood nahi.

**Effort:** 1–2 din · **Risk:** medium (dependency graph badal raha hai; poori suite chalao)
**Migration required:** nahi — `signal_app` role aur grants pehle se maujood hain.

### R2 · Close the auth gap for anything reachable from outside — P1
**Files:** `backend/app/api/v1/endpoints/auth.py`
**Immediate (aaj, 2 min):** VS Code Ports panel → port 3000 → visibility **Private**.
Password verify hota hi nahi, aur wo tunnel abhi Public hai.

**Proper (FEAT-12):**
- argon2id ya bcrypt(cost≥12) password verification
- `/auth/token` par rate limit (5 req / 5 min / IP) — `FixedWindowRateLimiter` pehle se hai
- account lockout: 5 nakaam koshishon par 30 min
- username enumeration na ho — ghalat email aur ghalat password par ek jaisa error

**Effort:** 2–3 din

### R3 · Pin dependencies and add a CI gate — P1
**Files:** `backend/requirements.txt`, naya `.github/workflows/ci.yml`
**Why:** `CLAUDE.md` yeh sab maangta hai; repo mein kuch bhi enforce nahi karta.

- `requirements.txt` → pinned (`uv pip compile` ya `pip-compile`), hashes ke saath
- CI: `pytest` + `pip-audit` + `bandit -r app/ -ll` + `npm audit --audit-level=high`
  + `gitleaks detect` + `tsc --noEmit` + `eslint` + `next build`
- PR par lazmi, main par blocking

**Effort:** 1 din · **Payoff:** har agla finding yahan pakda jayega, audit mein nahi

### R4 · Header hygiene — P1 (cheap)
**Files:** `frontend/next.config.ts`, `backend/app/main.py`
- CSP add karo: `default-src 'self'; frame-ancestors 'none'` (Next inline styles ke liye
  nonce/hash chahiye — pehle Report-Only mein chalao)
- `poweredByHeader: false`
- Backend par security headers + `Cache-Control: private, no-store` on PHI JSON
- `server: uvicorn` banner hatao

**Effort:** 2 ghante

---

## Sprint 2 — "Make it a clinical product" (≈ 2 hafte)

### R5 · Audit reads, not just writes — P1
**Files:** sab `@router.get` handlers jo child/flag/session data dete hain
Per-record read logging list endpoints par mehenga hai — faisla karo: per-query
(`child.list`, filter + count ke saath) vs per-record (`child.read`). Clinical standard
per-record hai un records ke liye jo actually kholay gaye.
**Effort:** 1 din + retention faisla

### R6 · Consent model — P2
Captured, versioned, timestamped. Guardian/institution consent for processing, aur
alag se voice-recording consent (abhi sirf UI checkbox hai, persist nahi hota).
Consent **query path mein enforce ho**, sirf record na ho.
**Effort:** 3–5 din · **Blocker:** legal/clinical faisla pehle chahiye

### R7 · Retention + defensible deletion — P2
Clinical retention period vs erasure rights ka explicit resolution. Abhi koi deletion
path nahi hai — jo apne aap mein ek faisla hai, bas likha hua nahi.
**Effort:** design 1 din, implementation 2–3 din

### R8 · Relationship-based access — P2
"Assigned caretaker" concept. Aaj institution ka har staff har bachcha dekhta hai.
**Effort:** 3 din (schema + enforcement + UI)

### R9 · Connection pooling — P2
`deps.py:102` ka per-request engine hatao — module-level pooled engine, per-request
session. R1 ke saath karo (dono `get_db` ko chhoote hain).
**Effort:** R1 ke andar hi

### R10 · PHI redaction before the LLM — P2
Observation text par ek light NER/redaction pass, ya UI mein caretaker ko batao ke naam
na likhein. Plus DeepSeek ke liye data-processing position document karo.
**Effort:** 2 din

---

## Sprint 3 — Hygiene

| # | Item | Effort |
|---|---|---|
| R11 | `frontend/.gitignore` mein `!.env.example` | 2 min |
| R12 | App ka Dockerfile + deployable artifact (abhi sirf DB ka compose hai) | 1 din |
| R13 | Frontend tests — abhi ek bhi nahi. Pehle `navGroupsFor()`/`isAdmin` (security-adjacent) | 2 din |
| R14 | Redis-backed rate limiter (multi-instance) | 1 din |
| R15 | Backup + tested restore | 1 din |

---

## Explicitly NOT recommended

- **Rewrite kuch bhi nahi.** Architecture theek hai; masla wiring ka hai, design ka nahi.
- **RLS ko chhodna aur sirf app filters par bharosa karna** — role aur policies pehle se
  bani hui hain, unhe on karna sasta hai.
- **R14 (clinical divergence) ka speculative fix** — wo sahi tarah blocked hai, clinical
  sign-off ka intezar kare.
