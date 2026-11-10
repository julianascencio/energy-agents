"""
From 57 role descriptions to 53 reusable role agents
====================================================================================================

Every role description reviewed through 10 November 2026 maps to a generic agent.
Duplicate procurement, forward-deployed engineering and translated support
listings share contracts. Identifying source metadata is omitted. Job descriptions
inform scope; they are not evidence
that an AI agent is qualified to perform a profession.

This offline example runs all roles on an intentionally incomplete **synthetic**
energy pilot brief, then coordinates five specialists using the existing
orchestrator. Outputs are **scripted work plans**, not completed deliverables,
measured savings, job replacement estimates, or live-model evaluations.
"""

from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from energy_agents.career_roles import (
    career_catalogue,
    career_runners,
    run_career_agent,
    synthetic_career_case,
)
from energy_agents.orchestrator import AgentTask, run_orchestrator

# %%
# Inspect the source-to-agent mapping and run every role
# ----------------------------------------------------------------------------------------------------
# No API key or network is required. The same brief is deliberately missing
# finance, HR, legal and site engineering inputs; those gaps must survive.
catalogue = career_catalogue()
case = synthetic_career_case()
reports = {r["id"]: run_career_agent(r["id"], case) for r in catalogue["roles"]}
assert len(reports) == 53 and all(r["success"] for r in reports.values())
assert sum(len(r["listing_ids"]) for r in catalogue["roles"]) == 57
print("57 role descriptions -> 53 role contracts -> 53 scripted work plans")
print("Protocol success is not completion or validation of professional work.")

# %%
# Build an explicit delivery workflow
# ----------------------------------------------------------------------------------------------------
# The catalogue's suggested handoffs are not automatic dependencies. Choose a
# small directed acyclic graph for the business objective. Existing Python/ML
# and forward-deployed workflows can receive separate, explicit implementation
# handoffs; this example does not silently invoke them.
tasks = [
    AgentTask("value_case", "career_ai_business_consulting_assistant", payload=case),
    AgentTask("requirements", "career_business_analyst", ("value_case",), case),
    AgentTask("solution", "career_forward_deployed_engineer", ("requirements",), case),
    AgentTask("security", "career_cloud_security_engineer", ("solution",), case),
    AgentTask("implementation", "career_full_stack_ai_engineer", ("solution", "security"), case),
]
team = run_orchestrator(tasks, career_runners())
assert team["success"]
for name, result in team["results"].items():
    print(name, "missing inputs:", result["inspection"]["missing_inputs"])
    assert result["requires_human_review"] and not result["execution_authorized"]

# %%
# Inspect a proposal and unresolved evidence
# ----------------------------------------------------------------------------------------------------
# The replay lists intended work and review checks. A live model can instead
# propose substantive content, but the validator checks structure and reference
# membership only. Human review must assess factual and professional quality.
proposal = team["results"]["solution"]["proposal"]
print(proposal["deliverables"][0]["content"])
print("Assumptions:", proposal["deliverables"][0]["assumptions"])

# %%
# Visualize actual catalogue coverage and missing-input counts
# ----------------------------------------------------------------------------------------------------
# These are counts from the catalogue and synthetic case, not performance scores.
families = Counter(r["family"] for r in catalogue["roles"])
listings = Counter()
for card in catalogue["roles"]:
    listings[card["family"]] += len(card["listing_ids"])
labels = sorted(families, key=lambda k: (families[k], k))
fig, axes = plt.subplots(1, 2, figsize=(14, 6), layout="constrained")
y = list(range(len(labels)))
axes[0].barh([v + .18 for v in y], [listings[k] for k in labels], height=.34,
             color="#9bb9cb", label="Observed openings")
axes[0].barh([v - .18 for v in y], [families[k] for k in labels], height=.34,
             color="#167d8d", label="Distinct agents")
axes[0].set_yticks(y, labels)
axes[0].set_xlabel("Count in 2026-11-10 snapshot")
axes[0].set_title("Coverage across 11 role families")
axes[0].legend(loc="lower right", fontsize=8)
names = list(team["results"])
present = [len(team["results"][n]["inspection"]["present_inputs"]) for n in names]
missing = [len(team["results"][n]["inspection"]["missing_inputs"]) for n in names]
axes[1].barh(names, present, color="#167d8d", label="Supplied inputs")
axes[1].barh(names, missing, left=present, color="#df9b4b", label="Missing inputs")
axes[1].set_xlabel("Required input count; content is not verified")
axes[1].set_title("Synthetic pilot: evidence gaps remain visible")
axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))
axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.13), ncol=2, fontsize=8)
fig.suptitle("Public-career role agents | offline work-plan demonstration", fontsize=15)
plt.show()
