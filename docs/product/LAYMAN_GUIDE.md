# SIGNAL explained in plain words

*No technical knowledge needed. If you can read this page, you can explain SIGNAL to someone else.*

---

## 1. The one-minute version

In orphanages and welfare homes, one caretaker looks after many children. Some children
have a small problem with **speaking or hearing**. These are usually the quiet children
who never make trouble, so nobody notices. If the problem is found early, it can be
treated well. If it is found late, the child loses years.

**SIGNAL is a helper that sits with the caretaker.**

1. The caretaker says (or types) what they noticed, for example *"he doesn't turn around
   when I clap behind him"*.
2. SIGNAL asks a few simple questions.
3. SIGNAL says how worried we should be, why, and what to do next.
4. Everything is written down safely, so a doctor can read it later and the institution
   can prove it noticed and acted.

> **SIGNAL is not a doctor and never gives a diagnosis.** It works like a smoke alarm. It
> tells you "something may be wrong, please get it checked". It does not tell you what the
> illness is.

---

## 2. The problem it solves

**Problem 1: nobody keeps a record.** A caretaker notices something and tells a colleague.
Later it is forgotten. Nothing happens, and nobody can prove anything was ever noticed.

**Problem 2: most children have no birth certificate.** Every "what a child should do at
this age" chart needs the child's age. In an orphanage the exact age is often unknown. A
tool that insists on a birth date cannot be used here.

SIGNAL is built for both. Every concern becomes a **record**, and the child's age may
simply be an **estimate**.

---

## 3. Who uses it

| Person | What they do |
|---|---|
| **Caretaker** | The only one who talks to SIGNAL. Adds a child, describes what they noticed, answers questions, reads the result. They need no medical training. |
| **Doctor / clinician** | Does not use the app. Receives the concern with its evidence and can see exactly why it was raised. |
| **Institution** | Keeps the record: who noticed, what was found, who is responsible, and when it will be reviewed. |
| **Administrator** | Manages staff, children and settings. Looks after the system but does not do screenings. |

---

## 4. A real example, step by step

> **Caretaker:** "He doesn't talk much and doesn't seem to listen."
> **SIGNAL:** "When you call him from behind, where he can't see you, does he respond?"
> **Caretaker:** "No, not really."
> **SIGNAL:** **HIGH concern (hearing).** "A doctor should check this soon. This is a
> screening result, not a diagnosis."

Why did SIGNAL ask that question? A child who talks late may have a *speech* problem or a
*hearing* problem. They look almost the same from outside. Asking whether the child reacts
to sounds from behind tells the two apart. Mixing them up means the child gets the wrong
help for years. That is why SIGNAL always checks **speech and hearing together**.

SIGNAL asks at most 4 or 5 questions. It stops early if it already has enough.

---

## 5. The four possible answers

| Answer | In plain words |
|---|---|
| **HIGH** | See a doctor soon. |
| **MODERATE** | Get it checked. |
| **LOW (monitor)** | Close to normal. Watch and check again in about 3 months. |
| **NOT ENOUGH INFORMATION** | We cannot tell. Ask someone who knows the child well and try again. |

There is **no "all clear" answer**, on purpose. "Not enough information" is never
treated as good news. A caretaker who joined last week and barely knows the child gets
exactly that answer, and is told what to do next.

---

## 6. What data does SIGNAL keep?

Everything shown in the demo is **made-up (synthetic) data**. No real child's information
is in this version.

| Data | What it is |
|---|---|
| **The child** | Name, date the child arrived, and age. Age is stored as either a **confirmed birth date** or an **estimated range** (for example "about 2 to 3 years"). Also notes on whether the child was born early. |
| **The staff** | Email, role (caretaker or admin) and which institution they belong to. Passwords are stored scrambled, never as plain text. |
| **A session** | One sitting where a caretaker describes concerns about one child: who, when, and the status. |
| **Observations** | What the caretaker said or typed, turn by turn, plus the facts SIGNAL pulled out of it (for example "does not respond to loud sounds"). |
| **A flag** | The result: the area (speech or hearing), the grade, a plain explanation, and **the exact evidence it was based on**. |
| **A referral** | The follow-up: who is responsible, the review date, whether it was escalated, and the doctor's note. |
| **Audit log** | A diary of who did what and when. It can only be added to, never edited or erased. |
| **Knowledge base** | The reference library of about 94 checked milestones and warning signs (see section 7). |

**What SIGNAL does not keep:** voice recordings. When someone speaks, the audio is turned
into text and **thrown away immediately**. Only the text is kept.

**Privacy of each institution:** every institution's data is walled off. The database
itself blocks one institution from seeing another's children, even if the software had a
mistake.

---

## 7. Where does the medical knowledge come from?

Not from the AI's memory. SIGNAL has a **reference library**: a spreadsheet of about 94
entries such as *"most babies coo by 6 months"* or *"a child who loses words they used to
say needs urgent attention"*. Each entry gives an age range and the source (ASHA, CDC,
NIDCD, JCIH and other recognised health bodies).

Every result points back to the exact entries that produced it. When a doctor asks "why
did it say this?", the answer is: *because of entries X and Y, which say exactly this.*

---

## 8. How the data moves

```
Caretaker speaks or types
        |
        v
Voice becomes text (audio is deleted)
        |
        v
AI helper 1 - "Listener": picks out the facts, nothing more
        |
        v
Looks up the reference library (speech AND hearing together)
        |
        v
AI helper 2 - "Thinker": matches the facts to library entries.
        May ask ONE follow-up question. Maximum 5 turns.
        |
        v
The GRADE is decided by fixed rules (ordinary code, not AI)
        |
        v
AI helper 3 - "Explainer": writes the result in simple, kind words,
        in the caretaker's own language (Urdu, Roman Urdu or English)
        |
        v
Saved as a record: grade + explanation + evidence
        |
        v
Doctor referral + a line in the tamper-proof diary
```

---

## 9. What is the AI's role, and what is it not allowed to do?

SIGNAL uses an AI language model (the same kind of technology as a chatbot) for three
small jobs.

| AI job | What it does |
|---|---|
| **Listener** | Turns messy human speech into a short list of facts ("does not respond to clapping"). It records what was seen, never a guess about the cause. |
| **Thinker** | Compares those facts with the reference library and decides whether one more question would help. |
| **Explainer** | Rewrites the result in warm, simple language, in Urdu or English. |

**The AI is NOT allowed to:**

- **Decide the grade.** A fixed set of written rules does. The same facts always give the
  same grade, so nobody has to trust a chatbot's mood.
- **Use its own medical knowledge.** It may only refer to library entries it was given.
  If it names something outside the library, the system rejects the answer.
- **Diagnose.** It never names a disease.
- **See who the child is.** The AI receives the child's age and what the caretaker said.
  It never receives the child's name, ID or institution.
- **Obey the caretaker's text as instructions.** What the caretaker types is treated as
  information only, so nobody can trick the AI by typing commands into it.

**Why this design?** An AI alone can be confident and wrong. So we use it only for what it
is good at (understanding language and writing clearly) and keep the serious decision in
simple rules a person can read and check.

**If voice is unavailable,** the caretaker can still type, and the record is saved the same way.

---

## 10. Why people can trust the record

- **Tamper-proof diary.** Every action (even *viewing* a child's file) is logged. Each
  line is mathematically linked to the one before it. Changing an old line breaks the
  chain, and the system shows exactly where.
- **The reasoning is frozen.** A flag stores the exact wording of the library entries as
  they were that day. If the library is edited later, the old flag is not silently
  rewritten, and a doctor is told that the reference has changed.
- **Honest about uncertainty.** If the age is only an estimate, borderline cases are
  graded *lower* to avoid false alarms. Serious signs, such as a child losing words they
  used to know, are **never** lowered.

---

## 11. What SIGNAL cannot do yet (honest list)

- It is **not approved for clinical use** and only runs on synthetic data.
- **Passwords are not checked yet.** This is why this version must not be put on the
  public internet.
- There is no consent form or data-retention policy yet. These need legal decisions first.
- One test case is deliberately marked as unresolved. Our rules and the clinical dataset
  disagree, and **a clinician must decide**, not the programmers.
- The AI can take about 45 seconds per answer. We have measured it and are looking into
  the cause.

---

## 12. Quick glossary

| Word | Meaning |
|---|---|
| **Screening** | A quick check that says "look closer". It is not a diagnosis. |
| **Milestone** | Something a child normally does by a certain age, such as cooing or first words. |
| **Red flag** | A warning sign that needs attention whatever the age. |
| **Flag** | SIGNAL's result for one child: the area, the grade and the evidence. |
| **Referral** | Handing the concern to a doctor, with a named person responsible. |
| **Synthetic data** | Made-up data that looks real, used so nobody's real information is at risk. |
| **AI / LLM** | The language technology behind chatbots. Here it only listens, thinks and explains. |
| **Audit log** | The permanent diary of who did what. |

---

**Team:** Sami (lead) · Ayesha · Amaan
**Code:** https://github.com/Amaan-Masood-0086/SIGNAL_dot_agent
