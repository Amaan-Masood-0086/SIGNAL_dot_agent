from __future__ import annotations

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeRelease(Base):
    """Immutable content-addressed snapshot of a review KB manifest."""
    __tablename__ = "knowledge_releases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    release_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="research_draft")
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
