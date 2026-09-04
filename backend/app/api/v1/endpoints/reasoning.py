"""Reasoning endpoint — POST /sessions/{id}/reason (FEAT-05).

The caretaker-facing surface of the Observation → Risk Reasoning →
Explanation pipeline. Institution-scoped exactly like every business
endpoint: the system-level admin role gains NOTHING here (RLS boundary).

The LLM provider is an injectable seam (FEAT-03 STT pattern): configured
provider wins; `synthetic_only` environments fall back to the deterministic
synthetic reasoner; anything else → clean 503 with text-fallback guidance.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentStaff,
    get_current_verified_staff,
    get_tenant_db,
    require_active_staff,
)
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.core.synthetic_gate import assert_synthetic_write
from app.services.credential_service import CredentialConfigError, CredentialService
from app.models.institution import Institution
from app.models.observation import Observation
from app.models.session import Session as ConversationSession
from app.services.audit import AuditService
from app.services.llm import LLMProvider, build_llm_provider, provider_from_settings
from app.services.pipeline_agents import AgentContractError, GroundingError
from app.services.llm import LLMError
from app.services.risk_pipeline import (
    MAX_TURNS,
    OUTCOME_FLAGGED,
    OUTCOME_FOLLOW_UP,
    LoopCapExceeded,
    PipelineError,
    RiskPipeline,
)

router = APIRouter(prefix="/sessions", tags=["reasoning"])

# Same budget as the turn-capture surface (TRD §4): every reason call sits
# upstream of at least one paid LLM call.
REASON_LIMITER = FixedWindowRateLimiter(limit=30, window_seconds=60.0)

FOLLOW_UP_MARKER = {"role": "risk_reasoning", "follow_up": True}


class ReasoningRequest(BaseModel):
    raw_input: str = Field(min_length=1, max_length=10_000)
    # Which language the caretaker READS. "auto" mirrors whatever they wrote,
    # which is right until it isn't: plenty of caretakers type Roman English
    # because the keyboard is easier while reading Urdu far more comfortably,
    # and no amount of detection can see that.
    #
    # A closed enum on purpose. The caretaker's own text stays fenced as DATA
    # and is never treated as instructions, so "reply in Urdu" typed into the
    # box must not steer the model. A structured field is how a preference
    # gets expressed without reopening that door.
    response_language: Literal["auto", "ur", "en"] = "auto"

    @field_validator("raw_input")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("raw_input must not be blank")
        return stripped


def rate_limited_reason(
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
) -> None:
    if not REASON_LIMITER.allow(str(current_staff.staff_id)):
        raise HTTPException(
            status_code=429,
            detail="Too many reasoning requests; try again in a minute",
        )


def get_reasoning_provider(
    settings: Settings = Depends(get_settings),
    db: Session | None = Depends(get_tenant_db),
) -> LLMProvider | None:
    """ADR-10 precedence: an ACTIVE stored LLM credential beats the env var;
    with no stored row the env path runs unchanged (FEAT-05's bootstrap/CI
    mechanism — the smoke script depends on it). Only when NEITHER exists
    does synthetic_only fall back to the deterministic reasoner."""
    if db is not None:
        try:
            stored, stored_model = CredentialService(db, settings).resolve_with_model("llm")
        except CredentialConfigError:
            stored, stored_model = None, None
        if stored:
            return build_llm_provider(settings, api_key=stored, model=stored_model)
    provider = provider_from_settings(settings)
    if provider is not None:
        return provider
    if settings.ENVIRONMENT == "synthetic_only":
        from app.services.synthetic_llm import SyntheticRuleLLM

        return SyntheticRuleLLM()
    return None


def _is_follow_up_row(row: Observation) -> bool:
    return bool(row.extracted_signals) and row.extracted_signals.get("follow_up") is True


@router.post("/{session_id}/reason")
def reason(
    session_id: uuid.UUID,
    payload: ReasoningRequest,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    _: None = Depends(rate_limited_reason),
    __: CurrentStaff = Depends(require_active_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_tenant_db),
    provider: LLMProvider | None = Depends(get_reasoning_provider),
):
    session = db.get(ConversationSession, session_id)
    if session is None or session.institution_id != current_staff.institution_id:
        # Uniform 403 — existence never leaks across the tenant boundary.
        raise HTTPException(status_code=403, detail="Access denied")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")

    institution = db.get(Institution, current_staff.institution_id)
    if institution is None:
        raise HTTPException(status_code=403, detail="Institution not recognized")
    assert_synthetic_write(bool(institution.is_synthetic), environment=settings.ENVIRONMENT)

    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Reasoning is not configured; use the text notes for now",
        )

    # Turn accounting: caretaker turns only — server-assigned follow-up
    # questions do not count against the adaptive-loop cap.
    rows = db.execute(
        select(Observation)
        .where(Observation.session_id == session.id)
        .order_by(Observation.turn_number.asc())
    ).scalars().all()
    caretaker_turns = [row.raw_input for row in rows if not _is_follow_up_row(row)]
    turn_number = len(caretaker_turns) + 1
    if turn_number > MAX_TURNS:
        raise HTTPException(
            status_code=409,
            detail=f"Conversation cap reached ({MAX_TURNS} turns) — "
            f"this session must conclude",
        )

    # Persist the caretaker turn first (server-assigned turn number).
    last_turn = db.execute(
        select(func.max(Observation.turn_number)).where(
            Observation.session_id == session.id
        )
    ).scalar_one()
    caretaker_row = Observation(
        institution_id=session.institution_id,
        session_id=session.id,
        turn_number=(last_turn or 0) + 1,
        raw_input=payload.raw_input,
    )
    db.add(caretaker_row)
    db.flush()
    caretaker_turns.append(payload.raw_input)

    try:
        result = RiskPipeline(db, provider).run(
            session=session,
            child=_child_or_fail(db, session),
            caretaker_turns=caretaker_turns,
            turn_number=turn_number,
            staff_id=current_staff.staff_id,
            response_language=payload.response_language,
            institution_id=current_staff.institution_id,
        )
    except LoopCapExceeded as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PipelineError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except (GroundingError, AgentContractError, LLMError) as exc:
        # Never surface model/provider internals to the CLIENT (MUST-NOT #1),
        # but the server log has to say what actually happened or a 502 is
        # undiagnosable.
        import logging

        logging.getLogger("signal.reasoning").error(
            "reasoning failed: %s: %s", type(exc).__name__, exc
        )
        raise HTTPException(status_code=502, detail="Reasoning failed")

    # Persist the outcome artifacts.
    caretaker_row.extracted_signals = {"signals": list(result.signals)}
    flag_id = None
    if result.outcome == OUTCOME_FOLLOW_UP and result.follow_up_question:
        db.add(Observation(
            institution_id=session.institution_id,
            session_id=session.id,
            turn_number=(last_turn or 0) + 2,
            raw_input=result.follow_up_question,
            extracted_signals=FOLLOW_UP_MARKER,
        ))
    if result.outcome == OUTCOME_FLAGGED:
        from app.models.flag import Flag

        flag = db.execute(
            select(Flag)
            .where(Flag.session_id == session.id)
            .order_by(Flag.created_at.desc())
            .limit(1)
        ).scalars().first()
        flag_id = str(flag.id) if flag else None
        AuditService(db).append(
            actor_id=str(current_staff.staff_id),
            action="flag.create",
            resource_type="flag",
            resource_id=flag_id or "unknown",
            institution_id=str(current_staff.institution_id),
        )

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="reasoning.run",
        resource_type="reasoning",
        resource_id=str(session.id),
        institution_id=str(current_staff.institution_id),
    )

    return envelope({
        "status": result.outcome,
        "turn": result.turn,
        "max_turns": MAX_TURNS,
        "follow_up_question": result.follow_up_question,
        "grade": result.grade,
        "domain": result.domain,
        "citations": result.citation_refs,
        "explanation_text": result.explanation_text,
        "age_uncertain": result.age_uncertain,
        "loop_exhausted": result.loop_exhausted,
        "flag_id": flag_id,
    })


def _child_or_fail(db: Session, session: ConversationSession):
    from app.models.child import Child

    child = db.get(Child, session.child_id)
    if child is None:
        raise HTTPException(status_code=409, detail="Session has no child record")
    return child
