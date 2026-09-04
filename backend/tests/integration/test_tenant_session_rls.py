"""Row-level security is ACTIVE on the tenant session (audit finding F1).

`test_postgres_rls.py` already proved the policies work when a connection
opts into them. It did not prove the application uses such a connection —
and it did not, because `DATABASE_URL` pointed at a superuser role carrying
`BYPASSRLS`, which bypasses RLS even where `FORCE ROW LEVEL SECURITY` is set.
Every table-level guarantee in migration 0001 was therefore inert at runtime,
and tenant isolation rested entirely on each handler remembering its
`WHERE institution_id = ...`.

These tests pin the fix from the other direction: they run queries with NO
application-level filter at all and assert the database still refuses to
return another institution's rows. If someone points the tenant path back at
a privileged role, these fail.
"""

from __future__ import annotations

import datetime
import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

TENANT_ROLE_URL_ENV = "SIGNAL_TEST_TENANT_DATABASE_URL"


@pytest.fixture()
def tenant_engine(pg_engine):
    """An engine on the SAME test database, connected as `signal_app`.

    `signal_app` is created by migration 0001 with password 'signal_app' and
    is deliberately not a superuser.
    """
    url = pg_engine.url.set(username="signal_app", password="signal_app")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
            ).one()
        assert row.rolsuper is False, "tenant role must not be a superuser"
        assert row.rolbypassrls is False, "tenant role must not carry BYPASSRLS"
    except Exception as exc:  # pragma: no cover - environment guard
        engine.dispose()
        pytest.skip(f"signal_app role unavailable on the test database: {exc}")
    yield engine
    engine.dispose()


def _seed_two_institutions(pg_engine) -> tuple[uuid.UUID, uuid.UUID]:
    """Two institutions, one child each, written with the privileged role."""
    from app.models.child import Child
    from app.models.institution import Institution

    ids = []
    with Session(pg_engine) as session:
        for label in ("RLS Tenant A", "RLS Tenant B"):
            inst = Institution(name=f"{label} {uuid.uuid4().hex[:6]}", is_synthetic=True)
            session.add(inst)
            session.flush()
            session.add(
                Child(
                    id=uuid.uuid4(),
                    institution_id=inst.id,
                    name=f"Child of {label}",
                    intake_date=datetime.date(2026, 8, 1),
                    dob_confirmed=True,
                    dob=datetime.date(2024, 1, 1),
                    is_synthetic=True,
                )
            )
            ids.append(inst.id)
        session.commit()
    return ids[0], ids[1]


def _scoped(session: Session, institution_id: uuid.UUID) -> None:
    """Exactly what get_tenant_db does — transaction-local, not session-level."""
    session.execute(
        text("SELECT set_config('app.institution_id', :iid, true)"),
        {"iid": str(institution_id)},
    )


def test_unfiltered_query_returns_only_the_scoped_institution(pg_engine, tenant_engine):
    """The point of the whole exercise: no WHERE clause, still isolated."""
    inst_a, inst_b = _seed_two_institutions(pg_engine)

    with Session(tenant_engine) as session:
        _scoped(session, inst_a)
        rows = session.execute(text("SELECT institution_id FROM children")).scalars().all()

    assert rows, "scoped session should see its own institution's children"
    assert set(rows) == {inst_a}, "an unfiltered read leaked another institution"
    assert inst_b not in rows


def test_no_scope_set_returns_nothing(pg_engine, tenant_engine):
    """Fail-closed: a missing setting must show zero rows, not all rows.
    NULL never compares equal, which is what makes the policy safe by default.
    """
    _seed_two_institutions(pg_engine)

    with Session(tenant_engine) as session:
        rows = session.execute(text("SELECT id FROM children")).scalars().all()

    assert rows == []


def test_scope_does_not_survive_the_transaction(pg_engine, tenant_engine):
    """`set_config(..., true)` is transaction-local on purpose.

    A session-level setting would persist on a POOLED connection into
    whichever request borrowed it next — the exact cross-tenant leak this
    layer exists to stop. This test fails if someone flips that flag.
    """
    inst_a, _ = _seed_two_institutions(pg_engine)

    with Session(tenant_engine) as session:
        _scoped(session, inst_a)
        assert session.execute(text("SELECT count(*) FROM children")).scalar_one() > 0
        session.commit()  # transaction ends — scope must end with it

        leaked = session.execute(
            text("SELECT current_setting('app.institution_id', true)")
        ).scalar_one()
        assert leaked in (None, ""), f"scope leaked past the transaction: {leaked!r}"


def test_tenant_role_cannot_rewrite_the_audit_log(tenant_engine):
    """Append-only is a GRANT, and grants only bind a non-superuser role.
    Under the old privileged connection this protection was inert too.
    """
    with Session(tenant_engine) as session:
        with pytest.raises(Exception) as excinfo:
            session.execute(text("UPDATE audit_log SET action = 'tampered'"))
        assert "permission denied" in str(excinfo.value).lower()
        session.rollback()

        with pytest.raises(Exception) as excinfo:
            session.execute(text("DELETE FROM audit_log"))
        assert "permission denied" in str(excinfo.value).lower()
        session.rollback()


def test_tenant_role_cannot_delete_children(tenant_engine):
    """No DELETE grant anywhere on tenant data — retention is a decision, not
    something a bug can make for you.
    """
    with Session(tenant_engine) as session:
        with pytest.raises(Exception) as excinfo:
            session.execute(text("DELETE FROM children"))
        assert "permission denied" in str(excinfo.value).lower()
        session.rollback()


@pytest.mark.skipif(
    os.environ.get(TENANT_ROLE_URL_ENV) is None,
    reason="set SIGNAL_TEST_TENANT_DATABASE_URL to check the deployed tenant URL",
)
def test_configured_tenant_url_is_not_privileged():
    """Guards the deployment itself, not just the test fixture."""
    engine = create_engine(os.environ[TENANT_ROLE_URL_ENV])
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
            ).one()
        assert row.rolsuper is False and row.rolbypassrls is False
    finally:
        engine.dispose()
