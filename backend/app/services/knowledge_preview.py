"""Deterministic, read-only V3 sandbox. It can suggest evidence to inspect; it never grades."""
from __future__ import annotations

import re
from pathlib import Path
from app.services.knowledge_release import review_manifest
from app.services.knowledge_v3 import DEFAULT_V3_DIR, Entry, age_eligibility

_STOP = {"the", "and", "is", "a", "an", "to", "of", "for", "in", "on", "with", "my", "child", "does"}


def preview(observation: str, age_lower_months: float, age_upper_months: float,
            domain: str | None = None, directory: Path = DEFAULT_V3_DIR) -> dict:
    manifest = review_manifest(directory)
    query = {t for t in re.findall(r"[a-z0-9]+", observation.lower()) if t not in _STOP and len(t) > 2}
    candidates = []
    for item in manifest["entries"]:
        entry = item["snapshot"]["entry"]
        if domain and entry["domain"] != domain:
            continue
        age = age_eligibility(Entry.model_validate(entry), age_lower_months, age_upper_months)
        if age == "outside_age_scope":
            continue
        text = " ".join([entry["observation"], entry["interpretation_notes"]]).lower()
        tokens = set(re.findall(r"[a-z0-9]+", text))
        overlap = len(query & tokens)
        if overlap or not query:
            candidates.append({"citation_ref": item["citation_ref"], "domain": entry["domain"], "age_status": age,
                "match_tokens": overlap, "observation": entry["observation"], "follow_up_en": entry["follow_up_en"],
                "follow_up_ur_latn": entry["follow_up_ur_latn"], "action": entry["action"],
                "evidence_group": entry["evidence_group"], "sources": item["snapshot"]["sources"],
                "clinical_grade": None, "review_status": entry["review_status"]})
    candidates.sort(key=lambda x: (-x["match_tokens"], x["citation_ref"]))
    return {"mode": "preview", "preview_only": True, "runtime_enabled": False, "clinical_grade": None,
            "candidates": candidates[:20], "caveats": ["Synthetic review aid only; no diagnosis or clinical grade.",
                "Candidates require expert review and do not write sessions or history."]}
