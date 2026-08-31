"""Pydantic schemas for the Admin Panel (RBAC ticket).

Every admin response is validated through these schemas — credential
material (hashed_password, provider keys) has no field here and can never
leak through serialization (ADR-09 for provider keys, OWASP A02 in general).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
    """ADR-09: configured/not-configured from env presence at startup.
    Key VALUES are never serialized — no field for them exists."""

    provider: Literal["stt", "llm"]
    backend: str  # e.g. "azure", "openai_compatible", "none"
    configured: bool
    detail: str


class ProviderTestResult(BaseModel):
    provider: Literal["stt", "llm"]
    success: bool
    detail: str


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
    by_staff: list[UsageByStaff]
    by_institution: list[UsageByInstitution]
