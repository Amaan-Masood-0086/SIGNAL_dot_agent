"""Bootstrap the FIRST admin — a management command, never an open endpoint.

The RBAC ticket locks this: promoting staff to admin is an admin-only,
audit-logged endpoint, but SOMETHING must create the first admin before any
admin exists. That something is this script, run by an operator with DB
access (deployment-time, like the env-var keys per ADR-09).

Usage (from backend/, venv active, .env configured):

    python scripts/seed_admin.py --email root@signal.example
    python scripts/seed_admin.py --email root@signal.example --institution "NextaSol System"

Idempotent: re-running promotes/reactivates the existing row instead of
duplicating it. The seeded admin logs in through the Phase-1 stub token
endpoint (POST /api/v1/auth/token with this email) — the stub mints the DB
row's real role. No password is set or needed in Phase 1 (real credentials
arrive with FEAT-12); the stored hash is an unusable random placeholder.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

# Allow `python scripts/seed_admin.py` from backend/ — app package is one up.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.models.institution import Institution  # noqa: E402
from app.models.staff import Staff  # noqa: E402
from app.services.audit import AuditService  # noqa: E402

DEFAULT_INSTITUTION = "NextaSol System (synthetic)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the first SIGNAL admin")
    parser.add_argument("--email", required=True, help="Admin email (login identity)")
    parser.add_argument(
        "--institution",
        default=DEFAULT_INSTITUTION,
        help="Host institution name (created if missing)",
    )
    args = parser.parse_args()

    settings = get_settings()
    if settings.ENVIRONMENT != "synthetic_only":
        print(
            "Refusing to seed outside ENVIRONMENT=synthetic_only "
            "(Phase 1 gate — RISK_REGISTER R8)."
        )
        return 1

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine, expire_on_commit=False) as session:
        institution = session.execute(
            select(Institution).where(Institution.name == args.institution)
        ).scalar_one_or_none()
        if institution is None:
            institution = Institution(name=args.institution, is_synthetic=True)
            session.add(institution)
            session.flush()
            print(f"Created institution: {institution.name} ({institution.id})")

        staff = session.execute(
            select(Staff).where(Staff.email == args.email)
        ).scalar_one_or_none()
        created = staff is None
        if created:
            staff = Staff(
                institution_id=institution.id,
                email=args.email,
                # Unusable placeholder — Phase 1 login is a stub; real
                # password hashing arrives with FEAT-12.
                hashed_password=f"!seeded-{secrets.token_urlsafe(24)}",
                role="admin",
                is_active=True,
                is_synthetic=True,
            )
            session.add(staff)
            session.flush()
        else:
            staff.role = "admin"
            staff.is_active = True

        # Tamper-evidence applies to bootstrapping too: the chain records
        # that a seed happened (actor None = out-of-band operator action).
        AuditService(session).append(
            actor_id="",
            action="staff.seed_admin",
            resource_type="staff",
            resource_id=str(staff.id),
            institution_id=str(institution.id),
        )
        session.commit()

        verb = "Created" if created else "Promoted/reactivated"
        print(f"{verb} admin: {staff.email} ({staff.id})")
        print("Log in via POST /api/v1/auth/token with this email (synthetic_only).")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
