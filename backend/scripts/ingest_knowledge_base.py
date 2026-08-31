"""Ingest signal_knowledge_base_v2.csv into the milestones table (FEAT-04).

Usage (from backend/, with .env DATABASE_URL set):
    .venv\\Scripts\\python.exe scripts\\ingest_knowledge_base.py
    .venv\\Scripts\\python.exe scripts\\ingest_knowledge_base.py --csv path\\to.csv

Idempotent by design (upsert on citation_ref, ADR-08) — run it as often as
the dataset is corrected. Runs under the DATABASE_URL role: the unprivileged
signal_app role has SELECT-only on milestones (FEAT-01), so ingestion needs
the privileged role.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.knowledge import DEFAULT_CSV_PATH, load_knowledge_base


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the SIGNAL knowledge base")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    args = parser.parse_args()

    engine = create_engine(get_settings().DATABASE_URL)
    with Session(engine) as db:
        result = load_knowledge_base(db, csv_path=args.csv)
        db.commit()
    print(
        f"Knowledge base loaded: {result.inserted} inserted, "
        f"{result.updated} updated, {result.total} total rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
