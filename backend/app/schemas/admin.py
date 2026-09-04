"""Pydantic schemas for the Admin Panel (RBAC ticket).

Every admin response is validated through these schemas — credential
material (hashed_password, provider keys) has no field here and can never
leak through serialization (ADR-09 for provider keys, OWASP A02 in general).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

StaffRole = Literal["caretaker", "admin"]


class StaffRead(BaseModel):
    """Admin staff view — deliberately contains NO credential fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime.datetime


class StaffPage(BaseModel):
    items: list[StaffRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class StaffRoleUpdate(BaseModel):
    role: StaffRole


class StaffActiveUpdate(BaseModel):
    is_active: bool


class AuditLogEntryRead(BaseModel):
    """Read-only audit row. Hashes are exposed on purpose — tamper-evidence
    is the product; the chain's hashes are not secrets."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sequence: int
    actor_id: uuid.UUID | None
    institution_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime.datetime
    hash_prev: str
    hash_self: str


class AuditLogPage(BaseModel):
    items: list[AuditLogEntryRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class AuditChainStatus(BaseModel):
    chain_intact: bool
    entries_checked: int
    first_broken_sequence: int | None = None


class ProviderStatus(BaseModel):
    """ADR-09/10: configured/not-configured status. Key VALUES are never
    serialized — no field for them exists. `source` says WHERE the active
    credential came from: "ui" (provider_credentials row), "env" (env var),
    or None (not configured)."""

    provider: Literal["stt", "llm"]
    backend: str  # e.g. "azure", "openai_compatible", "none"
    configured: bool
    detail: str
    source: Literal["ui", "env"] | None = None


class ProviderTestResult(BaseModel):
    provider: Literal["stt", "llm"]
    success: bool
    detail: str


class CredentialWrite(BaseModel):
    """ADR-10 PUT body. The value is accepted once, encrypted, and then can
    never be read back through any API surface."""

    value: Annotated[
        str, StringConstraints(min_length=1, max_length=2000, strip_whitespace=True)
    ]
    # Non-secret provider setting (LLM model name). Plaintext on purpose;
    # the KEY above is the only encrypted field.
    model: str | None = Field(default=None, max_length=120)


class CredentialStatusRead(BaseModel):
    """The ONLY credential shape that ever leaves the API — deliberately
    missing any field that could carry the raw or encrypted value."""

    provider: str
    is_active: bool
    masked_suffix: str | None = None
    updated_at: datetime.datetime | None = None
    model_name: str | None = None


class AdminChildRead(BaseModel):
    """Cross-institution child row for the admin console (owner-requested
    oversight view, 2026-09-01). Read-only; no clinical detail beyond what
    the roster shows."""

    id: uuid.UUID
    name: str
    institution_id: uuid.UUID
    institution_name: str
    dob_confirmed: bool
    dob: datetime.date | None = None
    estimated_age_range: str | None = None
    intake_date: datetime.date


class AdminChildPage(BaseModel):
    items: list[AdminChildRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class UsageTotals(BaseModel):
    calls: int
    estimated_cost: float | None


class UsageByProvider(BaseModel):
    stt: UsageTotals
    llm: UsageTotals


class MyUsage(BaseModel):
    staff_id: uuid.UUID
    total: UsageTotals
    by_provider: UsageByProvider


class UsageByStaff(BaseModel):
    staff_id: uuid.UUID
    email: str
    institution_id: uuid.UUID
    calls: int
    estimated_cost: float | None


class UsageByInstitution(BaseModel):
    institution_id: uuid.UUID
    name: str
    calls: int
    estimated_cost: float | None


class AllUsage(BaseModel):
    total: UsageTotals
    # STT and LLM are DIFFERENT VENDORS with different invoices. A single
    # combined figure cannot be reconciled against either one, so the split
    # travels with the total rather than being left to the reader to guess.
    # (`UsageByProvider` already existed for the caretaker's own view; the
    # admin console simply never surfaced it.)
    by_provider: UsageByProvider
    by_staff: list[UsageByStaff]
    by_institution: list[UsageByInstitution]
