"""Routing primitive for reviewed, confirmed matches; no symptom detection.

Not connected to live screening until approved match rules/local routing
are supplied. Age gaps stay explicit; this never extends source scope.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationRoute:
    recipient: str
    acknowledgement_required: bool
    escalation_contact: str


def route_confirmed_match(*, action: str, citation_ref: str, approved: bool,
                          chronological_age_in_scope: bool,
                          routes: dict[str, EscalationRoute], turns_used: int) -> dict | None:
    if action not in {"immediate_medical", "urgent_medical", "prompt_medical", "safeguarding_pathway"}:
        return None
    if not approved:
        raise ValueError("Unapproved content cannot trigger a clinical route")
    if not chronological_age_in_scope:
        raise ValueError("No approved age-appropriate route; source coverage gap requires review")
    route = routes.get(action)
    if route is None or not route.recipient.strip() or not route.escalation_contact.strip():
        raise ValueError("Local recipient and escalation contact must be configured")
    # Turn count is metadata, never a gate on an already-confirmed urgent match.
    return {"status": "screening_interrupted", "action": action, "citation_ref": citation_ref,
            "grade": None, "developmental_flag": False, "turns_used": turns_used,
            "recipient": route.recipient, "acknowledgement_required": route.acknowledgement_required,
            "escalation_contact": route.escalation_contact}
