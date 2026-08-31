"""Seed the synthetic tenant for local development.

The FEAT-01 auth stub mints tokens for a fixed synthetic institution id;
POST /children requires that institution row to exist, and FEAT-03 session
endpoints fail closed unless the JWT identity resolves to a real staff row.
Idempotent.
"""

import sys
import uuid
from pathlib import Path

# Scripts run standalone: put the backend package root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import SYNTHETIC_INSTITUTION_ID
from app.core.config import get_settings
from app.models.institution import Institution
from app.models.staff import Staff

# Same derivation as the FEAT-01 auth stub, so the seeded row matches the
# identity the stub token carries.
SYNTHETIC_STAFF_EMAIL = "synthetic-staff@signal.example"
SYNTHETIC_STAFF_ID = uuid.uuid5(uuid.NAMESPACE_URL, f"signal:{SYNTHETIC_STAFF_EMAIL}")


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        existing = session.execute(
            select(Institution).where(Institution.id == SYNTHETIC_INSTITUTION_ID)
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                Institution(
                    id=SYNTHETIC_INSTITUTION_ID,
                    name="Synthetic Demo Institution",
                    is_synthetic=True,
                )
            )
            session.commit()
            print("seeded synthetic institution")
        else:
            print("synthetic institution already present")

        staff = session.execute(
            select(Staff).where(Staff.id == SYNTHETIC_STAFF_ID)
        ).scalar_one_or_none()
        if staff is None:
            session.add(
                Staff(
                    id=SYNTHETIC_STAFF_ID,
                    institution_id=SYNTHETIC_INSTITUTION_ID,
                    email=SYNTHETIC_STAFF_EMAIL,
                    # Phase-1 stub never verifies passwords (FEAT-12 scope).
                    hashed_password="unused-in-phase-1-stub",
                    role="caretaker",
                    is_synthetic=True,
                )
            )
            session.commit()
            print("seeded synthetic staff")
        else:
            print("synthetic staff already present")
    engine.dispose()


if __name__ == "__main__":
    main()
