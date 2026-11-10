"""
Fleet operations: evidence to economic investigation
====================================================

Four synthetic solar assets are reviewed through Energy Agents and the real
Energy Data Insights operations method. The €1,500 scenario is conditional on
recurrence over the same six-day window; it is neither a forecast nor verified
recoverable revenue. Missing data holds an otherwise attractive site out of rank.
"""

import matplotlib.pyplot as plt

from energy_agents.operations import OperationsService, synthetic_portfolio

service = OperationsService(synthetic_portfolio())
result = service.review_portfolio()
assets = result["assets"]
names = [a["asset_id"].replace("solar-", "") for a in assets]
colors = {
    "investigate": "#087e80",
    "held_data_quality": "#d19a32",
    "review_economics": "#9c7183",
    "monitor": "#879aa5",
}

fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
bottom = [0.0] * len(assets)
for event, color in [
    ("equipment_fault", "#087e80"),
    ("curtailment", "#d19a32"),
    ("unresolved", "#9c7183"),
]:
    values = [a["ledger"]["deficit_by_event_mwh"][event] for a in assets]
    axes[0].bar(names, values, bottom=bottom, color=color, label=event.replace("_", " "))
    bottom = [a + b for a, b in zip(bottom, values)]
axes[0].set(title="Observed deficits · event associations", ylabel="MWh")
axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=1, frameon=False)
values = [a["ledger"]["conditional_net_value"] for a in assets]
axes[1].bar(names, values, color=[colors[a["state"]] for a in assets])
axes[1].axhline(0, color="#647480", linewidth=0.8)
for i, a in enumerate(assets):
    axes[1].annotate(
        a["state"].replace("_", "\n"),
        (i, max(0, values[i])),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontsize=9,
    )
axes[1].set(title="Conditional repair economics · same six days", ylabel="EUR", ylim=(-650, 2200))
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Energy Operations | synthetic inputs, executed EDI backend", fontweight="bold")
plt.show()

# %%
# The actionable economic queue excludes incomplete data and nonpositive repair
# value. Curtailment has its own commercial investigation; it is not repaired.
print("Backend:", result["backend"])
for group in result["summaries"]:
    print("Ranked conditional net value:", group["ranked_conditional_net_value"], group["currency"])
    for action in group["ranked_actions"]:
        print(action["rank"], action["asset_id"], action["conditional_net_value"])
        print(service.draft_work_order(action["asset_id"], action["action_id"]))
