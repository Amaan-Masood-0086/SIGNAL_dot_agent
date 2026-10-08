"""System-admin review notes, separate from runtime clinical evidence."""
import datetime as dt
import uuid
from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class KnowledgeReviewNote(Base):
    __tablename__ = "knowledge_review_notes"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    citation_ref: Mapped[str] = mapped_column(String(80), index=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30))
    reviewer_name: Mapped[str] = mapped_column(String(200))
    feedback: Mapped[str] = mapped_column(Text)
    attachment_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attachment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("staff.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
