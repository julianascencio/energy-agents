"""
Non-firm service: value the interruptions before valuing the discount
==========================================================================================

ISO-NE's 13 November 2026 proposal motivates an advisory contract screen.
ALL operating and financial inputs below are synthetic. The proposal is not an
effective tariff; the example establishes neither eligibility nor dispatch rights.
"""

from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.nonfirm import reference_case, run_workflow, screen_nonfirm

case = reference_case()
r = screen_nonfirm(case)
assert run_workflow(case)["results"]["finance"]["report"] == r
print("SYNTHETIC real USD; 10 years, 8%; proposal scenario, not approved tariff")
print("Period | Trigger | Curtailed MWh | Lost contribution USD | Avoided energy USD")
for row in r["periods"]:
    print(
        " | ".join(
            str(row[k])
            for k in (
                "period",
                "triggered",
                "curtailed_mwh",
                "lost_contribution_usd",
                "avoided_energy_cost_usd",
            )
        )
    )
for k in (
    "events",
    "annual_net_benefit_usd",
    "incremental_npv_usd",
    "break_even_annual_avoided_firm_cost_usd",
):
    print(k, r[k])
print("Unresolved:", r["evidence_gaps"])
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
labels = [
    "Assumed firm\ncost avoided",
    "Electricity\navoided",
    "Business\nloss",
    "Restart",
    "Flex O&M",
]
values = [
    case["assumptions"]["annual_avoided_firm_cost_usd"],
    r["annual"]["avoided_energy_cost_usd"],
    -r["annual"]["lost_contribution_usd"],
    -r["annual"]["restart_cost_usd"],
    -case["assumptions"]["annual_flex_opex_usd"],
]
axes[0].bar(
    labels, [v / 1e6 for v in values], color=["#278268" if v > 0 else "#bc594c" for v in values]
)
axes[0].set(ylabel="USD millions/year", title="Synthetic annual contribution = $0.58m")
axes[0].tick_params(axis="x", labelsize=8)
for margin in (300, 500, 800):
    hours = list(range(0, 481, 20))
    npvs = []
    for h in hours:
        c = deepcopy(case)
        c["assumptions"]["lost_contribution_usd_mwh"] = margin
        c["periods"] = [{"hours": 8760 - h, "price_usd_mwh": 70}]
        if h:
            c["periods"] += [{"hours": h, "price_usd_mwh": 400}]
        npvs.append(screen_nonfirm(c)["incremental_npv_usd"] / 1e6)
    axes[1].plot(hours, npvs, label=f"Lost contribution ${margin}/MWh")
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set(
    xlabel="One continuous interruption (hours/year)",
    ylabel="Incremental NPV (USD millions)",
    title="Synthetic duration / contribution stress",
)
axes[1].legend(fontsize=7)
fig.tight_layout()
