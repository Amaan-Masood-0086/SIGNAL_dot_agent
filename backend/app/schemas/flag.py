"""Flag display schemas (FEAT-09).

The reasoning trail is returned RESOLVED: each entry carries the cited
knowledge-base row's description + source so a clinician can independently
review the basis (ADR-03/08; TEST_PLAN §3 citation integrity).
"""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class TrailEntryRead(BaseModel):
    citation_ref: str
    basis: str | None = None
    description: str | None = None
    source: str | None = None
    # The knowledge-base row has been edited since this flag was written.
    # The basis shown is still the one the grade was made on (audit F11).
    kb_drifted: bool = False


class FlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    child_id: uuid.UUID
    domain: str
    confidence_grade: str
    status: str
    explanation_text: str | None
    created_at: datetime.datetime
    reasoning_trail: list[TrailEntryRead]


class FlagPage(BaseModel):
    items: list[FlagRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
