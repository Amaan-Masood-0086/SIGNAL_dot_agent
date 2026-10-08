"""Seed a few synthetic children so the demo roster is not empty.

Idempotent (matched by name within the synthetic institution). "Ayan" is
deliberately NOT seeded: the demo script registers him live in Act 1.
Run after seed_synthetic_tenant.py, under the privileged DATABASE_URL.
"""

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import SYNTHETIC_INSTITUTION_ID
from app.core.config import get_settings
from app.models.child import Child


def _months_ago(months: int) -> datetime.date:
    return datetime.date.today() - datetime.timedelta(days=round(months * 30.44))


def main() -> None:
    today = datetime.date.today()
    children = [
        dict(name="Zara (synthetic)", dob_confirmed=True, dob=_months_ago(30)),
        dict(name="Bilal (synthetic)", dob_confirmed=True, dob=_months_ago(54)),
        dict(
            name="Hira (synthetic)",
            dob_confirmed=False,
            estimated_age_range="30-36 months",
            estimated_age_note="intake worker estimate",
            estimated_age_lower_months=30,
            estimated_age_upper_months=36,
            age_reference_date=today,
        ),
    ]
    engine = create_engine(get_settings().DATABASE_URL)
    with Session(engine) as session:
        for spec in children:
            exists = session.execute(
                select(Child.id).where(
                    Child.institution_id == SYNTHETIC_INSTITUTION_ID,
                    Child.name == spec["name"],
                )
            ).first()
            if exists:
                print(f"already present: {spec['name']}")
                continue
            session.add(
                Child(
                    institution_id=SYNTHETIC_INSTITUTION_ID,
                    intake_date=today,
                    is_synthetic=True,
                    **spec,
                )
            )
            print(f"seeded: {spec['name']}")
        session.commit()


if __name__ == "__main__":
    main()
