"""Minimal pgvector column type (ADR-11).

An in-repo type rather than the `pgvector` + `numpy` packages: the app only
ever writes a list of floats and orders by cosine distance, so a ~30-line
type keeps the dependency / supply-chain surface unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.types import UserDefinedType

EMBEDDING_DIMENSIONS = 1024


def to_vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(v)) for v in values) + "]"


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions

    def get_col_spec(self, **kw) -> str:
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect):
        def process(value):
            return None if value is None else to_vector_literal(value)

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return [float(x) for x in str(value).strip("[]").split(",") if x]

        return process

    class comparator_factory(UserDefinedType.Comparator):
        def cosine_distance(self, other: Sequence[float]):
            from sqlalchemy import Float, literal

            return self.op("<=>", return_type=Float)(literal(to_vector_literal(other)).cast(Vector(len(other))))
