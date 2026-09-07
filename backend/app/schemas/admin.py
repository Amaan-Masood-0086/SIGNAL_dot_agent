"""Pydantic schemas for the Admin Panel (RBAC ticket).

Every admin response is validated through these schemas — credential
material (hashed_password, provider keys) has no field here and can never
leak through serialization (ADR-09 for provider keys, OWASP A02 in general).
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.child import ChildCreate

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

    # `model_name` collides with Pydantic's reserved `model_` namespace and
    # raised a UserWarning at import. `pytest.ini` sets `filterwarnings =
    # error`, so it was one `import` away from failing collection outright
    # and only stayed quiet because nothing imported this module early
    # enough. The field name is part of the API contract; the namespace is
    # not, so narrow the namespace.
    model_config = ConfigDict(protected_namespaces=())

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
    # Responsibility + roster state, so the console can show and change both
    # without a second round-trip per row.
    assigned_staff_id: uuid.UUID | None = None
    archived_at: datetime.datetime | None = None
    archived_reason: str | None = None


class AdminChildPage(BaseModel):
    items: list[AdminChildRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


# ── Onboarding: institution → staff → child ────────────────────────────────
#
# Every one of these takes the institution EXPLICITLY. The system-level admin
# belongs to the NextaSol tenant, not to any institution that delivers care,
# so deriving scope from their token — the way the caretaker routes correctly
# do — would file real children under the system tenant. `nav.ts` calls that
# "clean data that is quietly wrong", and a required field is what stops it.


class InstitutionCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]


class InstitutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_synthetic: bool
    created_at: datetime.datetime


class InstitutionPage(BaseModel):
    items: list[InstitutionRead]
    total: int


class StaffCreate(BaseModel):
    """Create a staff account.

    No password field, and that is deliberate rather than an omission: login
    does not verify passwords yet (FEAT-12), so accepting one here would
    store a credential nothing checks and imply a guarantee the system does
    not make. The row gets an unusable placeholder hash until real
    verification lands.
    """

    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=320)]
    role: StaffRole
    institution_id: uuid.UUID


class ChildAssignment(BaseModel):
    """Who is responsible for a child. `None` clears the assignment —
    unassigned is a legitimate state (a carer leaves, a child is between
    carers), not a defect to be prevented."""

    staff_id: uuid.UUID | None = None


class AdminChildCreate(ChildCreate):
    """The caretaker intake contract plus an explicit institution.

    Subclassing `ChildCreate` is the point: the ADR-02 dual-age validator is
    inherited whole, so the admin path cannot drift into a weaker version of
    the rule that confirmed-DOB and estimated-range are mutually exclusive.
    """

    institution_id: uuid.UUID


def cost_or_none(calls: int | None, cost_sum: "decimal.Decimal | None") -> float | None:
    """A cost figure that tells "free" apart from "never recorded".

    `usage_log.estimated_cost` is nullable ON PURPOSE and the two states mean
    different things: an STT provider test hits a FREE usage endpoint and
    records `Decimal("0")`, while an LLM test connection is a real billed
    call whose price cannot be computed and records NULL. Coercing NULL to
    0.0 collapses that distinction and quietly under-reports the figure an
    operator is reconciling against a vendor invoice.

    `SUM` over no rows is NULL too, but that case genuinely IS zero — no
    calls were made — so the call count settles which NULL this is.

    Note the explicit `is None`: the previous `float(x) if x else 0.0` also
    sent a real `Decimal("0")` down the fallback branch, so a genuinely free
    provider was indistinguishable from an unrecorded one even before the
    NULLs were considered.
    """
    if not calls:
        return 0.0
    if cost_sum is None:
        return None
    return float(cost_sum)


class UsageTotals(BaseModel):
    calls: int
    estimated_cost: float | None
    # How many of `calls` carry no cost at all. Without this, a set holding
    # ten priced calls and three unpriced ones sums to the ten-call figure
    # and READS as complete — the same under-reporting as coercing NULL to
    # zero, just harder to notice. `SUM` skips NULLs silently; this says so.
    unpriced_calls: int = 0

    @classmethod
    def from_counts(
        cls,
        calls: int | None,
        priced_calls: int | None,
        cost_sum: "decimal.Decimal | None",
    ) -> "UsageTotals":
        """Build from `COUNT(id)`, `COUNT(estimated_cost)` and `SUM(...)`.

        `COUNT(<column>)` counts non-NULLs, so the gap between the two
        counts is exactly the number of calls with no recorded price.
        """
        total_calls = calls or 0
        return cls(
            calls=total_calls,
            estimated_cost=cost_or_none(total_calls, cost_sum),
            unpriced_calls=total_calls - (priced_calls or 0),
        )


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
