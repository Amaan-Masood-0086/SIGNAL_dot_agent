"""Versioned reference rows; draft storage is separate from live milestones."""
from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.types import JSONVariant


class KnowledgeRevision(Base):
    __tablename__ = "knowledge_revisions"
    __table_args__ = (
        UniqueConstraint("release_snapshot_id", "citation_ref", "revision", name="uq_knowledge_revision"),
        CheckConstraint("domain IN ('Speech_Language','Hearing','Vision','Motor','Social_Communication','Attention','Attachment','Context','Safety','Safeguarding')", name="ck_revision_domain"),
        CheckConstraint("review_status IN ('needs_clinical_review','approved','excluded')", name="ck_revision_review"),
        CheckConstraint("NOT runtime_enabled OR review_status = 'approved'", name="ck_revision_activation"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    release_snapshot_id: Mapped[int] = mapped_column(ForeignKey("knowledge_releases.id"), nullable=False)
    citation_ref: Mapped[str] = mapped_column(String(80), nullable=False)
    revision: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONVariant, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="needs_clinical_review")
    runtime_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
