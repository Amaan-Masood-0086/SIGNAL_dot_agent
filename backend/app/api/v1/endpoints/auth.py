"""Auth endpoints — FEAT-01 STUB only.

The token endpoint mints RS256 tokens and is refused outside
`ENVIRONMENT=synthetic_only`. Real credential verification (passwords,
account lockout, token blacklisting) is FEAT-12 scope.

RBAC bootstrap seam: if a staff ROW exists for the requested email (created
by the seed script or the admin panel), the token carries that row's real
id/institution/role — this is how a seeded admin obtains an admin token in
Phase 1, and how a deactivation takes effect at login. Unknown emails keep
the original fixed synthetic caretaker identity so FEAT-01-era tests and
demos behave exactly as before.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_verified_staff, get_db
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.core.security import create_access_token
from app.models.institution import Institution
from app.models.staff import Staff
from app.schemas.auth import TokenRequest

router = APIRouter(prefix="/auth", tags=["auth"])

# Login throttle (audit F2 / CLAUDE.md "Login: 5 req / 5 min").
#
# Keyed by EMAIL, deliberately not by IP. Every login reaches this endpoint
# from the Next.js server, not from the browser — a per-IP limit here would
# see one address for the entire user base and throttle everyone together
# after five attempts by anyone. Email keying is what actually protects an
# account from credential stuffing on this topology.
#
# 5 per 5 minutes is a throttle, not a lockout: it expires on its own, so it
# cannot be used to lock a known account out indefinitely. A real lockout
# with an unlock path is FEAT-12 scope, alongside password verification.
LOGIN_LIMITER = FixedWindowRateLimiter(limit=5, window_seconds=300.0)

# Fixed synthetic identity for Phase 1 — deterministic so tests/dev can rely
# on it. Never used outside synthetic_only (guarded below).
SYNTHETIC_INSTITUTION_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


@router.post("/token")
def issue_stub_token(
    body: TokenRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    if settings.ENVIRONMENT != "synthetic_only":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stub token minting is only available in synthetic_only",
        )

    if not LOGIN_LIMITER.allow(body.email.strip().lower()):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many sign-in attempts; try again in a few minutes",
            headers={"Retry-After": "300"},
        )

    # Seeded/managed staff rows win over the fixed synthetic identity: the
    # token then carries the DB row's role (the bootstrap path for the first
    # admin, and the login-time enforcement point for deactivation).
    row = db.execute(
        select(Staff).where(Staff.email == body.email)
    ).scalar_one_or_none()
    if row is not None:
        if not row.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        staff_id, institution_id, role = row.id, row.institution_id, row.role
    else:
        staff_id = uuid.uuid5(uuid.NAMESPACE_URL, f"signal:{body.email}")
        institution_id = SYNTHETIC_INSTITUTION_ID
        role = "caretaker"

    token = create_access_token(
        staff_id=str(staff_id),
        institution_id=str(institution_id),
        role=role,
        private_key_pem=settings.JWT_PRIVATE_KEY,
        expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        settings=settings,
    )
    return envelope(
        {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


@router.get("/me")
def me(
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    """Identity for the signed-in caller.

    The JWT claims are the authority for `role` on caretaker surfaces; the
    staff row is read only to decorate the UI (own email, institution name)
    and to expose the DB-authoritative role so the frontend can render the
    same privilege the admin dependency would actually grant. Returning the
    caller's OWN email is not a PII leak — it is their identity; no other
    subject's data is exposed here, and nothing is logged.
    """
    staff = db.get(Staff, current_staff.staff_id)
    institution = db.get(Institution, current_staff.institution_id)
    return envelope(
        {
            "staff_id": str(current_staff.staff_id),
            "institution_id": str(current_staff.institution_id),
            "role": current_staff.role,
            "email": staff.email if staff is not None else None,
            "institution_name": institution.name if institution is not None else None,
            # DB-authoritative privilege: `get_current_admin_staff` refuses a
            # JWT "admin" claim over a caretaker/deactivated row, so the UI
            # must gate on the row too or it would offer dead links.
            "is_admin": bool(
                staff is not None and staff.is_active and staff.role == "admin"
            ),
        }
    )
