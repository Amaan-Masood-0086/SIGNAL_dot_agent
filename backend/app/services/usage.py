"""Usage ledger service (RISK_REGISTER cost-DoS mitigation).

Rate limiting caps abuse blindly; this ledger makes the numbers VISIBLE —
per-staff and per-institution call counts + best-effort cost, queryable by
the staff member themselves and by the admin panel.

Hook points: the STT transcribe endpoint records here today; the FEAT-05
reasoning pipeline records every LLM call through the SAME seam
(provider="llm", call_type = pipeline stage) when it lands.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.usage_log import UsageLog

# ── Best-effort STT cost model ───────────────────────────────────────────────
# Azure Speech standard pricing is ~$1 per 1000 minutes of audio. Browser
# opus voice runs ~32-64 kbps; 6 KiB/s brackets that range, so duration is
# estimated from payload size. This is deliberately a rough order-of-
# magnitude estimate (the column is "estimated_cost", nullable by design).
AZURE_STT_COST_PER_SECOND = Decimal("1") / Decimal(60_000)  # $1 / 1000 min
OPUS_BYTES_PER_SECOND = Decimal(6144)


def estimate_stt_cost(audio_bytes: int) -> Decimal:
    seconds = Decimal(audio_bytes) / OPUS_BYTES_PER_SECOND
    return (seconds * AZURE_STT_COST_PER_SECOND).quantize(Decimal("0.000001"))


class UsageService:
    """Appends usage rows; the table is append-only at the DB role level."""

    def __init__(self, session: Session):
        self._session = session

    def record(
        self,
        *,
        staff_id: uuid.UUID,
        institution_id: uuid.UUID,
        provider: str,
        call_type: str,
        estimated_cost: Decimal | None = None,
    ) -> UsageLog:
        row = UsageLog(
            staff_id=staff_id,
            institution_id=institution_id,
            provider=provider,
            call_type=call_type,
            estimated_cost=estimated_cost,
        )
        self._session.add(row)
        return row
