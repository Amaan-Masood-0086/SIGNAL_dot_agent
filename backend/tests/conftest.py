"""Shared fixtures for SIGNAL backend tests.

FEAT-01 scope: skeleton + schema + auth stub + synthetic gate + audit chain.

MANDATORY (FEAT-01 acceptance): ALL tests run against real PostgreSQL —
never SQLite. Row-Level Security and the migration-created role/grant
structure cannot be validated on SQLite. Schema is applied exclusively via
the Alembic migration (single source of truth), not metadata.create_all.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def rsa_keypair() -> tuple[bytes, bytes]:
    """Throwaway RS256 keypair — JWT signing is RS256 per sdlc-security.md."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


@pytest.fixture(scope="session")
def pg_engine():
    """Fresh PostgreSQL database migrated to head; dropped on teardown.

    Fails loudly when no Postgres URL is configured — SQLite is never a
    fallback for SIGNAL tests.
    """
    admin_url = os.environ.get("SIGNAL_TEST_DATABASE_URL")
    if not admin_url:
        pytest.fail(
            "SIGNAL_TEST_DATABASE_URL must point at a PostgreSQL instance "
            "(docker compose up -d db). SIGNAL tests never run on SQLite: "
            "Row-Level Security is a FEAT-01 acceptance criterion and is "
            "Postgres-only."
        )

    from alembic import command
    from alembic.config import Config

    db_name = f"signal_unit_{uuid.uuid4().hex[:8]}"
    root_url = admin_url.replace("/signal_dev", "/postgres").replace(
        "/signal_test", "/postgres"
    )
    admin_engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()

    target_url = admin_url.rsplit("/", 1)[0] + f"/{db_name}"
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", target_url)
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(target_url)
    yield engine
    engine.dispose()

    admin_engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        # Terminate stragglers so DROP DATABASE cannot fail on teardown.
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :db AND pid <> pg_backend_pid()"
            ),
            {"db": db_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
    admin_engine.dispose()


@pytest.fixture()
def db_session(pg_engine):
    """Session bound to a per-test transaction, rolled back on teardown.

    Tests may commit (audit-chain tests do); the outer engine-level
    transaction still rolls everything back, keeping tests isolated.
    """
    connection = pg_engine.connect()
    outer = connection.begin()
    testing_session = Session(bind=connection, expire_on_commit=False)
    yield testing_session
    testing_session.close()
    if outer.is_active:
        outer.rollback()
    connection.close()
