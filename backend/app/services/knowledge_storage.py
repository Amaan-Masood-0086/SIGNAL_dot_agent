"""Store all draft domains with no effect on the V2 reasoning pipeline."""
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.models.knowledge_revision import KnowledgeRevision
from app.services.knowledge_release import fingerprint
from app.services.knowledge_v3 import Entry


def store_revisions(db: Session, release_snapshot_id: int, manifest: dict) -> int:
    db.execute(text("SELECT pg_advisory_xact_lock(736194022)"))
    existing = set(db.execute(select(KnowledgeRevision.citation_ref).where(KnowledgeRevision.release_snapshot_id == release_snapshot_id)).scalars())
    count = 0
    for item in manifest["entries"]:
        entry = Entry.model_validate(item["snapshot"]["entry"])
        if fingerprint(item["snapshot"]) != item["content_sha256"]:
            raise ValueError("Revision fingerprint mismatch")
        if entry.citation_ref in existing:
            continue
        db.add(KnowledgeRevision(release_snapshot_id=release_snapshot_id, citation_ref=entry.citation_ref,
            revision=item["content_sha256"], domain=entry.domain, snapshot=item["snapshot"],
            review_status="needs_clinical_review", runtime_enabled=False))
        count += 1
    db.flush()
    return count


def eligible_runtime_revisions(db: Session, release_snapshot_id: int) -> list[KnowledgeRevision]:
    """Defense in depth for a future approved runtime consumer.

    This query does not activate anything and is not wired to live V2.
    Both switches must pass; missing approval always returns no content.
    """
    return list(db.execute(select(KnowledgeRevision).where(
        KnowledgeRevision.release_snapshot_id == release_snapshot_id,
        KnowledgeRevision.review_status == "approved",
        KnowledgeRevision.runtime_enabled.is_(True),
    ).order_by(KnowledgeRevision.citation_ref)).scalars())
