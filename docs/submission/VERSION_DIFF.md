# SIGNAL: purana (submit kiya hua) vs naya version

Comparison of two folders:

- **Purana:** `S:\Projects\Hackthon Project\SIGNAL_dot_agent` (git HEAD `020e925`, plus two untracked files)
- **Naya:** `S:\Projects\Hackthon Project\code\SIGNAL_dot_agent` (current working tree)

`020e925` is an ancestor of the new project's history, so the old folder is an earlier snapshot of the same project. The comparison ignores line-ending differences.

---

## Summary table

| # | Cheez | Purana | Naya | GitHub par hai? |
|---|---|---|---|---|
| 1 | Admin ka kaam | Basic panel | Institution, staff aur bachche khud bana sakta hai | Haan |
| 2 | Bachche ki zimmedari | Nahi thi | Bachche ko kisi caretaker ke zimme laga sakte hain | Haan |
| 3 | AI service atak jaye | Seedha fail | Khud dobara koshish karta hai (retry) | Haan |
| 4 | Fake concern ka bug | Maujood tha | Theek ho gaya | Haan |
| 5 | Doctor ka jawab | Sirf referral banta tha | Outcome likha jata hai: confirm, ruled out, follow-up chhoota, abhi dekha nahi. Saath doctor ka note | Nahi |
| 6 | Bachche ki umar | Simple estimate | Range (jaise 2 se 3 saal), reference date, samay se pehle paida hone ki info | Nahi |
| 7 | Knowledge base | 94 entries, ek version | Review system: versions, compare, rollback. 88 nayi entries taiyar (live nahi) | Nahi |
| 8 | Flag ka version | Pata nahi chalta tha | Flag batata hai ke kis knowledge version par bana | Nahi |
| 9 | Urgent routing | Nahi thi | Pehla hissa bana hai (live se jura nahi) | Nahi |
| 10 | Naye pages | 12 | 18 (error, loading, help, referrals, knowledge review) | Aadhe |
| 11 | Browser tests | Nahi | Playwright e2e tests | Nahi |
| 12 | Migrations | 6 | 15 | 7 mein se 1 (sirf 0007) |
| 13 | API endpoints | 35 | 54 | Aadhe |
| 14 | Backend services | 15 | 22 | Aadhe |
| 15 | Backend tests | 356 | 459 | Aadhe |
| 16 | Presentation | Sirf `PRESENTATION_BRIEF.md` | 12-slide deck (`.pptx`, `.pdf`), `SUBMISSION.md`, guides | Haan |
| 17 | pgvector | Nahi | Optional, default band | Nahi (alag branch) |
| 18 | Team ke naam | NextaSol, Akasha Azhar, Amaan, Ayesha, Sami | Sirf Sami, Ayesha, Amaan | Haan |

"GitHub par hai?" ka matlab: wo kaam `main` ya PR #2 mein aa chuka hai ya nahi. "Aadhe" ka matlab hai ke kuch hissa pahunch chuka hai, baaki nahi.

---

## Numbers (measured)

| Metric | Purana | Naya |
|---|---|---|
| Migrations | 6 | 15 |
| Backend test files | 43 | 58 |
| Backend `def test_` | 356 | 459 |
| API route decorators | 35 | 54 |
| Backend services | 15 | 22 |
| Frontend pages | 12 | 18 |
| Frontend API proxy routes | 24 | 33 |

Files: 83 badli hain, 87 nayi hain, aur sirf 1 purani file naye mein nahi (`PRESENTATION_BRIEF.md`).

---

## Naya kaam, do hisson mein

### A. GitHub par hai (commits `2e0026c`, `16aa9b2`, `ba9b414`)

- Admin onboarding: institution, staff, child. Child ko caretaker assign karna (migration 0007).
- LLM ke temporary failure par retry; synthetic reasoner ka bug fix.
- CSP ka logic alag module (`csp.ts`) mein, tests ke saath.
- Docs: `PRESENTATION.md`, `PROJECT_OVERVIEW.md`, `SUBMISSION.md`, deck.

### B. Sirf local machine par (uncommitted)

- **Knowledge v3 review system:** migrations 0008, 0009, 0013, 0014; services `knowledge_v3`, `knowledge_release`, `knowledge_preview`, `knowledge_approval`, `knowledge_storage`; admin knowledge-review page; `knowledge_base/v3/` (88 entries, 41 references). Live scoring mein use nahi hota.
- **Referral outcomes** (migration 0010) aur referrals ke frontend pages.
- **Flag par knowledge-base revision** (migration 0011).
- **Structured age** (migration 0012).
- **`urgent_route.py`**: confirmed urgent matches ka routing primitive, live screening se connected nahi.
- **Frontend:** Playwright e2e tests, error/loading/not-found pages, "Workspace guide" page, UI components ka naya look.
- **CI:** `quality.yml`.
- **pgvector (ADR-11):** branch `feat/pgvector-semantic-retrieval`.

---

## Zaroori nateeja

Section B ka kaam GitHub par nahi hai, isliye judges GitHub dekhein to unhein naya sara kaam nahi dikhega. Migrations 0008 se 0014 commit nahi hain, aur migration 0015 (pgvector) 0014 par depend karti hai, to inko ek saath commit karna hoga. Mera mashwara hai ke section B ko saaf commits mein bantkar PR bana diya jaye.
