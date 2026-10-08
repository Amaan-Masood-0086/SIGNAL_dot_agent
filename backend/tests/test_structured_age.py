import datetime as dt
import pytest
from pydantic import ValidationError
from app.schemas.child import ChildCreate
from app.schemas.evidence import EvidenceObservation
from app.models.child import Child
from app.services.risk_pipeline import resolve_age_context


def test_estimate_advances_without_changing_width():
    child = Child(dob_confirmed=False, estimated_age_lower_months=24, estimated_age_upper_months=30, age_reference_date=dt.date(2025, 1, 15))
    result = resolve_age_context(child, dt.date(2025, 4, 14))
    assert result.age_months == 26
    assert result.estimated_age_range == "26-32 months"


def test_partial_estimate_rejected():
    with pytest.raises(ValidationError):
        ChildCreate(name="Synthetic", dob_confirmed=False, estimated_age_range="24-30 months", estimated_age_lower_months=24)


def test_new_caretaker_account_defaults_unknown():
    evidence = EvidenceObservation(citation_ref="test", account="I started this shift yesterday")
    assert evidence.state == "unknown"
    with pytest.raises(ValidationError):
        EvidenceObservation(citation_ref="test", account="I started this shift yesterday", state="absent_after_observation")
