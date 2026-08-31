"""FEAT-03 — session + observation schemas.

The observation payload is MODE-AGNOSTIC by design: voice input arrives as a
transcript and typed input as text, both through the same endpoint and schema
(FEAT-03 acceptance: identical downstream observation format).

Server-generated values (turn_number, timestamps, ids) NEVER come from the
request body (backend coding contract #5) — `SessionCreate` and
`ObservationCreate` simply have no such fields.
"""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

SESSION_MODES = ("voice", "text")


class SessionCreate(BaseModel):
    child_id: uuid.UUID
    mode: str = Field(pattern="^(voice|text)$")


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    child_id: uuid.UUID
    staff_id: uuid.UUID
    status: str
    mode: str
    started_at: datetime.datetime
    resumed_at: datetime.datetime | None
    created_at: datetime.datetime


class ObservationCreate(BaseModel):
    # Unknown fields (e.g. a client-supplied turn_number) are ignored —
    # server-generated values are never honored from the body (MUST #5).
    model_config = ConfigDict(extra="ignore")

    raw_input: str = Field(min_length=1, max_length=10_000)

    @field_validator("raw_input")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("raw_input must not be blank")
        return stripped


class ObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    session_id: uuid.UUID
    turn_number: int
    raw_input: str
    extracted_signals: dict | None
    created_at: datetime.datetime


class ObservationPage(BaseModel):
    items: list[ObservationRead]
    total: int
    page: int
    page_size: int
