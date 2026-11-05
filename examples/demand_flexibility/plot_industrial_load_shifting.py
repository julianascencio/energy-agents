"""Industrial solar: shift batches, preserve output
================================================

Synthetic advisory case inspired by the IEA Spain review of 5 November 2026.
Production is unchanged; all prices, solar and site inputs are illustrative.
Lost export revenue and one-off rescheduling fees are included. No annual savings,
emissions reductions, live LLM advantage or automated dispatch are asserted.
See :doc:`the business case </industrial_flexibility>` for provenance and limits.
"""

import matplotlib.pyplot as plt

from energy_agents.flexibility import reference_case, run_flexibility_agent

case = reference_case()
report = run_flexibility_agent(case)["result"]
print(f"Daily net saving: EUR {report['net_savings_eur']:,.0f}")
print("Proposed starts (UTC hour):", report["proposed"]["starts"])
fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
for key, label in (("baseline", "Baseline"), ("proposed", "Proposed")):
    axes[0].step(range(24), report[key]["load_mw"], where="post", label=label)
axes[0].plot(range(24), case["solar_mw"], label="On-site solar", color="goldenrod")
axes[0].set(xlabel="UTC hour", ylabel="MW", title="Same production, different timing")
axes[0].legend()
labels = ["Baseline net bill", "Proposed net bill", "Rescheduling fees", "Net saving"]
values = [
    report["baseline"]["total_cost_eur"],
    report["proposed"]["total_cost_eur"] - report["proposed"]["shift_cost_eur"],
    report["proposed"]["shift_cost_eur"],
    report["net_savings_eur"],
]
axes[1].barh(labels, values, color=["slategray", "teal", "orange", "seagreen"])
axes[1].set(xlabel="EUR / synthetic day", title="Electricity cost includes export credits")
plt.show()
