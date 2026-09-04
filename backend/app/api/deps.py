"""Auth + database dependencies.

FEAT-01 ships the verified-staff dependency; FEAT-02 adds `get_db`. The
full chain (lockout and token blacklist) lands with real credentials in
FEAT-12. Every business endpoint MUST depend on `get_current_verified_staff`.

RBAC / Admin Panel addition: `get_current_admin_staff`. Per THREAT_MODEL §2
the admin role is a SYSTEM-LEVEL (NextaSol/dev) role, NOT a per-institution
one. Its cross-institution visibility applies ONLY to the explicit admin
endpoints (admin staff management, GET /audit_log, provider status, all-
usage view); it NEVER weakens institution scoping on any caretaker-facing
endpoint — those keep using `get_current_verified_staff` unchanged.

Privilege authority: for the admin chain the DB staff row is the source of
truth for role + active state (a promotion/demotion/deactivation takes
effect immediately, not when the caller's 15-minute token expires). The JWT
remains the signed identity carrier; a JWT "admin" claim over a caretaker
row does not elevate.
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Iterator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import ALLOWED_ROLES, decode_access_token
from app.models.staff import Staff

# auto_error=False so missing/empty tokens return a clean 401 via our handler
# rather than a framework-generated response.
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentStaff(BaseModel):
    """Identity derived ONLY from the signed JWT — never from request body."""

    staff_id: uuid.UUID
    institution_id: uuid.UUID
    role: str


def _verified_claims(
    credentials: HTTPAuthorizationCredentials | None, settings: Settings
) -> dict:
    """JWT verification shared by every dependency in the chain."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token(credentials.credentials, settings=settings)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if claims.get("role") not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    return claims


def get_current_verified_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> CurrentStaff:
    claims = _verified_claims(credentials, settings)
    try:
        return CurrentStaff(
            staff_id=claims["sub"],
            institution_id=claims["institution_id"],
            role=claims["role"],
        )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )


# Engines are cached per URL and pooled. Previously one Engine was created
# and disposed per request, which meant a fresh TCP + auth handshake on every
# call and no pooling at all (audit F8).
_ENGINES: dict[str, Engine] = {}
_ENGINE_LOCK = threading.Lock()


def _engine_for(url: str) -> Engine:
    engine = _ENGINES.get(url)
    if engine is not None:
        return engine
    with _ENGINE_LOCK:
        engine = _ENGINES.get(url)
        if engine is None:
            engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)
            _ENGINES[url] = engine
    return engine


def get_db(settings: Settings = Depends(get_settings)) -> Iterator[Session]:
    """PRIVILEGED request-scoped session — no RLS scoping.

    Reserved for the two places that legitimately cannot be tenant-scoped:
    `/auth/token` (finds a staff row by email before any institution is
    known) and the admin console's documented cross-institution reads.
    Everything caretaker-facing must use `get_tenant_db` instead.
    """
    session = Session(bind=_engine_for(settings.DATABASE_URL), expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Tenant URLs whose connected role has been checked and cannot bypass RLS.
# Verified once per engine rather than once per request: the answer cannot
# change without a DB-side ALTER ROLE, and a `pg_roles` lookup on every
# caretaker request would buy nothing.
_TENANT_ROLE_VERIFIED: set[str] = set()


def _verified_tenant_engine(settings: Settings) -> Engine:
    """The tenant engine — or nothing at all. Fail closed, no escape hatch.

    Audit finding F1 was never a missing control. RLS was enabled, FORCEd
    and covered by passing tests; it was simply not in force at runtime,
    because the connection carried BYPASSRLS. A system in that state looks
    completely healthy from the outside, and the thing it silently stops
    enforcing is cross-institution isolation of children's health data.

    Two misconfigurations recreate exactly that state, so both are refused
    here instead of being absorbed:

      * `TENANT_DATABASE_URL` unset. The old code fell back to
        `DATABASE_URL`, which is the PRIVILEGED path by definition — so
        forgetting one setting reverted the entire fix, and nothing said so.
      * `TENANT_DATABASE_URL` set, but pointed at a role that is a superuser
        or holds BYPASSRLS. The URL being present proves nothing; only the
        role's own attributes do.

    Refusing costs a 500 on caretaker traffic, which is loud and immediate.
    That is the intended trade: a deployment with broken tenant isolation
    must stop, not serve. There is deliberately no ENVIRONMENT exemption —
    an exemption is precisely how the first version came to be inert.
    """
    url = settings.TENANT_DATABASE_URL
    if not url:
        raise RuntimeError(
            "TENANT_DATABASE_URL is not configured. Caretaker-facing requests "
            "must connect as the unprivileged `signal_app` role so row-level "
            "security applies; falling back to DATABASE_URL would restore the "
            "audit-F1 state in which RLS is enabled but never enforced. "
            "See backend/.env.example."
        )

    engine = _engine_for(url)
    if url in _TENANT_ROLE_VERIFIED:
        return engine

    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT rolsuper, rolbypassrls FROM pg_roles "
                "WHERE rolname = current_user"
            )
        ).one()
    if row.rolsuper or row.rolbypassrls:
        raise RuntimeError(
            "TENANT_DATABASE_URL connects as a role that can bypass row-level "
            "security (rolsuper=%r, rolbypassrls=%r). RLS would be inert and "
            "tenant isolation would rest entirely on handler-side WHERE "
            "clauses. Point it at the unprivileged `signal_app` role created "
            "by migration 0001." % (row.rolsuper, row.rolbypassrls)
        )

    _TENANT_ROLE_VERIFIED.add(url)
    return engine


def get_tenant_db(
    current_staff: "CurrentStaff" = Depends(get_current_verified_staff),
    settings: Settings = Depends(get_settings),
) -> Iterator[Session]:
    """Tenant-scoped session — the DB enforces isolation, not the handler.

    Connects as the unprivileged `signal_app` role (no superuser, no
    BYPASSRLS) and sets `app.institution_id` from the SIGNED token, so the
    RLS policies from migration 0001 actually bind. A handler that forgets
    its `WHERE institution_id = ...` now returns nothing instead of another
    institution's children (audit F1).

    `set_config(..., true)` makes the setting TRANSACTION-local. That is not
    a detail: with a pooled connection a session-level setting would survive
    into whichever request borrowed the connection next, which is precisely
    the cross-tenant leak this function exists to prevent.
    """
    session = Session(bind=_verified_tenant_engine(settings), expire_on_commit=False)
    try:
        session.execute(
            text("SELECT set_config('app.institution_id', :iid, true)"),
            {"iid": str(current_staff.institution_id)},
        )
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_admin_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> CurrentStaff:
    """SYSTEM-LEVEL admin gate (THREAT_MODEL §2: NextaSol/dev admin).

    Fail-closed ordering: valid JWT (401 otherwise) → staff row exists and is
    ACTIVE and role == "admin" in the DB (403 otherwise). The DB row, not
    the JWT claim, decides privilege: promotions/demotions/deactivations
    take effect immediately.

    BOUNDARY NOTE: endpoints using this dependency are the ONLY places that
    may read across institutions. Any endpoint guarded by
    `get_current_verified_staff` keeps strict institution scoping.
    """
    claims = _verified_claims(credentials, settings)
    try:
        staff_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    staff = db.get(Staff, staff_id)
    if staff is None or not staff.is_active or staff.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return CurrentStaff(
        staff_id=staff.id,
        institution_id=staff.institution_id,
        role=staff.role,
    )


def require_active_staff(
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
) -> CurrentStaff:
    """Deactivation guard for the write surface (sessions, turns, STT).

    A deactivated account keeps read access to already-visible data until its
    short-lived token expires (token blacklisting is FEAT-12), but can never
    create anything new. Institution scoping is untouched.
    """
    staff = db.get(Staff, current_staff.staff_id)
    if staff is None or not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_staff
