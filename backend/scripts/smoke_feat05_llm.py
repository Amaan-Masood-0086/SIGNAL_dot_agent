"""FEAT-05 real-LLM smoke — T1, T5, T6, T9 through the ACTUAL pipeline.

Run from backend/ AFTER adding LLM_PROVIDER / LLM_API_KEY / LLM_MODEL to
backend/.env:

    python scripts/smoke_feat05_llm.py

What it does:
- refuses to run when no real LLM is configured (never silently falls back
  to the synthetic reasoner — this smoke must exercise the real model);
- spins up an ephemeral, fully-migrated Postgres DB with the knowledge base
  ingested (the dev DB is never polluted);
- runs the four pinned conversations through RiskPipeline with the real
  provider and compares against the LOCKED expectations:
    T1  HIGH Hearing, cites HEAR-RF-003
    T5  HIGH Hearing (cross-domain), cites HEAR-RF-013 + HEAR-RF-008
    T6  HIGH Hearing — ADR-06 literal count rule per the R14 lock
        (dataset says MODERATE; HIGH here is CORRECT until sign-off)
    T9  INSUFFICIENT_INFORMATION, zero flags rows
- prints grades + citations and exits non-zero on any mismatch.
"""

from __future__ import annotations

import csv
import datetime
import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.services.knowledge import load_knowledge_base  # noqa: E402
from app.services.llm import provider_from_settings  # noqa: E402
from app.services.pipeline_agents import (  # noqa: E402
    AgentContractError,
    GroundingError,
)
from app.services.risk_pipeline import RiskPipeline  # noqa: E402

CSV_PATH = (
    BACKEND_DIR.parent
    / ".ai" / "brain" / "knowledge-base-source" / "signal_test_conversations_v2.csv"
)
REFERENCE_DATE = datetime.date.today()

# convo -> (expected_grade, expected_domain, must-cite refs)
LOCKED = {
    "T1": ("HIGH", "Hearing", {"HEAR-RF-003"}),
    "T5": ("HIGH", "Hearing", {"HEAR-RF-013", "HEAR-RF-008"}),
    "T6": ("HIGH", "Hearing", set()),  # grade is the R14 assertion; cites vary
    "T9": ("INSUFFICIENT_INFORMATION", None, set()),
}


def _age_months(age: str) -> int:
    value, unit = age.split()
    return int(value) if unit == "mo" else int(value) * 12


def _dob_for(months: int) -> datetime.date:
    total = REFERENCE_DATE.year * 12 + (REFERENCE_DATE.month - 1) - months
    return datetime.date(total // 12, total % 12 + 1, 15)


def main() -> int:
    settings = get_settings()
    provider = provider_from_settings(settings)
    if provider is None:
        print(
            "LLM not configured — add LLM_PROVIDER / LLM_API_KEY / LLM_MODEL "
            "to backend/.env first. This smoke refuses the synthetic fallback "
            "on purpose: it must exercise the real model."
        )
        return 2

    from alembic import command
    from alembic.config import Config

    db_name = f"signal_smoke_{uuid.uuid4().hex[:8]}"
    root_url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()

    target_url = settings.DATABASE_URL.rsplit("/", 1)[0] + f"/{db_name}"
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", target_url)
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(target_url)
    failures = 0
    try:
        session_db = Session(bind=engine, expire_on_commit=False)
        load_knowledge_base(session_db)
        session_db.commit()

        with open(CSV_PATH, newline="", encoding="utf-8") as handle:
            conversations = {row["id"]: row for row in csv.DictReader(handle)}

        for convo_id in ("T1", "T5", "T6", "T9"):
            failures += _run_one(session_db, provider, conversations[convo_id])
        session_db.close()
    finally:
        engine.dispose()
        admin_engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :db AND pid <> pg_backend_pid()"
                ),
                {"db": db_name},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        admin_engine.dispose()

    print("\nRESULT:", "ALL 4 MATCH LOCKED EXPECTATIONS" if failures == 0
          else f"{failures} MISMATCH(ES) — do not proceed, investigate first")
    return 0 if failures == 0 else 1


def _run_one(db: Session, provider, row: dict) -> int:
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.session import Session as ConversationSession
    from app.models.staff import Staff

    convo_id = row["id"]
    expected_grade, expected_domain, must_cite = LOCKED[convo_id]

    inst = Institution(name=f"Smoke {convo_id}", is_synthetic=True)
    db.add(inst)
    db.flush()
    staff = Staff(
        id=uuid.uuid4(), institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@smoke.example",
        hashed_password="unused", role="caretaker", is_synthetic=True,
    )
    db.add(staff)
    child = Child(
        institution_id=inst.id, name=f"Smoke {convo_id}",
        intake_date=REFERENCE_DATE,
        dob_confirmed=True, dob=_dob_for(_age_months(row["age"])),
        is_synthetic=True,
    )
    db.add(child)
    db.flush()
    convo = ConversationSession(
        institution_id=inst.id, child_id=child.id, staff_id=staff.id, mode="text"
    )
    db.add(convo)
    db.flush()

    pipeline = RiskPipeline(db, provider)
    turns = [row["caretaker_opening"]]
    try:
        result = pipeline.run(
            session=convo, child=child, caretaker_turns=list(turns),
            turn_number=1, staff_id=staff.id, institution_id=inst.id,
            reference_date=REFERENCE_DATE,
        )
        follow_ups = 0
        while result.outcome == "follow_up" and follow_ups < 2:
            follow_ups += 1
            turns.append(row["caretaker_response"])
            result = pipeline.run(
                session=convo, child=child, caretaker_turns=list(turns),
                turn_number=len(turns), staff_id=staff.id,
                institution_id=inst.id, reference_date=REFERENCE_DATE,
            )
    except (GroundingError, AgentContractError) as exc:
        print(f"{convo_id}: FAIL — pipeline error: {exc}")
        return 1

    problems = []
    if result.grade != expected_grade:
        problems.append(f"grade {result.grade!r} != expected {expected_grade!r}")
    if expected_domain is not None and result.domain != expected_domain:
        problems.append(f"domain {result.domain!r} != expected {expected_domain!r}")
    missing = must_cite - set(result.citation_refs)
    if missing:
        problems.append(f"missing citations {sorted(missing)}")

    status = "FAIL" if problems else "PASS"
    print(
        f"{convo_id}: {status} — outcome={result.outcome} "
        f"grade={result.grade} domain={result.domain} "
        f"citations={result.citation_refs}"
        + (f" follow-ups={result.turn - 1}" if result.turn > 1 else "")
    )
    if result.follow_up_question and result.outcome == "follow_up":
        print(f"    (stopped mid-loop: {result.follow_up_question!r})")
        problems.append("did not conclude within the available turns")
    for problem in problems:
        print(f"    MISMATCH: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
