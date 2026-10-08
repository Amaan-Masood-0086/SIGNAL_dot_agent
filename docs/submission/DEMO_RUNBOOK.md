# Live demo runbook

Everything here was run against the real app on 2026-10-08 (cold start, browser walk-through, API checks).

## 1. Start it (about 3 minutes, do this 10 minutes before)

1. Open **Docker Desktop** and wait until it says running.
2. In PowerShell, from the repo root:

```bash
.\scripts\run_demo.ps1 -Reset
```

`-Reset` wipes the dev database and rebuilds clean synthetic data (94 knowledge rows, a demo institution, three demo children). Leave it off to keep existing data. Add `-Rebuild` after changing frontend code.

The script prints the URLs and accounts when it is ready. It picks database port 5432, or 5433 if another project already holds 5432.

| Account | Role | Password |
|---|---|---|
| `synthetic-staff@signal.example` | Caretaker | any (synthetic mode) |
| `root@signal.example` | Administrator | any (synthetic mode) |

App: http://localhost:3000

## 2. The demo path (all verified)

**Act 1: register a child.** Dashboard, **Register a child**, name `Ayan`, **Estimated age**, range `8-10 months`, note `intake worker estimate`. Point at the amber estimate banner.

**Act 2: screening with a follow-up.** Open Ayan, **Start a text observation session**, type:

> He doesn't turn around even when I clap loudly behind him

SIGNAL asks a follow-up ("Does he react at all to loud sounds, like a door slamming?"). Answer:

> No, he doesn't seem to notice

Result: **HIGH, Hearing**, citation `HEAR-RF-003`, the "why" panel with the knowledge-base row, and no diagnosis named.

**Second example (older child).** Open the seeded child **Zara (30 months)**, type `He doesn't talk much and doesn't seem to listen.`, answer `No, not really.` Result: **HIGH, Hearing**, `HEAR-RF-008`. Grades depend on age, so this phrase gives no HIGH for an 8-month-old.

**Act 3: close the loop.** On the result card choose **Referral & follow-up**, enter a responsible person and a review date, tick the confirmation and **Confirm referral**. A referral cannot be created without the confirmation.

**Act 4: admin tour.** Sign out, sign in as `root@signal.example`: overview, staff and roles, children, audit log (hash-chain integrity), usage, providers, knowledge review.

## 3. Know these before you present

| Topic | What is true |
|---|---|
| AI mode | No LLM key is configured, so the app uses its **built-in deterministic reasoner**. It is fast (under 1 second) and gives the results above, but it is a rule matcher: free text outside its phrasing patterns returns **"Not enough information"**, which is the designed safe outcome, not a crash. Say this plainly if asked. |
| Real LLM | Add a key in Admin, Providers (stored encrypted, write-only). It was **not tested here** because no key was available. Provider latency has been measured at about 45 seconds per call on DeepSeek, which is long for a live demo. |
| Knowledge base | The live app uses the **v2 knowledge base (94 rows)**. v3 (88 entries) is a review release and is **not live**. Do not describe it as active. |
| pgvector | Installed and optional, **off by default**. It does not make responses faster; it is for scaling the knowledge base later. |
| Sign-in | Limited to **5 attempts per 5 minutes per account**. Do not sign in and out repeatedly. |
| Session | A login lasts **15 minutes**. Sign in shortly before you present. |
| Voice | Needs a speech-to-text key. Without one, use typing; do not demo the microphone. |
| Passwords | Not verified (synthetic mode). Never expose this build publicly. |

## 4. If something breaks

| Symptom | Fix |
|---|---|
| Login fails or the page will not load | Run `.\scripts\run_demo.ps1` again (it restarts both servers) |
| "Docker is not running" | Start Docker Desktop, wait, rerun |
| Port 8002 or 3000 held by another program | The script refuses to kill non-Python/Node processes; close that program |
| Roster is messy from rehearsing | `.\scripts\run_demo.ps1 -Reset` |
| "Too many sign-in attempts" | Wait 5 minutes |
