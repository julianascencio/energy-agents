"""
PV professional team: losses to proposed actions
================================================

Five professional roles investigate a synthetic six-day plant case. Missing meter
energy is excluded, never filled with zero. Fault associations are not causal proof.
The revenue panel is a conditional same-period recurrence scenario, not a forecast.
The three modes use identical tools: this tests architecture parity, not LLM quality.
"""

import matplotlib.pyplot as plt

from energy_agents.pv.analysis import run_comparison

comparison = run_comparison()
assert comparison["all_passed"] and comparison["report_parity"]
team = comparison["runs"][2]
reports = team["reports"]
p = reports["performance"]["data"]
r = reports["reliability"]["data"]
c = reports["commercial"]["data"]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
axes[0].bar(
    ["Fault-associated", "Curtailment", "Unresolved"],
    [r["equipment_fault_mwh"], r["curtailment_mwh"], r["unresolved_mwh"]],
    color=["#247b91", "#e4ae42", "#ad667c"],
)
axes[0].set(ylabel="Deficit (MWh)", title="Synthetic loss accounting: 5 of 6 days")
axes[1].bar(
    ["Gross recovery", "Intervention cost", "Net value"],
    [c["conditional_gross_value"], c["intervention_cost"], c["conditional_net_value"]],
    color=["#247b91", "#ad667c", "#54966b"],
)
axes[1].set(ylabel="EUR", title="Conditional recovery scenario: not a forecast")
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=9)
fig.suptitle("PV operations — synthetic inputs, advisory outputs")
plt.show()

# %%
# All three modes must agree numerically. The team introduces explicit role
# boundaries and handoffs; these call counts do not demonstrate higher quality.
for run in comparison["runs"]:
    print(
        run["mode"],
        "passed:",
        run["success"],
        "planner calls:",
        run["planner_calls"],
        "tool calls:",
        run["tool_calls"],
    )
print("Excluded dates:", p["excluded_dates"])
print("Surplus kept separate:", p["surplus_mwh"], "MWh")
for action in reports["maintenance"]["data"]["actions"]:
    print(action["action"], "—", action["status"])
print("Open issues:", reports["asset_summary"]["data"]["open_issues"])
print("Reviewer:", team["review"])
