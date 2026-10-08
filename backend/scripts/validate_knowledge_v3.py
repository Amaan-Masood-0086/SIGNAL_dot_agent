"""Read-only v3 validation / age-preview command; no keys or database needed."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.knowledge_v3 import DEFAULT_V3_DIR, age_eligibility, load_review_bundle, summary
from app.services.knowledge_release import review_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_V3_DIR)
    parser.add_argument("--age-months", type=float, help="Review preview only; not a clinical result")
    parser.add_argument("--review-manifest", action="store_true", help="Print content fingerprints, evidence snapshots and outstanding review gates; never activates a release")
    args = parser.parse_args()
    try:
        bundle, sources = load_review_bundle(args.directory)
        result = summary(bundle, sources)
        if args.review_manifest:
            result["review_manifest"] = review_manifest(args.directory)
        if args.age_months is not None:
            result["age_preview"] = [
                r.citation_ref for r in bundle.rows
                if age_eligibility(r, args.age_months, args.age_months) == "eligible_for_review"
            ]
            result["preview_note"] = "Assumes supplied age applies to each row; no skill absence or grade inferred."
        print(json.dumps(result, indent=2, ensure_ascii=True))
    except (OSError, ValueError) as exc:
        print(f"Knowledge-base validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
