"""Verify external review receipts against exact KB content.

Offline integration boundary only. Does not change the live v2 pipeline or
interpret a clinical scoring policy. Trust keys must be supplied by the
deployment owner after verifying the reviewer's identity and authority.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
from pathlib import Path
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field

from app.services.knowledge_release import review_manifest
from app.services.knowledge_v3 import DEFAULT_V3_DIR


class ReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    citation_ref: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    clinical: Literal["approved", "excluded"]
    translation: Literal["approved", "excluded"]
    rationale: str = Field(min_length=1)


class ReviewReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    schema_version: Literal["1.0"]
    release_id: str
    release_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str = Field(min_length=1)
    reviewer_credentials: str = Field(min_length=1)
    reviewed_on: dt.date
    review_document: str = Field(min_length=1)
    scoring_policy_document: str = Field(min_length=1)
    r14_decision_document: str = Field(min_length=1)
    legacy_decisions: dict[str, str]
    entries: list[ReviewItem] = Field(min_length=1)


def signing_bytes(receipt: ReviewReceipt) -> bytes:
    return json.dumps(receipt.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def verify_approved_subset(
    receipt_data: dict,
    *,
    signature_base64: str,
    key_id: str,
    trusted_keys: dict[str, bytes],
    directory: Path = DEFAULT_V3_DIR,
    today: dt.date | None = None,
) -> dict:
    """Return reviewed snapshots only; zero auto-grading or activation.

    A signature authenticates the configured key, not medical correctness.
    Clinical validation and implementation of the named scoring policy are
    independent release gates even after this function succeeds.
    """
    if key_id not in trusted_keys:
        raise ValueError("Reviewer key is not trusted")
    receipt = ReviewReceipt.model_validate(receipt_data)
    try:
        signature = base64.b64decode(signature_base64, validate=True)
        Ed25519PublicKey.from_public_bytes(trusted_keys[key_id]).verify(signature, signing_bytes(receipt))
    except (ValueError, InvalidSignature) as exc:
        raise ValueError("Invalid review signature") from exc
    if receipt.reviewed_on > (today or dt.date.today()):
        raise ValueError("Review date is in the future")
    manifest = review_manifest(directory)
    if receipt.release_id != manifest["release_id"] or receipt.release_sha256 != manifest["content_sha256"]:
        raise ValueError("Review does not match this release content")
    required = set(manifest["blockers"]["legacy_specific_review"])
    if set(receipt.legacy_decisions) != required or any(not text.strip() for text in receipt.legacy_decisions.values()):
        raise ValueError("All specific legacy reviews need explicit decisions")
    by_ref = {item["citation_ref"]: item for item in manifest["entries"]}
    seen = set()
    selected = []
    for decision in receipt.entries:
        if decision.citation_ref in seen:
            raise ValueError("Duplicate review decision")
        seen.add(decision.citation_ref)
        item = by_ref.get(decision.citation_ref)
        if item is None or item["content_sha256"] != decision.content_sha256:
            raise ValueError("Entry review is stale or unknown")
        if decision.clinical == "approved" and decision.translation == "approved":
            selected.append(item)
    if not selected:
        raise ValueError("No jointly approved clinical and translation content")
    return {
        "release_id": manifest["release_id"],
        "release_sha256": manifest["content_sha256"],
        "reviewer_key_id": key_id,
        "review_document": receipt.review_document,
        "scoring_policy_document": receipt.scoring_policy_document,
        "entries": selected,
        "runtime_enabled": False,
        "remaining_gates": ["Implement and validate approved scoring policy", "Expert-labelled regression evaluation", "Explicit deployment approval"],
    }
