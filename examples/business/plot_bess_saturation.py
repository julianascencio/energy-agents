"""
Battery revenue concentration: the cost of a flat forecast
==========================================================

Inspired by Clean Horizon's 4 November 2026 publication. Two published annualised
index inputs are combined with explicitly illustrative 10 MW / 20 MWh economics.
Revenue paths are our stress assumptions, not Clean Horizon forecasts. This
executes a bounded scripted finance agent; it is not a live LLM benchmark.
"""

import matplotlib.pyplot as plt

from energy_agents.business import reference_case, run_bess_agent, stress_revenues

case = reference_case()
run = run_bess_agent(case)
assert run["success"]
screen = run["reports"]["screen"]
assert screen == stress_revenues(case)
scenarios = screen["scenarios"]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
colors = ["#247b91", "#e4ae42", "#ad667c"]
for (name, result), color in zip(scenarios.items(), colors):
    axes[0].plot(
        [r["year"] for r in result["annual"]],
        [r["cash_flow_eur"] / 1e6 for r in result["annual"]],
        label=name.replace("_", " "),
        color=color,
        linewidth=2,
    )
axes[0].set(
    xlabel="Operating year",
    ylabel="Annual operating cash (EUR million)",
    title="Illustrative revenue paths",
)
axes[0].legend()
axes[1].bar(
    [name.replace("_", "\n") for name in scenarios],
    [v["npv_eur"] / 1e6 for v in scenarios.values()],
    color=colors,
)
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set(ylabel="Unlevered pretax NPV (EUR million)", title="15 years, 10% real discount rate")
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("BESS investment screening — modelled scenarios, not realised returns")
plt.show()

# %%
# The budget is the discounted operating cash in this simplified model. It is
# neither a transaction valuation nor an estimate of an achievable purchase price.
print("Source:", screen["source_url"])
print("Source classification:", screen["source_classification"])
print("Ancillary concentration:", f"{screen['ancillary_share']:.1%}")
for name, result in scenarios.items():
    print(
        name,
        "NPV EUR",
        round(result["npv_eur"]),
        "reduction vs flat EUR",
        round(result["npv_reduction_vs_flat_eur"]),
    )
print("Decision:", run["decision"])
print("LLM execution: not run; scripted tools agree with deterministic baseline")
