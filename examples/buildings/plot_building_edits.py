"""
Tool-augmented versus primitive building edits
============================================================

Based on Shirzadi, Lopez and Stylianou (2026), DOI 10.1016/j.egyai.2026.100896.
The left panel is a deterministic synthetic replay, NOT an LLM benchmark.
Both policies succeed by construction; finish/validation calls are excluded.
The right panel contains manually transcribed published Table 8A observations.
Counts use different scopes and must not be compared across panels.
No EnergyPlus simulation, energy savings or NECB compliance is claimed.
"""

import matplotlib.pyplot as plt

from energy_agents.analysis import published_windows, run_comparison

runs = run_comparison()
published = published_windows()
fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
colors = ["#2f6fdb", "#e69732"]
for i, surface in enumerate(("domain", "primitive")):
    selected = [r for r in runs if r["surface"] == surface]
    axes[0].bar(
        [j + (i - 0.5) * 0.35 for j in range(2)],
        [r["edit_calls"] for r in selected],
        width=0.35,
        label=surface,
        color=colors[i],
    )
    selected = [r for r in published if r["surface"] == surface]
    axes[1].barh(
        [j + (i - 0.5) * 0.35 for j in range(7)],
        [r["calls"] for r in selected],
        height=0.35,
        label=surface,
        color=colors[i],
    )
axes[0].set(
    xticks=[0, 1],
    xticklabels=["Windows", "Lighting"],
    ylabel="Local edit calls (finish excluded)",
    title="Synthetic scripted replay",
)
axes[1].set(
    yticks=list(range(7)),
    yticklabels=[r["building"] for r in published[::2]],
    xlabel="Reported calls (paper Table 8A)",
    title="Published window-task observations",
)
for ax in axes:
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
plt.show()

# %%
# Each execution retains the changed model and every tool action. Failed task
# postconditions roll back to the original model. These checks cover exact edit
# effects, not whole-building physical validity.
for run in runs:
    print(run["task"], run["surface"], run["success"], run["edit_calls"], run["simulation"])
