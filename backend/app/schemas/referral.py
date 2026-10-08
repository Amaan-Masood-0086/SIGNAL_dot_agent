"""Referral schemas (FEAT-10)."""

from __future__ import annotations

import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReferralStatus = Literal["referred", "pending_capacity", "closed"]


class ReferralCreate(BaseModel):
    caretaker_confirmed: bool = False
    responsible_person: str | None = Field(default=None, max_length=200)
    review_date: datetime.date | None = None


class ReferralUpdate(BaseModel):
    status: ReferralStatus | None = None
    responsible_person: str | None = Field(default=None, max_length=200)
    review_date: datetime.date | None = None
    outcome: Literal["confirmed", "ruled_out", "lost_to_followup", "not_yet_assessed"] | None = None
    clinician_note: str | None = Field(default=None, max_length=2000)


class ReferralRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    flag_id: uuid.UUID
    status: str
    responsible_person: str | None
    review_date: datetime.date | None
    escalated: bool
    caretaker_confirmed: bool
    outcome: str
    clinician_note: str | None
    created_at: datetime.datetime


class ReferralPage(BaseModel):
    items: list[ReferralRead]
    total: int
    page: int
    page_size: int
