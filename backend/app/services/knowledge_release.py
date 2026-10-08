"""Content-addressed review manifest. Never authorizes clinical activation.

Fingerprints bind a review to exact entry and source metadata, not just a
mutable release name. They detect changes; they are not digital signatures.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.services.knowledge_v3 import DEFAULT_V3_DIR, _json, load_review_bundle


def fingerprint(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def review_manifest(directory: Path = DEFAULT_V3_DIR) -> dict:
    bundle, sources = load_review_bundle(directory)
    source_map = {source.source_id: source.model_dump(mode="json") for source in sources}
    mappings = _json(directory / "legacy_mapping.json")
    entries = []
    for row in sorted(bundle.rows, key=lambda item: item.citation_ref):
        snapshot = {
            "entry": row.model_dump(mode="json"),
            "sources": [source_map[source_id] for source_id in sorted(row.source_ids)],
        }
        entries.append({
            "citation_ref": row.citation_ref,
            "content_sha256": fingerprint(snapshot),
            "review_status": row.review_status,
            "translation_status": row.translation_status,
            "snapshot": snapshot,
        })
    payload = {
        "bundle": bundle.model_dump(mode="json"),
        "sources": sorted(source_map.values(), key=lambda source: source["source_id"]),
        "legacy_mapping": sorted(mappings, key=lambda item: item["legacy_ref"]),
    }
    return {
        "manifest_schema": "1.0",
        "release_id": bundle.release_id,
        "content_sha256": fingerprint(payload),
        "runtime_enabled": False,
        "ready_for_activation": False,
        "blockers": {
            "clinical_review": [row["citation_ref"] for row in entries],
            "translation_review": [row["citation_ref"] for row in entries],
            "legacy_specific_review": sorted(item["legacy_ref"] for item in mappings if item["disposition"] == "needs_specific_review"),
            "clinical_grading_decision": ["R14"],
            "runtime_and_evaluation": ["Version-aware runtime integration", "Expert-labelled evaluation", "Approved subset activation policy"],
        },
        "entries": entries,
    }


def compare_manifests(left: dict, right: dict) -> dict:
    """Content diff; old snapshots remain untouched."""
    a = {x["citation_ref"]: x["content_sha256"] for x in left.get("entries", [])}
    b = {x["citation_ref"]: x["content_sha256"] for x in right.get("entries", [])}
    return {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
            "from_release": left.get("release_id"), "to_release": right.get("release_id")}
