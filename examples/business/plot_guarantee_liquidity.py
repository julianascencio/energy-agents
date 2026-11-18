"""
Guarantee collateral: liquidity released is not profit
======================================================

Enlight's 16 November 2026 announcement motivates this advisory treasury screen.
The guarantee estimate is reported; ALL bank terms and risk inputs are synthetic.
No bank quote, grid approval, or realised savings is represented.
"""

from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.guarantee import reference_case, run_workflow, screen_guarantee

c = reference_case()
r = screen_guarantee(c)
assert run_workflow(c)["results"]["finance"]["report"] == r
print("SYNTHETIC terms; NIS; undiscounted two-year horizon")
for name, row in r["offers"].items():
    print(name)
    for k, v in row.items():
        print(" ", k, v)
print("Economic cost reduction:", r["economic_cost_reduction_nis"])
print("Restricted cash released (NOT profit):", r["restricted_cash_released_nis"])
print("Break-even alternative annual fee:", r["alternative_break_even_annual_fee_rate"])
print("Evidence gaps:", r["evidence_gaps"])
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for i, (name, row) in enumerate(r["offers"].items()):
    bottom = 0
    for key, label, color in [
        ("upfront_fees_nis", "Fees", "#c46440"),
        ("opportunity_cost_nis", "Opportunity cost", "#426c97"),
        ("expected_net_call_loss_nis", "Expected net loss", "#9b8a46"),
    ]:
        value = row[key] / 1e6
        axes[0].bar(name, value, bottom=bottom, color=color, label=label if i == 0 else None)
        bottom += value
axes[0].set(ylabel="NIS million / two years", title="Synthetic economic costs (not principal)")
axes[0].legend(fontsize=8)
for fraction in (0.25, 0.5, 1):
    fees = [i / 1000 for i in range(0, 51)]
    costs = []
    for fee in fees:
        x = deepcopy(c)
        x["offers"]["alternative"].update(collateral_fraction=fraction, annual_fee_rate=fee)
        costs.append(screen_guarantee(x)["economic_cost_reduction_nis"] / 1e6)
    axes[1].plot([f * 100 for f in fees], costs, label=f"{fraction:.0%} collateral")
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set(
    xlabel="Alternative annual guarantee fee (%)",
    ylabel="Cost reduction vs baseline (NIS m)",
    title="Synthetic fee / collateral stress",
)
axes[1].legend(fontsize=8)
fig.tight_layout()
