"""KB review workflow. A 'reviewed' note is NOT clinical approval."""
import datetime as dt
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.api.deps import CurrentStaff, get_current_admin_staff, get_db
from app.core.envelope import envelope
from app.models.knowledge_review import KnowledgeReviewNote
from app.services.audit import AuditService
from app.services.knowledge_release import review_manifest

router = APIRouter(prefix="/admin/knowledge-review", tags=["admin"])


class ReviewWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_note_id: int = Field(ge=0)
    status: Literal["pending", "changes_requested", "reviewed"]
    reviewer_name: str = Field(min_length=1, max_length=200)
    feedback: str = Field(min_length=1, max_length=10000)
    attachment_name: str | None = Field(default=None, max_length=200)
    attachment_text: str | None = Field(default=None, max_length=32000)

    @model_validator(mode="after")
    def attachment_pair(self):
        if bool(self.attachment_name) != bool(self.attachment_text):
            raise ValueError("Provide both attachment name and text")
        if self.attachment_name and (not self.attachment_name.lower().endswith(".txt") or any(c in self.attachment_name for c in "/\\\x00")):
            raise ValueError("Only plain-text .txt attachments are supported")
        return self


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    citation_ref: str
    content_sha256: str
    status: str
    reviewer_name: str
    feedback: str
    attachment_name: str | None
    attachment_text: str | None
    recorded_by: uuid.UUID
    created_at: dt.datetime


def catalog():
    try:
        return review_manifest()
    except (ValueError, OSError):
        raise HTTPException(status_code=503, detail="Review knowledge base is unavailable")


@router.get("")
def entries(admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    manifest = catalog()
    notes = db.execute(select(KnowledgeReviewNote).distinct(KnowledgeReviewNote.citation_ref).order_by(KnowledgeReviewNote.citation_ref, KnowledgeReviewNote.id.desc())).scalars().all()
    latest = {note.citation_ref: note for note in notes}
    items = []
    for item in manifest["entries"]:
        note = latest.get(item["citation_ref"])
        current = note is not None and note.content_sha256 == item["content_sha256"]
        items.append({**item, "workflow_status": note.status if current else "pending", "feedback_stale": bool(note and not current), "latest_note_id": note.id if note else 0})
    return envelope({"release_id": manifest["release_id"], "runtime_enabled": False, "items": items})


@router.get("/{citation_ref}/notes")
def notes(citation_ref: str, admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    if citation_ref not in {item["citation_ref"] for item in catalog()["entries"]}:
        raise HTTPException(status_code=404, detail="Unknown knowledge-base entry")
    rows = db.execute(select(KnowledgeReviewNote).where(KnowledgeReviewNote.citation_ref == citation_ref).order_by(KnowledgeReviewNote.id.desc()).limit(20)).scalars().all()
    return envelope([ReviewRead.model_validate(row).model_dump(mode="json") for row in rows])


@router.post("/{citation_ref}/notes", status_code=201)
def save_note(citation_ref: str, payload: ReviewWrite, admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    item = next((item for item in catalog()["entries"] if item["citation_ref"] == citation_ref), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown knowledge-base entry")
    if item["content_sha256"] != payload.content_sha256:
        raise HTTPException(status_code=409, detail="Evidence has changed; reload before recording a review")
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:ref))"), {"ref": "kb-review:" + citation_ref})
    latest = db.execute(select(KnowledgeReviewNote.id).where(KnowledgeReviewNote.citation_ref == citation_ref).order_by(KnowledgeReviewNote.id.desc()).limit(1)).scalar_one_or_none()
    if (latest or 0) != payload.expected_note_id:
        raise HTTPException(status_code=409, detail="Another review was saved; reload before submitting")
    note = KnowledgeReviewNote(citation_ref=citation_ref, recorded_by=admin.staff_id, **payload.model_dump(exclude={"expected_note_id"}))
    db.add(note)
    db.flush()
    AuditService(db).append(actor_id=str(admin.staff_id), action="knowledge_review.record", resource_type="knowledge_review_note", resource_id=str(note.id), institution_id=str(admin.institution_id))
    return envelope(ReviewRead.model_validate(note).model_dump(mode="json"))
