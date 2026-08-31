"""FlagService — the ONLY write path into `flags` (FEAT-05).

ADR-03 (as refined by ADR-08): every flag's `reasoning_trail` must cite one
or more REAL knowledge-base entries by `citation_ref`. Enforcement lives
HERE, at the service layer — not in schema hope, not in prompt wishes:

- empty/missing trail → rejected
- any citation_ref that does not resolve to an ingested `milestones` row
  → rejected (a trail is only as credible as its weakest citation)
- domain must use ADR-07 naming (Speech_Language | Hearing — never "DLD")
- confidence_grade must be one of the four ADR-06 states

Safeguarding signals NEVER come through here — that pathway is a separate
table/service by design (sdlc-security rule 14; FEAT-11 owns the write).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.flag import CONFIDENCE_GRADES, FLAG_DOMAINS, FLAG_STATUSES, Flag
from app.models.milestone import Milestone


class FlagValidationError(ValueError):
    """A flag that violates ADR-03/06/07 invariants — never persisted."""


class FlagService:
    def __init__(self, session: Session):
        self._session = session

    def create_flag(
        self,
        *,
        institution_id: uuid.UUID,
        session_id: uuid.UUID,
        child_id: uuid.UUID,
        domain: str,
        confidence_grade: str,
        reasoning_trail: list | None,
        status: str,
        explanation_text: str | None = None,
    ) -> Flag:
        if domain not in FLAG_DOMAINS:
            raise FlagValidationError(
                f"Unknown domain {domain!r} — ADR-07 naming only: {FLAG_DOMAINS}"
            )
        if confidence_grade not in CONFIDENCE_GRADES:
            raise FlagValidationError(
                f"Unknown confidence grade {confidence_grade!r} — "
                f"ADR-06 four states only: {CONFIDENCE_GRADES}"
            )
        if status not in FLAG_STATUSES:
            raise FlagValidationError(f"Unknown flag status {status!r}")

        self._validate_trail(reasoning_trail)

        flag = Flag(
            institution_id=institution_id,
            session_id=session_id,
            child_id=child_id,
            domain=domain,
            confidence_grade=confidence_grade,
            reasoning_trail=reasoning_trail,
            explanation_text=explanation_text,
            status=status,
        )
        self._session.add(flag)
        return flag

    def _validate_trail(self, reasoning_trail: list | None) -> None:
        """ADR-03: non-empty trail; ADR-08: every citation_ref resolves."""
        if not reasoning_trail:
            raise FlagValidationError(
                "reasoning_trail is mandatory — a flag without a cited basis "
                "is a compliance failure (ADR-03)"
            )
        refs: list[str] = []
        for entry in reasoning_trail:
            if not isinstance(entry, dict) or not entry.get("citation_ref"):
                raise FlagValidationError(
                    "every reasoning_trail entry must carry a citation_ref"
                )
            refs.append(str(entry["citation_ref"]))

        known = set(
            self._session.execute(
                select(Milestone.citation_ref).where(
                    Milestone.citation_ref.in_(refs)
                )
            ).scalars().all()
        )
        dangling = [ref for ref in refs if ref not in known]
        if dangling:
            raise FlagValidationError(
                f"reasoning_trail cites unknown knowledge-base entries "
                f"{dangling} — ungrounded citations are rejected (ADR-03/08)"
            )
