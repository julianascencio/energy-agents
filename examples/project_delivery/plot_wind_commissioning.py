"""
Which commissioning activities are worth accelerating?
=======================================================

Inspired by Orsted's 5 November 2026 commercial-operation milestone update.
This is an entirely synthetic 100 MW wind schedule, not Orsted project data.
The agent compares feasible packages, respects minimum durations and keeps a
no-action baseline. Contribution brought forward is not realised profit.
"""

import matplotlib.pyplot as plt

from energy_agents.commissioning import rank_acceleration, reference_case, run_commissioning_agent

case = reference_case()
run = run_commissioning_agent(case)
assert run["success"]
screen = run["reports"]["screen"]
assert screen == rank_acceleration(case)
best = screen["recommended_package"]
fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
for i, task in enumerate(case["tasks"]):
    key = task["id"]
    for offset, plan, color, label in [
        (-0.18, screen["baseline"], "#8197a5", "Baseline"),
        (0.18, best["schedule"], "#247b91", "Proposed"),
    ]:
        item = plan["tasks"][key]
        axes[0].barh(
            i + offset,
            item["finish_day"] - item["start_day"],
            left=item["start_day"],
            height=0.32,
            color=color,
            label=label if i == 0 else None,
        )
axes[0].set(
    yticks=range(len(case["tasks"])),
    yticklabels=[t["id"].replace("_", " ") for t in case["tasks"]],
    xlabel="Days from common start",
    title="Synthetic dependency schedule",
)
axes[0].invert_yaxis()
axes[0].legend()
selected = [p for p in screen["packages"] if len(p["options"]) == 1] + [best]
axes[1].barh(
    [", ".join(p["options"]).replace("_", " ") for p in selected],
    [p["net_benefit_eur"] / 1000 for p in selected],
    color="#247b91",
)
axes[1].axvline(0, color="black", linewidth=0.8)
axes[1].set(
    xlabel="Expected net benefit (EUR thousand)", title="Feasible singles and best combined package"
)
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
plt.show()

# %%
# Both computation paths are deterministic. No live LLM run or quality advantage
# is claimed; the agent adds an inspectable role contract and permission boundary.
print("Baseline completion day:", screen["baseline"]["completion_day"])
print("Proposed completion day:", best["schedule"]["completion_day"])
print("Days brought forward:", best["days_saved"])
print("Expected contribution EUR:", best["gross_contribution_eur"])
print("Acceleration cost EUR:", best["cost_eur"])
print("Expected net benefit EUR:", best["net_benefit_eur"])
print("Decision:", screen["decision"])
