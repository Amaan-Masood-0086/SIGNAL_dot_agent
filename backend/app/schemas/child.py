"""Pydantic contracts for child intake + profile (FEAT-02).

ADR-02's dual confirmed/estimated age model is a server-side contract:
the two entry modes are mutually exclusive and validated here, never
trusted to frontend behavior alone (backend MUST — validation on every
route, TRD §4).
"""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    # Optional: defaults to the server's current date — server-derived,
    # never a silently assumed client timestamp.
    intake_date: datetime.date | None = None
    dob_confirmed: bool
    dob: datetime.date | None = None
    estimated_age_range: str | None = Field(default=None, max_length=50)
    estimated_age_note: str | None = None

    @model_validator(mode="after")
    def adr02_dual_age_contract(self) -> "ChildCreate":
        if self.dob_confirmed:
            problems: list[str] = []
            if self.dob is None:
                problems.append("dob is required when dob_confirmed is true")
            if self.estimated_age_range is not None or self.estimated_age_note is not None:
                problems.append(
                    "estimated-age fields must be empty when dob_confirmed is true"
                )
        else:
            problems = []
            if not self.estimated_age_range:
                problems.append(
                    "estimated_age_range is required when dob_confirmed is false"
                )
            if self.dob is not None:
                problems.append("dob must be null when dob_confirmed is false")
        if problems:
            raise ValueError("; ".join(problems))
        return self


class ChildRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    intake_date: datetime.date
    dob_confirmed: bool
    dob: datetime.date | None
    estimated_age_range: str | None
    estimated_age_note: str | None
    is_synthetic: bool
    created_at: datetime.datetime


class ChildPage(BaseModel):
    """Institution-scoped roster page for the dashboard list."""

    items: list[ChildRead]
    total: int
    page: int
    page_size: int
