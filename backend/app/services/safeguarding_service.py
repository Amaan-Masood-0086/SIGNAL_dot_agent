"""SafeguardingService — the ONLY write path into safeguarding_escalations.

Deliberately separate from FlagService — no shared code path between the
two tables, ever (sdlc-security rule 14). Developmental concerns go to
flags; abuse/neglect-pattern signals go here. Phase 1 depth is the stub:
routing + row write. The downstream mandatory-reporting process is out of
scope until PROJECT_BRIEF Open Item #6 is decided.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.safeguarding_escalation import SafeguardingEscalation


class SafeguardingService:
    def __init__(self, session: Session):
        self._session = session

    def escalate(
        self,
        *,
        institution_id: uuid.UUID,
        session_id: uuid.UUID,
        child_id: uuid.UUID,
        signal_description: str,
    ) -> SafeguardingEscalation:
        escalation = SafeguardingEscalation(
            institution_id=institution_id,
            session_id=session_id,
            child_id=child_id,
            signal_description=signal_description,
            status="open",
        )
        self._session.add(escalation)
        return escalation
