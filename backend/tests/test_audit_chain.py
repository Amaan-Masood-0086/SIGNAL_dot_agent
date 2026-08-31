"""Hash-chained audit log — THREAT_MODEL §1 (Tampering) + TEST_PLAN §3.

Each entry stores hash_prev (the hash of the previous entry) and hash_self.
Any edit to a historical row breaks the chain and must be detectable — this
is the technical basis of SIGNAL's liability-protection value proposition.
"""

from __future__ import annotations

import uuid

import pytest

from app.services.audit import AuditService, verify_audit_chain


@pytest.fixture(autouse=True)
def _clean_audit_table(db_session):
    """These tests COMMIT (the chain must be durable to verify), and pooled
    connections persist committed rows across tests. Give every test a
    clean chain (GENESIS semantics) and leak nothing into later modules."""
    from sqlalchemy import delete

    from app.models.audit_log import AuditLogEntry

    db_session.execute(delete(AuditLogEntry))
    db_session.commit()
    yield
    db_session.execute(delete(AuditLogEntry))
    db_session.commit()


def _staff_and_institution_ids() -> tuple[str, str]:
    return str(uuid.uuid4()), str(uuid.uuid4())


def test_append_builds_a_verifiable_chain(db_session):
    actor_id, institution_id = _staff_and_institution_ids()
    service = AuditService(db_session)

    first = service.append(
        actor_id=actor_id,
        action="child.created",
        resource_type="children",
        resource_id=str(uuid.uuid4()),
        institution_id=institution_id,
    )
    second = service.append(
        actor_id=actor_id,
        action="session.started",
        resource_type="sessions",
        resource_id=str(uuid.uuid4()),
        institution_id=institution_id,
    )
    db_session.commit()

    assert first.hash_prev == AuditService.GENESIS_HASH
    assert second.hash_prev == first.hash_self
    assert verify_audit_chain(db_session) is True


def test_tamper_detection_catches_altered_history(db_session):
    """TEST_PLAN §3: alter a historical row directly → chain verification fails."""
    from app.models.audit_log import AuditLogEntry

    actor_id, institution_id = _staff_and_institution_ids()
    service = AuditService(db_session)
    service.append(
        actor_id=actor_id,
        action="flag.created",
        resource_type="flags",
        resource_id=str(uuid.uuid4()),
        institution_id=institution_id,
    )
    service.append(
        actor_id=actor_id,
        action="referral.created",
        resource_type="referrals",
        resource_id=str(uuid.uuid4()),
        institution_id=institution_id,
    )
    db_session.commit()

    # Tamper: rewrite the first entry's action in place.
    first = db_session.query(AuditLogEntry).order_by(AuditLogEntry.sequence).first()
    first.action = "flag.deleted"
    db_session.commit()

    assert verify_audit_chain(db_session) is False
