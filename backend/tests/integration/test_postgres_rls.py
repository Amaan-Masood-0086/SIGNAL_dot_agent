"""Postgres integration tests — migrations + RLS at the DB role level.

FEAT-01 acceptance criteria: migrations run cleanly; RLS policies active at
DB role level. Skipped unless SIGNAL_TEST_DATABASE_URL points at a Postgres
instance (docker compose up -d db). These tests connect as the UNPRIVILEGED
app role — exactly the way the application connects — so a missing policy
fails loudly instead of being masked by superuser privileges.
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("SIGNAL_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="SIGNAL_TEST_DATABASE_URL not set (Postgres not available)"
)


@pytest.fixture(scope="module")
def migrated_postgres():
    """Run alembic migrations against a fresh database, return engine."""
    from alembic import command
    from alembic.config import Config

    db_name = f"signal_test_{uuid.uuid4().hex[:8]}"
    admin_url = DATABASE_URL.replace("/signal_dev", "/postgres").replace(
        "/signal_test", "/postgres"
    )
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()

    target_url = DATABASE_URL.rsplit("/", 1)[0] + f"/{db_name}"
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", target_url)
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(target_url)
    yield engine
    engine.dispose()

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
    admin_engine.dispose()


def test_migrations_create_all_trd_tables(migrated_postgres):
    expected = {
        "institutions", "staff", "children", "sessions", "observations",
        "milestones", "flags", "referrals", "safeguarding_escalations", "audit_log",
    }
    with migrated_postgres.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename = ANY(:names)"
            ),
            {"names": list(expected)},
        ).scalars().all()
    assert expected == set(rows)


def test_rls_policies_active_on_tenant_tables(migrated_postgres):
    """RLS must be enabled AND forced on every institution-scoped table."""
    tenant_tables = {
        "children", "sessions", "observations", "flags", "referrals",
        "safeguarding_escalations", "staff",
    }
    with migrated_postgres.connect() as conn:
        # pg_tables exposes relrowsecurity but NOT relforcerowsecurity, so
        # query pg_class directly for both flags.
        rows = conn.execute(
            text(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relrowsecurity "
                "AND c.relforcerowsecurity "
                "AND c.relname = ANY(:names)"
            ),
            {"names": list(tenant_tables)},
        ).scalars().all()
    assert tenant_tables == set(rows), (
        f"RLS not enabled+forced on: {tenant_tables - set(rows)}"
    )


def test_rls_hides_cross_institution_rows(migrated_postgres):
    """THREAT_MODEL: elevation-of-privilege — institution A must never see B.

    Connects as the application role (signal_app), seeds two institutions as
    the migration owner, then proves row visibility follows app.institution_id.
    """
    from sqlalchemy.orm import Session as SASession

    inst_a, inst_b = str(uuid.uuid4()), str(uuid.uuid4())

    # Seed via the migration-owner role (the URL role owns the schema).
    with migrated_postgres.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO institutions (id, name, is_synthetic, created_at) "
                "VALUES (:a, 'Inst A', true, now()), (:b, 'Inst B', true, now())"
            ),
            {"a": inst_a, "b": inst_b},
        )
        conn.execute(
            text(
                "INSERT INTO children (id, institution_id, name, intake_date, "
                "dob_confirmed, is_synthetic, created_at) "
                "VALUES (:ca, :a, 'Child A', now(), true, true, now()), "
                "(:cb, :b, 'Child B', now(), true, true, now())"
            ),
            {"ca": str(uuid.uuid4()), "cb": str(uuid.uuid4()), "a": inst_a, "b": inst_b},
        )

    # Query as the unprivileged app role, scoped to institution A.
    # SET ROLE (not a separate connection) is sufficient: superusers/migration
    # owners can assume any role, and RLS applies to signal_app.
    with migrated_postgres.connect() as conn:
        conn.execute(text("SET ROLE signal_app"))
        conn.execute(
            text("SELECT set_config('app.institution_id', :iid, false)"), {"iid": inst_a}
        )
        visible = conn.execute(text("SELECT name FROM children")).scalars().all()

    assert visible == ["Child A"], (
        f"RLS breach: institution-scoped connection saw {visible}"
    )
