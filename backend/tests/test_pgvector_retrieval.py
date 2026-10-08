"""ADR-11 — pgvector semantic retrieval is additive and fails toward MORE context.

Real PostgreSQL with the vector extension (conftest.py::pg_engine, Alembic head).
No network: embedders are deterministic fakes; the HTTP embedder is exercised
through a monkeypatched httpx.post.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from app.db.vector import EMBEDDING_DIMENSIONS
from app.models.milestone import Milestone
from app.services.embeddings import (
    EmbeddingError,
    OpenAICompatibleEmbedder,
    embedding_hash,
    embedding_text,
    get_embedder,
)
from app.services.knowledge import (
    load_knowledge_base,
    retrieve_for_prompt,
    retrieve_in_scope_entries,
)

CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / ".ai" / "brain" / "knowledge-base-source" / "signal_knowledge_base_v2.csv"
)
AGE = 24


def _vec(text: str) -> list[float]:
    v = [0.0] * EMBEDDING_DIMENSIONS
    lowered = text.lower()
    v[0 if ("hear" in lowered or "sound" in lowered or "ear" in lowered) else 1] = 1.0
    return v


class FakeEmbedder:
    model = "fake-1024"

    def embed(self, texts):
        return [_vec(t) for t in texts]


class BrokenEmbedder:
    model = "broken"

    def embed(self, texts):
        raise EmbeddingError("provider down")


@pytest.fixture()
def embedded_db(db_session):
    load_knowledge_base(db_session, csv_path=CSV_PATH)
    for row in db_session.execute(select(Milestone)).scalars():
        text = embedding_text(row.description)
        row.embedding = _vec(text)
        row.embedding_model = FakeEmbedder.model
        row.embedding_hash = embedding_hash(text)
    db_session.flush()
    return db_session


def _refs(rows):
    return [r.citation_ref for r in rows]


def _retrieve(db, mode, embedder, query="he does not hear when called", k=2):
    return retrieve_for_prompt(
        db, AGE, query_text=query, mode=mode, embedder=embedder, top_k_per_domain=k
    )


def test_vector_column_round_trips_and_orders_by_cosine_distance(embedded_db):
    query = _vec("hearing")
    distance = Milestone.embedding.cosine_distance(query).label("dist")
    nearest = embedded_db.execute(
        select(Milestone.citation_ref, distance).order_by(distance).limit(1)
    ).one()
    assert nearest.dist == pytest.approx(0.0)
    row = embedded_db.execute(
        select(Milestone).where(Milestone.citation_ref == nearest.citation_ref)
    ).scalar_one()
    assert len(row.embedding) == EMBEDDING_DIMENSIONS


def test_default_mode_is_byte_for_byte_the_full_context_set(embedded_db):
    full = retrieve_in_scope_entries(embedded_db, AGE)
    assert _refs(_retrieve(embedded_db, "full_context", FakeEmbedder())) == _refs(full)


def test_semantic_mode_narrows_but_keeps_high_red_flags_and_both_domains(embedded_db):
    full = retrieve_in_scope_entries(embedded_db, AGE)
    narrowed = _retrieve(embedded_db, "semantic", FakeEmbedder(), k=2)
    assert len(narrowed) < len(full)
    narrowed_refs = set(_refs(narrowed))
    high = {m.citation_ref for m in full if m.entry_type == "red_flag" and m.severity == "HIGH"}
    assert high <= narrowed_refs
    assert {m.domain for m in narrowed} == {m.domain for m in full}
    assert _refs(narrowed) == [r for r in _refs(full) if r in narrowed_refs]


@pytest.mark.parametrize("embedder", [None, BrokenEmbedder()])
def test_unavailable_embedder_falls_back_to_full_context(embedded_db, embedder):
    full = _refs(retrieve_in_scope_entries(embedded_db, AGE))
    assert _refs(_retrieve(embedded_db, "semantic", embedder)) == full


def test_blank_query_falls_back_to_full_context(embedded_db):
    full = _refs(retrieve_in_scope_entries(embedded_db, AGE))
    assert _refs(_retrieve(embedded_db, "semantic", FakeEmbedder(), query="   ")) == full


def test_missing_embedding_on_any_in_window_row_falls_back_to_full_context(embedded_db):
    full = retrieve_in_scope_entries(embedded_db, AGE)
    victim = embedded_db.execute(
        select(Milestone).where(Milestone.citation_ref == full[0].citation_ref)
    ).scalar_one()
    victim.embedding = None
    embedded_db.flush()
    assert _refs(_retrieve(embedded_db, "semantic", FakeEmbedder())) == _refs(full)


def test_get_embedder_is_none_until_fully_configured():
    from app.core.config import Settings

    base = dict(ENVIRONMENT="synthetic_only")
    assert get_embedder(Settings(**base)) is None
    assert get_embedder(Settings(**base, EMBEDDING_BASE_URL="http://x", EMBEDDING_MODEL="m")) is None
    assert get_embedder(
        Settings(**base, EMBEDDING_BASE_URL="http://x", EMBEDDING_MODEL="m", EMBEDDING_API_KEY="k")
    ) is not None


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._p


def _embedder():
    return OpenAICompatibleEmbedder(base_url="http://x/v1", model="m", api_key="k", timeout=1)


def test_http_embedder_orders_by_index_and_sends_bearer(monkeypatch):
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers)
        return _Resp({"data": [
            {"index": 1, "embedding": [0.0] * EMBEDDING_DIMENSIONS},
            {"index": 0, "embedding": [1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 1)},
        ]})

    monkeypatch.setattr("app.services.embeddings.httpx.post", fake_post)
    out = _embedder().embed(["a", "b"])
    assert out[0][0] == 1.0 and out[1][0] == 0.0
    assert seen["url"] == "http://x/v1/embeddings"
    assert seen["headers"]["Authorization"] == "Bearer k"


@pytest.mark.parametrize(
    "payload",
    [
        {"data": [{"index": 0, "embedding": [0.1, 0.2]}]},
        {"data": []},
        {"unexpected": True},
    ],
)
def test_http_embedder_rejects_malformed_responses(monkeypatch, payload):
    monkeypatch.setattr("app.services.embeddings.httpx.post", lambda *a, **k: _Resp(payload))
    with pytest.raises(EmbeddingError):
        _embedder().embed(["a"])
