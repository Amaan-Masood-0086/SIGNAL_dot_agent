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


class ReferralRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    flag_id: uuid.UUID
    status: str
    responsible_person: str | None
    review_date: datetime.date | None
    escalated: bool
    caretaker_confirmed: bool
    created_at: datetime.datetime
