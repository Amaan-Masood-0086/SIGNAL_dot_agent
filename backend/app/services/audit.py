"""Append-only, hash-chained audit log (THREAT_MODEL §1 — Tampering).

Each entry's `hash_self` commits to the previous entry's `hash_self` via
`hash_prev`, so any edit to a historical row breaks the chain and is
detectable by `verify_audit_chain()`. This is the technical basis of
SIGNAL's liability-protection value proposition — business-critical.
"""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLogEntry


class AuditService:
    """Writes audit entries and maintains the hash chain."""

    GENESIS_HASH = "0" * 64

    def __init__(self, session: Session):
        self._session = session

    def _last_hash_and_sequence(self) -> tuple[str, int]:
        row = self._session.execute(
            select(AuditLogEntry.hash_self, AuditLogEntry.sequence).order_by(
                AuditLogEntry.sequence.desc()
            ).limit(1)
        ).first()
        if row is None:
            return self.GENESIS_HASH, 0
        return row.hash_self, row.sequence

    def append(
        self,
        *,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        institution_id: str | None = None,
    ) -> AuditLogEntry:
        """Append a new entry, chaining its hash to the previous entry."""
        last_hash, last_sequence = self._last_hash_and_sequence()
        entry = AuditLogEntry(
            sequence=last_sequence + 1,
            actor_id=uuid.UUID(actor_id) if actor_id else None,
            institution_id=uuid.UUID(institution_id) if institution_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        entry.hash_prev = last_hash
        entry.hash_self = self._compute_hash(entry, last_hash)
        self._session.add(entry)
        return entry

    @staticmethod
    def _canonical_payload(entry: AuditLogEntry, hash_prev: str) -> str:
        return "|".join(
            [
                hash_prev,
                str(entry.sequence),
                str(entry.actor_id),
                entry.action,
                entry.resource_type,
                entry.resource_id,
            ]
        )

    @classmethod
    def _compute_hash(cls, entry: AuditLogEntry, hash_prev: str) -> str:
        payload = cls._canonical_payload(entry, hash_prev)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_audit_chain_detail(session: Session) -> tuple[bool, int, int | None]:
    """Re-walk the chain in sequence order.

    Returns (chain_intact, entries_checked, first_broken_sequence) — the
    admin viewer surfaces "chain intact" or the exact position where the
    chain first breaks (THREAT_MODEL §1 Tampering).
    """
    rows = session.execute(
        select(AuditLogEntry).order_by(AuditLogEntry.sequence.asc())
    ).scalars().all()

    expected_prev = AuditService.GENESIS_HASH
    checked = 0
    for entry in rows:
        checked += 1
        if entry.hash_prev != expected_prev:
            return False, checked, entry.sequence
        if entry.hash_self != AuditService._compute_hash(entry, entry.hash_prev):
            return False, checked, entry.sequence
        expected_prev = entry.hash_self
    return True, checked, None


def verify_audit_chain(session: Session) -> bool:
    """Re-walk the chain in sequence order; any mismatch = tamper detected."""
    intact, _, _ = verify_audit_chain_detail(session)
    return intact
