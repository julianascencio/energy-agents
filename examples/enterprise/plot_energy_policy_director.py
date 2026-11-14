"""
Flexible AI data-center regulatory policy director
==================================================

Run an offline policy work-plan agent for a fictional 100 MW campus with
20 MW of potentially shiftable load. These numbers are synthetic inputs, not
verified flexibility or accredited capacity. No current tariff, real docket,
regulatory filing or coalition position is asserted. The missing proceeding,
cost evidence and engagement calendar remain visible in the result.

Run: ``python examples/enterprise/plot_energy_policy_director.py``.
For substantive model-generated drafts, pass a configured ``CareerRolePlanner``
to ``run_career_agent`` after supplying appropriate primary-source evidence.
The replay below only demonstrates the work-plan protocol.
"""

import json

from energy_agents.career_roles import run_career_agent

ROLE_ID = "career_energy_markets_regulatory_policy_director"


def synthetic_policy_case():
    """Return a deliberately incomplete fictional policy brief."""
    inputs = {
        "policy_objective": "Compare firm and flexible connection policy options for a 100 MW campus.",
        "jurisdiction_and_market": "Hypothetical PJM-region project; state and utility not selected.",
        "load_flexibility_profile": (
            "20 MW may shift for two hours; baseline, telemetry, rebound, SLA constraints "
            "and availability remain unvalidated. No accredited capacity is claimed."
        ),
        "member_positions": (
            "Fictional operator seeks earlier access; utility seeks upgrade cost recovery; "
            "consumer representative seeks protection against cost shifting. No consensus."
        ),
    }
    return {
        "id": "synthetic-flexible-campus-policy",
        "objective": "Prepare an evidence collection and policy evaluation work plan.",
        "inputs": {key: {"text": value, "evidence_ids": ["fictional_brief"]}
                   for key, value in inputs.items()},
        "evidence": {"fictional_brief": {
            "kind": "synthetic", "summary": "Educational scenario; no actual project or proceeding."
        }},
    }


if __name__ == "__main__":
    result = run_career_agent(ROLE_ID, synthetic_policy_case())
    assert result["success"]
    assert result["inspection"]["missing_inputs"] == [
        "proceeding_evidence", "cost_and_reliability_evidence", "engagement_calendar"
    ]
    print(json.dumps(result, indent=2))
