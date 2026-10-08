import pytest
from app.services.urgent_route import EscalationRoute, route_confirmed_match


@pytest.mark.parametrize("turns", [0, 1, 5, 6])
def test_confirmed_urgent_match_ignores_interview_budget(turns):
    result = route_confirmed_match(action="immediate_medical", citation_ref="synthetic", approved=True,
        chronological_age_in_scope=True, turns_used=turns,
        routes={"immediate_medical": EscalationRoute("Synthetic responder", True, "Synthetic supervisor")})
    assert result["status"] == "screening_interrupted"
    assert result["grade"] is None and not result["developmental_flag"]


@pytest.mark.parametrize("approved,in_scope", [(False, True), (True, False)])
def test_draft_or_uncovered_age_never_routes(approved, in_scope):
    with pytest.raises(ValueError):
        route_confirmed_match(action="immediate_medical", citation_ref="synthetic", approved=approved,
            chronological_age_in_scope=in_scope, routes={}, turns_used=1)
