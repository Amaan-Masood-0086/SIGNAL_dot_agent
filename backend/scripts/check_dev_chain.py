"""One-off dev check: verify the dev DB audit chain after seeding.

Run from backend/:  python scripts/check_dev_chain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.services.audit import verify_audit_chain_detail  # noqa: E402

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
with Session(engine) as session:
    intact, checked, first_broken = verify_audit_chain_detail(session)
    print(f"chain_intact={intact} entries_checked={checked} first_broken={first_broken}")
engine.dispose()
