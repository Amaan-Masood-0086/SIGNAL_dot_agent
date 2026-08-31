"""ReferralService — loop-closing record (FEAT-10).

TRD business rule #3 / backend MUST #15: a referral can NEVER persist
without an explicit caretaker confirmation step — the gate is enforced
HERE, at the service layer, not only in request validation.

Escalation: an open referral past its review date is escalated. The
effective state is evaluated on every read/write; a status update
persists it so the audit trail reflects reality.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.referral import Referral


class ReferralValidationError(ValueError):
    """A referral write that violates the confirmation gate."""


class ReferralService:
    def __init__(self, session: Session):
        self._session = session

    def create_referral(
        self,
        *,
        institution_id: uuid.UUID,
        flag_id: uuid.UUID,
        caretaker_confirmed: bool,
        responsible_person: str | None = None,
        review_date: datetime.date | None = None,
    ) -> Referral:
        if not caretaker_confirmed:
            raise ReferralValidationError(
                "a referral requires the explicit caretaker confirmation step "
                "— it can never auto-populate (TRD business rule #3)"
            )
        referral = Referral(
            institution_id=institution_id,
            flag_id=flag_id,
            status="referred",
            responsible_person=responsible_person,
            review_date=review_date,
            escalated=False,
            caretaker_confirmed=True,
        )
        self._session.add(referral)
        return referral

    @staticmethod
    def is_overdue(referral: Referral, today: datetime.date) -> bool:
        return (
            referral.status != "closed"
            and referral.review_date is not None
            and referral.review_date < today
        )

    def effective_escalated(self, referral: Referral) -> bool:
        """Persisted escalation OR a freshly-missed review date."""
        return referral.escalated or self.is_overdue(
            referral, datetime.date.today()
        )
