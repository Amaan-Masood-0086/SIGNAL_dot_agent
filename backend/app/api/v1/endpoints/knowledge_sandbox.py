from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.api.deps import CurrentStaff, get_current_admin_staff, get_db
from app.core.envelope import envelope
from app.models.knowledge_release import KnowledgeRelease
from app.services.knowledge_preview import preview
from app.services.knowledge_release import review_manifest, compare_manifests
from app.services.knowledge_v3 import Domain
from app.services.audit import AuditService
from app.services.knowledge_storage import store_revisions
import json

router = APIRouter(prefix="/admin/knowledge", tags=["admin"])

class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    observation: str = Field(min_length=1, max_length=2000)
    age_lower_months: float = Field(ge=0, le=216)
    age_upper_months: float = Field(ge=0, le=216)
    domain: Domain | None = None

    def model_post_init(self, __context):
        if self.age_lower_months > self.age_upper_months:
            raise ValueError("Age interval is reversed")

@router.get("/releases")
def releases(admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    rows = db.execute(select(KnowledgeRelease).order_by(KnowledgeRelease.id.desc()).limit(50)).scalars().all()
    return envelope({"current_draft": review_manifest(), "releases": [{"id": r.id, "release_id": r.release_id, "content_sha256": r.content_sha256, "status": r.status, "created_at": r.created_at} for r in rows]})

@router.post("/releases", status_code=201)
def capture_release(admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    manifest = review_manifest()
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "kb-capture:" + manifest["content_sha256"]})
    existing = db.execute(select(KnowledgeRelease).where(KnowledgeRelease.content_sha256 == manifest["content_sha256"])).scalar_one_or_none()
    if existing:
        store_revisions(db, existing.id, json.loads(existing.manifest_json))
        return envelope({"id": existing.id, "release_id": existing.release_id, "content_sha256": existing.content_sha256, "existing": True})
    row = KnowledgeRelease(release_id=manifest["release_id"], content_sha256=manifest["content_sha256"], status="research_draft", manifest_json=json.dumps(manifest, sort_keys=True), created_by=str(admin.staff_id))
    db.add(row); db.flush()
    store_revisions(db, row.id, manifest)
    AuditService(db).append(actor_id=str(admin.staff_id), action="knowledge_release.capture", resource_type="knowledge_release", resource_id=str(row.id), institution_id=str(admin.institution_id))
    return envelope({"id": row.id, "release_id": row.release_id, "content_sha256": row.content_sha256, "existing": False})

@router.post("/preview")
def sandbox(payload: PreviewRequest, admin: CurrentStaff = Depends(get_current_admin_staff)):
    return envelope(preview(payload.observation, payload.age_lower_months, payload.age_upper_months, payload.domain))

@router.get("/releases/compare")
def compare(from_id: int, to_id: int, admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    rows = db.execute(select(KnowledgeRelease).where(KnowledgeRelease.id.in_([from_id, to_id]))).scalars().all()
    by_id = {r.id: r for r in rows}
    if from_id not in by_id or to_id not in by_id:
        raise HTTPException(status_code=404, detail="Release snapshot not found")
    return envelope(compare_manifests(json.loads(by_id[from_id].manifest_json), json.loads(by_id[to_id].manifest_json)))

@router.post("/releases/{release_id}/rollback")
def rollback(release_id: int, admin: CurrentStaff = Depends(get_current_admin_staff), db: Session = Depends(get_db)):
    row = db.get(KnowledgeRelease, release_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Release snapshot not found")
    # Rollback is deliberately a plan: immutable snapshots are never mutated
    # and no unreviewed content is activated by this endpoint.
    return envelope({"rollback_plan": {"source_release_id": row.id, "release_id": row.release_id,
        "content_sha256": row.content_sha256, "status": "rollback_candidate", "runtime_enabled": False},
        "message": "Snapshot selected for review; activation requires separate clinical approval."})
