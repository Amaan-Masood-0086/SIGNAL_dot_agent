"""Deterministic synthetic LLM provider (synthetic_only fallback).

Phase 1 runs with `LLM_PROVIDER=none` in the demo environment — the
pipeline still has to work keylessly, so this module provides a
deterministic rule-based stand-in for the three agents: keyword concept
detection for observation, age-banded concept→citation mapping for
reasoning, and template prose for explanation.

HONEST SCOPE (documented per ai-agent-development.md — known limitation,
not a silent gap): this is NOT general language understanding. It resolves
the curated demo scenarios (signal_test_conversations_v2.csv) and obvious
variants; anything unrecognized concludes with empty evidence, which the
pipeline routes to INSUFFICIENT_INFORMATION — the correct safe failure
mode. With a real `LLM_PROVIDER` configured, this module is never used.

Safety properties it shares with the real path: it only ever cites refs
whose age band contains the evaluation age (so the pipeline's grounding
check can never fail), and it never emits diagnostic labels.
"""

from __future__ import annotations

import json
import re

from app.services.llm import AGENT_EXPLANATION, AGENT_OBSERVATION, AGENT_RISK_REASONING

_SAFEGUARDING_PHRASES = (
    "flinch", "flinches", "withdrawn", "bruise", "bruises", "afraid of",
    "scares", "scared of", "hurts him", "hurts her", "neglect",
)
_INSUFFICIENT_PHRASES = (
    "only met", "met him this week", "met her this week", "haven't seen enough",
    "not sure", "just started", "barely know",
)

# concept -> (trigger phrases, follow-up question, confirmed refs with bands,
# refs cited when the follow-up answer is protective, refs cited as missed
# borderline anchors). Bands keep every synthetic citation inside the
# pipeline's grounding universe.
_CONCEPTS = (
    {
        "name": "regression",
        "phrases": ("used to say", "stopped saying", "used to wave", "lost any", "not anymore"),
        "follow_up": "Has he lost any words or skills he used to have?",
        "confirmed": (("SL-RF-008", 12, 18),),
        "definitive": True,
    },
    {
        "name": "caretaker_hearing_concern",
        "phrases": ("worried about her hearing", "worried about his hearing", "worry about hearing"),
        "follow_up": "What makes you feel that way — is there something specific?",
        "confirmed": (("HEAR-RF-014", 0, 72),),
        "definitive": True,
    },
    {
        "name": "no_response_to_sound_infant",
        "phrases": ("doesn't turn around", "clap loudly", "no response to sound", "doesn't react to loud"),
        "follow_up": "Does he react at all to loud sounds, like a door slamming?",
        "confirmed": (("HEAR-RF-003", 6, 9), ("HEAR-RF-013", 36, 72)),
    },
    {
        "name": "limited_speech_not_listening",
        "phrases": ("doesn't talk much", "doesn't seem to listen", "not listening"),
        "follow_up": "Does he respond when you call him from behind, where he can't see you?",
        "confirmed": (("HEAR-RF-008", 12, 36), ("HEAR-RF-013", 36, 72), ("HEAR-RF-011", 36, 72)),
    },
    {
        "name": "ear_pattern",
        "phrases": ("pulling at her ear", "pulling at his ear", "ear infection", "says 'what?'", 'says "what?"', "what? a lot"),
        "follow_up": "Has she had ear infections before? Does she sit very close to the TV?",
        "confirmed": (("HEAR-RF-009", 36, 72), ("HEAR-RF-010", 36, 72), ("HEAR-RF-016", 0, 72)),
    },
    {
        "name": "unintelligible_at_five",
        "phrases": ("struggle to understand", "hard to understand her", "hard to understand him"),
        "follow_up": "Does she use full sentences? Does she ask questions like 'why'?",
        "confirmed": (("SL-RF-018", 60, 72), ("SL-RF-019", 60, 72)),
    },
    {
        "name": "vague_five_year_old",
        # The trailing comma is load-bearing. Without it this is a plain
        # string, `for phrase in phrases` walks its CHARACTERS, and the
        # concept matches any input containing "s" or a space — which meant
        # a five-year-old whose caretaker reported nothing developmental was
        # graded MODERATE on invented evidence. Pinned by
        # tests/test_synthetic_reasoner_matching.py.
        "phrases": ("something feels off",),
        "follow_up": "Does she talk as much as other children her age? Does she hear and understand you?",
        "confirmed": (("SL-RF-020", 60, 72),),
        "missed": (("SL-M-031", 60, 72),),
    },
    {
        "name": "few_words_18mo",
        "phrases": ("only says about", "only a few words", "only says a couple"),
        "follow_up": "Does he point or gesture to ask for things?",
        "missed": (("SL-M-015", 18, 18),),
        "protective": (("SL-M-012", 18, 18), ("SL-M-014", 12, 18)),
        "protective_phrases": ("points", "point", "gesture", "responds right away"),
    },
    {
        "name": "intelligibility_borderline",
        "phrases": ("only i can really understand", "only i can understand"),
        "follow_up": "Does she put two words together? Does she understand instructions?",
        "missed": (("SL-M-017", 18, 24),),
        "protective": (("SL-M-019", 24, 36),),
        "protective_phrases": ("understands everything", "understands"),
    },
    {
        "name": "talking_behind_borderline",
        "phrases": ("behind the other kids", "behind other kids"),
        "follow_up": "Roughly how many words does she use? Does she understand without gestures?",
        "missed": (("SL-M-017", 18, 24),),
        "protective": (("SL-M-018", 18, 24),),
        "protective_phrases": ("understands fine", "understands"),
    },
)


class SyntheticRuleLLM:
    """Drop-in LLMProvider: deterministic, keyless, demo-grade."""

    def complete(self, *, agent: str, tier: str, system: str, user: str) -> str:
        if agent == AGENT_OBSERVATION:
            return self._observation(user)
        if agent == AGENT_RISK_REASONING:
            return self._reasoning(user)
        if agent == AGENT_EXPLANATION:
            return self._explanation(user)
        raise ValueError(f"unknown agent {agent!r}")

    # ── observation ────────────────────────────────────────────────────────

    def _observation(self, user: str) -> str:
        text = self._fenced_text(user)
        lowered = text.lower()
        if any(phrase in lowered for phrase in _SAFEGUARDING_PHRASES):
            return json.dumps({
                "signals": [text.strip()],
                "safeguarding_pattern": True,
                "key_items_missing": False,
            })
        key_missing = any(phrase in lowered for phrase in _INSUFFICIENT_PHRASES)
        signals = [
            concept["name"].replace("_", " ")
            for concept in _CONCEPTS
            if any(phrase in lowered for phrase in concept["phrases"])
        ] or ([text.strip()] if text.strip() else [])
        return json.dumps({
            "signals": signals,
            "safeguarding_pattern": False,
            "key_items_missing": key_missing,
        })

    # ── risk reasoning ─────────────────────────────────────────────────────

    def _reasoning(self, user: str) -> str:
        turns = re.findall(r"<caretaker_input>(.*?)</caretaker_input>", user, re.S)
        lowered_turns = [turn.lower() for turn in turns]
        joined = " ".join(lowered_turns)
        latest = lowered_turns[-1] if lowered_turns else ""
        age = self._evaluation_age(user)

        if any(phrase in joined for phrase in _INSUFFICIENT_PHRASES):
            return self._reason_payload(key_items_missing=True)

        if age > 72:
            # Out of Phase-1 knowledge scope: no in-scope row is citable, so
            # the only honest conclusion is empty evidence.
            return self._reason_payload()

        matched = [
            concept for concept in _CONCEPTS
            if any(phrase in joined for phrase in concept["phrases"])
        ]
        if not matched:
            return self._reason_payload()

        first = matched[0]
        if len(turns) < 2 and not first.get("definitive"):
            # Ask the discriminating follow-up before concluding.
            return self._reason_payload(
                concluded=False, follow_up_question=first["follow_up"]
            )

        confirmed: list[str] = []
        missed: list[str] = []
        met: list[str] = []
        for concept in matched:
            for ref, low, high in concept.get("confirmed", ()):
                if low <= age <= high and ref not in confirmed:
                    confirmed.append(ref)
            for ref, low, high in concept.get("missed", ()):
                if low <= age <= high and ref not in missed:
                    missed.append(ref)
            protective_phrases = concept.get("protective_phrases", ())
            if any(phrase in latest for phrase in protective_phrases):
                for ref, low, high in concept.get("protective", ()):
                    if low <= age <= high and ref not in met:
                        met.append(ref)

        return self._reason_payload(
            confirmed_red_flags=confirmed,
            missed_milestones=missed,
            met_milestones=met,
        )

    @staticmethod
    def _reason_payload(
        *,
        concluded: bool = True,
        follow_up_question: str | None = None,
        key_items_missing: bool = False,
        confirmed_red_flags: list[str] | None = None,
        missed_milestones: list[str] | None = None,
        met_milestones: list[str] | None = None,
    ) -> str:
        return json.dumps({
            "concluded": concluded,
            "follow_up_question": follow_up_question,
            "key_items_missing": key_items_missing,
            "confirmed_red_flags": confirmed_red_flags or [],
            "missed_milestones": missed_milestones or [],
            "met_milestones": met_milestones or [],
            "risk_modifiers": [],
        })

    # ── explanation ────────────────────────────────────────────────────────

    def _explanation(self, user: str) -> str:
        refs = re.findall(r"- ((?:SL|HEAR)-(?:M|RF|RISK)-\d+):", user)
        grade = re.search(r"grade: (\w+)", user)
        grade_name = grade.group(1) if grade else "UNKNOWN"
        lines = {
            "HIGH": "What you described should be checked by a clinician soon.",
            "MODERATE": "What you described is worth having a clinician look at.",
            "LOW_MONITOR": "What you described is near the expected range; recheck in about three months.",
            "INSUFFICIENT_INFORMATION": "There is not enough information yet to grade this.",
        }.get(grade_name, "A clinician can review what you described.")
        basis = f" Basis: {', '.join(refs)}." if refs else ""
        return f"{lines}{basis} This is a screening result, not a diagnosis."

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _fenced_text(user: str) -> str:
        match = re.search(r"<caretaker_input>\n?(.*?)\n?</caretaker_input>", user, re.S)
        return match.group(1) if match else ""

    @staticmethod
    def _evaluation_age(user: str) -> int:
        match = re.search(r"(?:EVALUATION AGE: |age: )(\d+) months", user)
        return int(match.group(1)) if match else 0
