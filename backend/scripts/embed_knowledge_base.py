"""Compute pgvector embeddings for the knowledge base (ADR-11).

Usage (from backend/, with .env DATABASE_URL and EMBEDDING_* set):
    .venv\Scripts\python.exe scripts\embed_knowledge_base.py
    .venv\Scripts\python.exe scripts\embed_knowledge_base.py --force

Idempotent: only rows whose description hash or embedding model changed are
re-embedded. Runs under the privileged DATABASE_URL role (signal_app is
SELECT-only on milestones). Optional — the default RETRIEVAL_MODE=full_context
never reads embeddings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.milestone import Milestone
from app.services.embeddings import EmbeddingError, embedding_hash, embedding_text, get_embedder

BATCH = 32


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed the SIGNAL knowledge base")
    parser.add_argument("--force", action="store_true", help="re-embed every row")
    args = parser.parse_args()

    settings = get_settings()
    embedder = get_embedder(settings)
    if embedder is None:
        print("EMBEDDING_BASE_URL / EMBEDDING_MODEL / EMBEDDING_API_KEY are not all set.")
        return 2

    engine = create_engine(settings.DATABASE_URL)
    done = 0
    with Session(engine) as db:
        rows = db.execute(select(Milestone).order_by(Milestone.citation_ref)).scalars().all()
        stale = [
            r
            for r in rows
            if args.force
            or r.embedding_model != embedder.model
            or r.embedding_hash != embedding_hash(embedding_text(r.description))
        ]
        for start in range(0, len(stale), BATCH):
            chunk = stale[start : start + BATCH]
            texts = [embedding_text(r.description) for r in chunk]
            try:
                vectors = embedder.embed(texts)
            except EmbeddingError as exc:
                print(f"Embedding failed after {done} rows: {exc}")
                db.rollback()
                return 1
            for row, text, vector in zip(chunk, texts, vectors, strict=True):
                row.embedding = vector
                row.embedding_model = embedder.model
                row.embedding_hash = embedding_hash(text)
            done += len(chunk)
        db.commit()
    print(f"Embedded {done} of {len(rows)} rows with {embedder.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
