"""
Quantum ML engineer: demand forecasts to production schedules
======================================================================

A fictional factory has hourly demand observations and two one-hour production
batches. The agent prepares data, compares forecasting models, schedules the
batches and writes a research/technology-transfer handoff. Every numerical result
below is calculated by the agent's tools; its offline planner is scripted.

This example needs ``pip install -e '.[quantum,docs]'`` and no API keys. For the
additional PennyLane/PyTorch hybrid neural experiment, install
``.[quantum-hybrid]`` and run ``energy-agents-qml --hybrid``. The heavier training
is tested separately in CI and is not silently omitted from a requested run.
"""

# %%
# 1. Define the business question and data
# ----------------------------------------------------------------------
# Each day's 24 forecasts are issued at midnight UTC from available lag-24 and
# lag-48 measurements and calendar features. Eighteen synthetic days contain two
# warm-up days, eight training days, four validation days and four test days.

import matplotlib.pyplot as plt
import numpy as np

from energy_agents.quantum_ml import quantum_context, run_quantum_ml_agent, synthetic_load_case

case = synthetic_load_case(days=18, seed=17)
print("Evidence classification:", case["classification"])
print("Available role skills:", [skill["id"] for skill in quantum_context()["skills"]])

# %%
# 2. Execute the agent's bounded workflow
# ----------------------------------------------------------------------
# The planner has five permitted stages. It cannot alter the input, insert model
# scores, change the numerical methods or dispatch a production command.

result = run_quantum_ml_agent(case)
assert result["success"], result["trace"]
for event in result["trace"]:
    print(event["tool"], "->", event["status"])
forecast = result["reports"]["forecast"]
schedule = result["reports"]["optimization"]
print("Chronological split:", forecast["split"])
print("Validation-selected model:", forecast["selected_model"])

# %%
# 3. Inspect classical, quantum-inspired and simulated quantum forecasts
# --------------------------------------------------------------------------
# Only validation error selects hyperparameters and the downstream model. Test
# errors can favor another model; this does not trigger a retrospective switch.
# The no-entanglement circuit is an ablation, not evidence of a quantum benefit.

for row in forecast["rows"]:
    print(f"{row['model']:26s} validation MAE={row['validation_mae_mw']:.5f} MW; "
          f"test MAE={row['test']['mae_mw']:.5f} MW")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
labels = [row["model"].replace("_", " ") for row in forecast["rows"]]
positions = np.arange(len(labels))
axes[0].barh(positions - 0.18, [r["validation_mae_mw"] for r in forecast["rows"]],
             height=0.35, label="Validation", color="#4477aa")
axes[0].barh(positions + 0.18, [r["test"]["mae_mw"] for r in forecast["rows"]],
             height=0.35, label="Untouched test", color="#ee7733")
axes[0].set(yticks=positions, yticklabels=labels, xlabel="MAE (MW)",
            title="Measured errors on synthetic demand")
axes[0].invert_yaxis()
axes[0].legend()
axes[1].plot(forecast["actual_mw"][:48], label="Actual synthetic load", color="#222222")
for name in ("seasonal_persistence", forecast["selected_model"], "quantum_kernel"):
    axes[1].plot(forecast["predictions_mw"][name][:48], label=name.replace("_", " "), alpha=0.8)
axes[1].set(xlabel="Hours from test start (UTC)", ylabel="Demand (MW)",
            title="First two held-out days")
axes[1].legend(fontsize=8)

# %%
# 4. Connect predictions to a scheduling decision
# ----------------------------------------------------------------------
# Two 0.2 MW, one-hour batches choose distinct slots between 08:00 and 11:00 on
# the first test day. The objective combines assumed energy prices with an
# explicitly synthetic quadratic load-stress proxy. It is not a utility bill.
# Exact enumeration checks all 256 bitstrings, including 12 feasible schedules.
# Classical annealing and an eight-qubit, p=1 QAOA simulation are compared with
# this reference. QAOA parameters use a 144-point classical search; its output
# schedule is selected only from 2,048 sampled bitstrings.

print("Exact objective on forecasts (EUR):", schedule["exact"]["qubo_energy"])
print("Annealing optimality gaps (EUR):",
      [run["optimality_gap_eur"] for run in schedule["annealing_runs"]])
print("QAOA feasible probability:", schedule["qaoa"]["feasible_probability"])
print("QAOA sampled-schedule gap (EUR):", schedule["qaoa"]["optimality_gap_eur"])

costs = schedule["ex_post_costs"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
names = list(costs)
energy = [costs[name]["incremental_energy_eur"] for name in names]
stress = [costs[name]["load_stress_proxy_eur"] for name in names]
axes[0].bar(range(3), energy, label="Energy charge", color="#4477aa")
axes[0].bar(range(3), stress, bottom=energy, label="Assumed stress proxy", color="#ccbb44")
axes[0].set(xticks=range(3), xticklabels=["Fixed\nbaseline", "Forecast\nschedule", "Perfect\nforesight"],
            ylabel="Scenario objective (EUR)", title="Ex-post evaluation on the same actual load")
axes[0].legend(fontsize=8)
bits = np.array(schedule["exact"]["bits"]).reshape(2, 4)
axes[1].imshow(bits, cmap="Blues", vmin=0, vmax=1, aspect="auto")
axes[1].set(xticks=range(4), xticklabels=["08:00", "09:00", "10:00", "11:00"],
            yticks=[0, 1], yticklabels=["Batch 1", "Batch 2"], xlabel="First test day (UTC)",
            title="Exact forecast-based schedule for review")
for job in range(2):
    for slot in range(4):
        axes[1].text(slot, job, "RUN" if bits[job, slot] else "—", ha="center", va="center",
                     color="white" if bits[job, slot] else "#333333")

# %%
# 5. Review evidence, limitations and the next experiment
# ----------------------------------------------------------------------
# A lower test error or a successful tiny QAOA search does not establish quantum
# advantage. The simulation cost, strong classical baselines, real plant data,
# multi-season validation, noise and production constraints need further work.
# The dated literature context flags overdue review; no live search is claimed.

print("Quantum advantage demonstrated:", forecast["quantum_advantage_demonstrated"])
print("Scenario objective reduction (EUR):", schedule["scenario_objective_reduction_eur"])
print("Forecast regret versus perfect foresight (EUR):", schedule["forecast_regret_eur"])
print("Research handoff:", result["reports"]["handoff"]["recommendation"])
print("Primary references:", [r["url"] for r in quantum_context()["references"]])
plt.show()
