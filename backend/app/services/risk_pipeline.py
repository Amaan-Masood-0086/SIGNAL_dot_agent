"""FEAT-05 orchestration — Observation → Risk Reasoning → Explanation.

Direct multi-call pipeline (ADR-01). Everything safety-critical is
deterministic code here, never LLM discretion:

- ONE retrieval call — `retrieve_in_scope_entries` returns BOTH domains
  jointly (ADR-05); there is no domain parameter to filter with. The citable
  universe is that set plus already-passed milestones (age_max below the
  child's age — protective "already reached" evidence, e.g. a 30-month-old
  citing the 18-24 mo band), all Phase-2 rows excluded.
- The grade comes from FEAT-04's literal `grade()` (ADR-06) — the model
  never picks a grade.
- Domain is decided ONLY after the joint check: strongest confirmed red
  flags win; a cross-domain tie resolves to Hearing — hearing-driven speech
  delay misattribution is the canonical error ADR-05 exists to prevent.
- ADR-02: estimated age evaluates at the YOUNGER bound; `age_uncertain`
  rides every result.
- Adaptive loop hard-stops at max_turns=5 with a forced conclusion; turn 6
  is refused outright.
- Safeguarding-pattern input routes OUT of developmental reasoning with zero
  flags. The escalation-table write is FEAT-11's scope — this is the stub
  handoff, deliberately a separate code path (no shared writer with flags).
"""

from __future__ import annotations

import datetime
import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.milestone import Milestone
from app.models.session import Session as ConversationSession
from app.services.flag_service import FlagService
from app.services.knowledge import (
    ENTRY_TYPE_MILESTONE,
    ENTRY_TYPE_RED_FLAG,
    GRADE_INSUFFICIENT_INFORMATION,
    KnowledgeEntry,
    grade,
    retrieve_in_scope_entries,
)
from app.services.audit import AuditService
from app.services.llm import AGENT_EXPLANATION, AGENT_OBSERVATION, AGENT_RISK_REASONING, LLMProvider
from app.services.safeguarding_service import SafeguardingService
from app.services.pipeline_agents import (
    AgeContext,
    ExplanationAgent,
    ObservationAgent,
    RiskReasoningAgent,
)
from app.services.usage import UsageService

MAX_TURNS = 5

OUTCOME_FOLLOW_UP = "follow_up"
OUTCOME_FLAGGED = "flagged"
OUTCOME_INSUFFICIENT_INFORMATION = "insufficient_information"
OUTCOME_SAFEGUARDING = "safeguarding_escalation"

SEVERITY_ORDER = {"HIGH": 0, "MODERATE": 1}


class LoopCapExceeded(RuntimeError):
    """A caretaker turn beyond max_turns — the session must conclude, not
    continue (cost + drift control)."""


class PipelineError(RuntimeError):
    """The run cannot proceed (e.g. a child with no usable age data)."""


@dataclass(frozen=True)
class PipelineResult:
    outcome: str
    turn: int
    age_uncertain: bool = False
    follow_up_question: str | None = None
    grade: str | None = None
    domain: str | None = None
    citation_refs: list[str] = field(default_factory=list)
    explanation_text: str | None = None
    loop_exhausted: bool = False
    safeguarding_signal: str | None = None
    # Structured signals the Observation Agent extracted from the latest
    # turn — stored on the observation row for auditability.
    signals: list[str] = field(default_factory=list)
    # FEAT-07 continuity: this child's flags from EARLIER sessions.
    prior_flags: list[dict] = field(default_factory=list)


def resolve_age_context(child: Child, reference_date: datetime.date) -> AgeContext:
    """ADR-02 dual-age model → the single evaluation age.

    Confirmed DOB → exact months at the reference date. Estimated → the
    YOUNGER bound of the range (conservative against over-referral).
    """
    if child.dob_confirmed:
        if child.dob is None:
            raise PipelineError("child marked dob_confirmed without a dob")
        months = (
            (reference_date.year - child.dob.year) * 12
            + (reference_date.month - child.dob.month)
            - (1 if reference_date.day < child.dob.day else 0)
        )
        return AgeContext(age_months=max(months, 0), dob_confirmed=True)

    match = re.search(r"(\d+)\s*[-\u2013]\s*(\d+)", child.estimated_age_range or "")
    if match is None:
        raise PipelineError(
            f"unparseable estimated_age_range {child.estimated_age_range!r}"
        )
    lower_bound = int(match.group(1))
    return AgeContext(
        age_months=lower_bound,
        dob_confirmed=False,
        estimated_age_range=child.estimated_age_range,
    )


def _resolve_domain(cited: list[KnowledgeEntry]) -> str | None:
    """Domain is decided AFTER the joint check (ADR-05): strongest red flags
    first; a cross-domain pool resolves to Hearing — hearing is the live
    differential on every language observation."""
    red_flags = [e for e in cited if e.entry_type == ENTRY_TYPE_RED_FLAG]
    high = [e for e in red_flags if e.severity == "HIGH"]
    moderate = [e for e in red_flags if e.severity == "MODERATE"]
    pool = high or moderate or red_flags or cited
    domains = {e.domain for e in pool}
    if not domains:
        return None
    if len(domains) > 1:
        return "Hearing" if "Hearing" in domains else pool[0].domain
    return next(iter(domains))


_INSUFFICIENT_TEXT = (
    "There is not enough information yet to say how things are going. This "
    "is not a reassuring result — it means the check should be repeated "
    "with a caretaker who knows the child day to day."
)
_SAFEGUARDING_TEXT = (
    "What you described is being passed to the safeguarding pathway, which "
    "is handled separately from developmental screening. If a child is in "
    "immediate danger, contact the relevant authorities now."
)


class RiskPipeline:
    def __init__(self, db: Session, provider: LLMProvider):
        self._db = db
        self.provider = provider
        self._observation = ObservationAgent(provider)
        self._reasoning = RiskReasoningAgent(provider)
        self._explanation = ExplanationAgent(provider)

    # ── main entrypoint ────────────────────────────────────────────────────

    def run(
        self,
        *,
        session: ConversationSession,
        child: Child,
        caretaker_turns: list[str],
        turn_number: int,
        staff_id: uuid.UUID,
        institution_id: uuid.UUID,
        reference_date: datetime.date | None = None,
    ) -> PipelineResult:
        if turn_number > MAX_TURNS:
            raise LoopCapExceeded(
                f"adaptive loop capped at {MAX_TURNS} turns — the session "
                f"must conclude, not continue"
            )
        reference_date = reference_date or datetime.date.today()
        age_context = resolve_age_context(child, reference_date)
        usage = UsageService(self._db)

        # 1) Observation — extraction only. Safeguarding patterns route OUT
        # before any developmental reasoning happens.
        observation = self._llm_call(
            usage,
            staff_id=staff_id,
            institution_id=institution_id,
            call_type=AGENT_OBSERVATION,
            fn=lambda: self._observation.extract(
                caretaker_turns[-1], age_context=age_context
            ),
        )
        if observation.safeguarding_pattern:
            # FEAT-11 (stub depth): abuse/neglect-pattern signals route to
            # the safeguarding pathway via its OWN service — no shared code
            # path with flags, and NO developmental flag is produced.
            # Downstream mandatory-reporting is out of Phase-1 scope.
            escalation = SafeguardingService(self._db).escalate(
                institution_id=session.institution_id,
                session_id=session.id,
                child_id=child.id,
                signal_description="; ".join(observation.signals)
                or "caretaker report",
            )
            self._db.flush()
            AuditService(self._db).append(
                actor_id=str(staff_id),
                action="safeguarding.escalate",
                resource_type="safeguarding_escalation",
                resource_id=str(escalation.id),
                institution_id=str(institution_id),
            )
            return PipelineResult(
                outcome=OUTCOME_SAFEGUARDING,
                turn=turn_number,
                age_uncertain=age_context.age_uncertain,
                explanation_text=_SAFEGUARDING_TEXT,
                safeguarding_signal="; ".join(observation.signals) or "caretaker report",
                signals=list(observation.signals),
            )

        # 2) Retrieval — ONE joint call, both domains (ADR-05), plus
        # already-passed milestones as protective-evidence candidates.
        retrieved = retrieve_in_scope_entries(self._db, age_context.age_months)
        universe = self._with_passed_milestones(retrieved, age_context.age_months)

        # 2b) Case memory (FEAT-07): this child's flags from earlier
        # sessions give the reasoning agent continuity. Same child only —
        # the query is scoped to child_id, so no cross-child leakage.
        prior_flags = self._prior_flags(child, session)
        case_memory = self._case_memory_block(prior_flags)

        # 3) Risk Reasoning — grounded, adaptive, capped.
        force_conclusion = turn_number >= MAX_TURNS
        reasoning = self._llm_call(
            usage,
            staff_id=staff_id,
            institution_id=institution_id,
            call_type=AGENT_RISK_REASONING,
            fn=lambda: self._reasoning.reason(
                caretaker_turns=caretaker_turns,
                entries=universe,
                age_context=age_context,
                force_conclusion=force_conclusion,
                case_memory=case_memory,
            ),
        )
        if not reasoning.concluded:
            return PipelineResult(
                outcome=OUTCOME_FOLLOW_UP,
                turn=turn_number,
                age_uncertain=age_context.age_uncertain,
                follow_up_question=reasoning.follow_up_question,
                signals=list(observation.signals),
                prior_flags=prior_flags,
            )

        # 4) Deterministic grading (ADR-06 literal rule — never the model).
        by_ref = {entry.citation_ref: entry for entry in universe}
        red_flag_entries = [by_ref[r] for r in reasoning.confirmed_red_flags]
        missed_entries = [by_ref[r] for r in reasoning.missed_milestones]
        met_entries = [by_ref[r] for r in reasoning.met_milestones]
        modifier_entries = [by_ref[r] for r in reasoning.risk_modifiers]

        grade_result = grade(
            confirmed_flags=red_flag_entries,
            missed_milestones=missed_entries,
            risk_modifiers=modifier_entries,
            age_is_estimated=age_context.age_uncertain,
            key_items_missing=reasoning.key_items_missing or not observation.signals,
        )

        if grade_result.grade == GRADE_INSUFFICIENT_INFORMATION:
            return PipelineResult(
                outcome=OUTCOME_INSUFFICIENT_INFORMATION,
                turn=turn_number,
                age_uncertain=age_context.age_uncertain,
                grade=GRADE_INSUFFICIENT_INFORMATION,
                citation_refs=list(grade_result.citation_refs),
                explanation_text=_INSUFFICIENT_TEXT,
                loop_exhausted=force_conclusion,
                signals=list(observation.signals),
                prior_flags=prior_flags,
            )

        cited = red_flag_entries + missed_entries + met_entries + modifier_entries
        domain = _resolve_domain(cited)

        # Trail = the grade's own citations, then protective met-milestones
        # (deduped) — the clinician sees the rule AND the context.
        # `basis` and `source` are SNAPSHOTS taken now, not references
        # resolved later. A flag has to stay readable as the thing it was
        # when the grade was made: the knowledge base is upserted on
        # citation_ref, so a later wording change would otherwise silently
        # rewrite the stated basis of every historical flag (audit F11).
        trail: list[dict] = []
        for ref in grade_result.citation_refs:
            trail.append(
                {
                    "citation_ref": ref,
                    "basis": by_ref[ref].description,
                    "source": by_ref[ref].source,
                }
            )
        for entry in met_entries:
            if entry.citation_ref not in grade_result.citation_refs:
                trail.append(
                    {
                        "citation_ref": entry.citation_ref,
                        "basis": f"protective: {entry.description}",
                        "source": entry.source,
                    }
                )

        # 5) Explanation — mid-tier rephrasing, server-validated (ADR-07).
        explanation = self._llm_call(
            usage,
            staff_id=staff_id,
            institution_id=institution_id,
            call_type=AGENT_EXPLANATION,
            fn=lambda: self._explanation.explain(
                grade=grade_result.grade,
                domain=domain,
                trail=trail,
                age_uncertain=age_context.age_uncertain,
            ),
        )

        # 6) Persist the flag — the ONLY write path enforces the trail.
        FlagService(self._db).create_flag(
            institution_id=session.institution_id,
            session_id=session.id,
            child_id=child.id,
            domain=domain,
            confidence_grade=grade_result.grade.lower(),
            reasoning_trail=trail,
            explanation_text=explanation,
            status="flagged",
        )

        return PipelineResult(
            outcome=OUTCOME_FLAGGED,
            turn=turn_number,
            age_uncertain=age_context.age_uncertain,
            grade=grade_result.grade,
            domain=domain,
            citation_refs=[entry["citation_ref"] for entry in trail],
            explanation_text=explanation,
            loop_exhausted=force_conclusion,
            signals=list(observation.signals),
            prior_flags=prior_flags,
        )

    # ── helpers ─────────────────────────────────────────────────────

    def _prior_flags(self, child: Child, session: ConversationSession) -> list[dict]:
        """FEAT-07: this child's flags from EARLIER sessions (multi-session
        continuity). Child-scoped by construction — never cross-child."""
        from app.models.flag import Flag

        rows = self._db.execute(
            select(Flag)
            .where(Flag.child_id == child.id)
            .where(Flag.session_id != session.id)
            .order_by(Flag.created_at.asc())
        ).scalars().all()
        return [
            {
                "grade": row.confidence_grade,
                "domain": row.domain,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "citations": [
                    str(entry.get("citation_ref"))
                    for entry in (row.reasoning_trail or [])
                    if isinstance(entry, dict) and entry.get("citation_ref")
                ],
            }
            for row in rows
        ]

    @staticmethod
    def _case_memory_block(prior_flags: list[dict]) -> str | None:
        if not prior_flags:
            return None
        lines = []
        for flag in prior_flags:
            lines.append(
                f"- {flag['created_at']}: grade={flag['grade']} "
                f"domain={flag['domain']} basis={', '.join(flag['citations']) or '—'}"
            )
        return "\n".join(lines)

    def _with_passed_milestones(
        self, retrieved: list[Milestone], age_months: int
    ) -> list[KnowledgeEntry]:
        """Citable universe = in-scope retrieval + milestones whose band the
        child has already passed (age_max < age) — "already reached"
        protective evidence, e.g. a 30-month-old citing the 18-24 mo band."""
        universe = {row.citation_ref: KnowledgeEntry.from_row(row) for row in retrieved}
        passed = self._db.execute(
            select(Milestone)
            .where(Milestone.entry_type == ENTRY_TYPE_MILESTONE)
            .where(~Milestone.phase_scope.startswith("PHASE"))
            .where(Milestone.age_max_months < age_months)
            .order_by(Milestone.domain, Milestone.citation_ref)
        ).scalars().all()
        for row in passed:
            universe.setdefault(row.citation_ref, KnowledgeEntry.from_row(row))
        return sorted(universe.values(), key=lambda e: (e.domain, e.citation_ref))

    def _llm_call(self, usage, *, staff_id, institution_id, call_type, fn):
        """One LLM call = exactly one usage_log row (cost-DoS visibility).
        Cost is best-effort: adapters expose `last_call_cost` when the
        provider reports token usage; otherwise NULL by design."""
        result = fn()
        usage.record(
            staff_id=staff_id,
            institution_id=institution_id,
            provider="llm",
            call_type=call_type,
            estimated_cost=getattr(self.provider, "last_call_cost", None),
        )
        return result
