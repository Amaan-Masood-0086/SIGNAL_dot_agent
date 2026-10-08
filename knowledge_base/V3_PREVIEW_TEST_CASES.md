# V3 knowledge preview — synthetic test cases

Open **Administration → KB preview sandbox**. For each case, paste the observation, set the age and domain, then select **Run preview**.

These are synthetic test inputs, not clinical assessments. The preview uses keyword-based retrieval. A matching entry does not confirm a concern, and these examples are not an expert-labelled evaluation dataset.

## 1. Speech and language

- Age from: `30`
- Age to: `30`
- Domain: `Speech_Language`

```text
The child uses a few single words but rarely combines two words. He points when he wants something.
```

Inspect whether word-use and word-combination candidates are relevant and whether the follow-up questions are understandable.

## 2. Hearing

- Age from: `48`
- Age to: `48`
- Domain: `Hearing`

```text
The child sometimes does not respond when called by name and has difficulty hearing speech in a noisy room.
```

Inspect hearing-related candidates and questions about the circumstances of the observation. A match must not be interpreted as confirmed hearing loss.

## 3. Vision

- Age from: `84`
- Age to: `84`
- Domain: `Vision`

```text
The child holds books very close and struggles to see objects across the room.
```

Inspect candidate relevance and the wording of follow-up questions. Record unrelated or missing candidates as retrieval findings.

## 4. Motor

- Age from: `48`
- Age to: `48`
- Domain: `Motor`

```text
The child has difficulty running and climbing stairs and frequently falls during play.
```

Inspect movement-related candidates. Keyword overlap must not be treated as confirmation that a particular milestone is absent.

## 5. Social communication

- Age from: `24`
- Age to: `24`
- Domain: `Social_Communication`

```text
The child rarely points to show something interesting or brings toys to share with a caregiver.
```

Inspect candidates about pointing and sharing interest, and whether the questions remain neutral rather than suggesting a diagnosis.

## 6. Attention

- Age from: `96`
- Age to: `96`
- Domain: `Attention`

```text
The child finds it difficult to sustain attention during classroom activities. Similar difficulties are reported during everyday activities at home.
```

Inspect attention-related candidates and context questions. The preview must not produce an ADHD diagnosis or a clinical grade.

## 7. Unknown information

- Age from: `30`
- Age to: `30`
- Domain: `Speech_Language`

```text
I started caring for this child yesterday. I do not know which words the child usually says.
```

The current preview may retrieve word-related entries. This does not mean it has classified the answer as unknown, or that the child lacks the skill. Record any misleading interpretation in the displayed wording.

## 8. Irrelevant observation

- Age from: `48`
- Age to: `48`
- Domain: `Speech_Language`

```text
The child wore a blue shirt today.
```

Inspect whether unrelated candidates appear. Any such matches are retrieval-quality findings; do not treat them as developmental concerns.

## 9. Age interval comparison

Use the speech observation from case 1 with domain `Speech_Language`.

1. Run with age from `24` and age to `36`.
2. Record candidates labelled `age_uncertain`.
3. Run again with age from `30` and age to `30`.
4. Compare candidate age statuses.

An age interval means the child's age is uncertain within those bounds; it is not a search range for milestones. Use `30 / 30` when testing a child known to be 30 months old. An uncertain label is expected when the interval crosses an entry's age boundary.

## Checklist for every case

- The banner shows preview-only operation, runtime disabled and clinical grade none.
- Candidates belong to the selected domain.
- English and Roman-Urdu questions are understandable and preserve the same meaning.
- Evidence/source references are visible.
- No diagnosis or final clinical grade is generated.
- Preview submissions do not create caretaker sessions, flags or referrals.
- Record unrelated matches, confusing translations and unexpected age statuses.

## Record your findings

| Case | Age bounds | Candidate citation | What was unclear or incorrect? | Suggested wording / notes |
|---|---|---|---|---|
| | | | | |

V3 remains a research draft. These tests inspect the sandbox; they do not approve or activate its clinical content.
