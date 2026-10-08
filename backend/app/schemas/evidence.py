"""Explicit observation states. Uncertainty must never become absence."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

EvidenceState = Literal["present", "absent_after_observation", "not_observed", "unknown", "not_applicable", "conflicting_reports", "previously_present_now_lost"]


class EvidenceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citation_ref: str = Field(min_length=1, max_length=80)
    state: EvidenceState = "unknown"
    personally_observed: bool = False
    observation_opportunity: bool = False
    account: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def absence_requires_observation(self):
        if self.state == "absent_after_observation" and not (self.personally_observed and self.observation_opportunity):
            raise ValueError("Absence requires personal observation and an opportunity to observe")
        return self
