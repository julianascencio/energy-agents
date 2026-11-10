"""
CEN Chile: a real solar operations review
==================================================

Seven public CEN daily reports, 2–8 November 2026, supply 583 comparable
plant-days across 84 source PFV names. These are downloaded observations,
not synthetic inputs. Replay is offline; the EDI connector can refresh the
source separately. Dispatch schedule is not unconstrained technical production.
"""

from math import fsum

import matplotlib.pyplot as plt

from energy_agents.operations.cen import CENOperationsService, load_cen_snapshot

snapshot = load_cen_snapshot()
service = CENOperationsService(snapshot)
result = service.review_portfolio()
reports = sorted(snapshot["reports"], key=lambda r: r["report_date"])
days = [r["report_date"][8:] + " Nov" for r in reports]
scheduled = [fsum(r["scheduled_mwh"] for r in p["generation"]) / 1000 for p in reports]
actual = [fsum(r["actual_mwh"] for r in p["generation"]) / 1000 for p in reports]
leaders = result["investigation_queue"][:6][::-1]

fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), layout="constrained")
fig.set_facecolor("#f3f7f8")
fig.suptitle("CEN Chile | Solar operations · 2–8 November 2026", fontsize=17, fontweight="bold")
axes[0].plot(days, scheduled, "o--", color="#647480", label="CEN dispatch schedule")
axes[0].plot(days, actual, "o-", color="#087e80", linewidth=2.5, label="CEN actual generation")
axes[0].set(title="Selected PFV fleet · 83–84 reported names/day", ylabel="Daily energy (GWh)")
axes[0].legend(frameon=False, loc="lower left")
axes[0].grid(axis="y", alpha=0.2)
values = [a["shortfall_mwh"] / 1000 for a in leaders]
names = [a["asset_id"].removeprefix("PFV ") for a in leaders]
bars = axes[1].barh(names, values, color="#087e80", height=0.6)
axes[1].bar_label(bars, labels=[f"{v:.2f}" for v in values], padding=6, fontsize=10)
axes[1].set(
    title="Schedule investigations · complete 7-day records",
    xlabel="Sum of daily positive shortfalls (GWh)",
    xlim=(0, max(values) * 1.18),
)
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor("white")
    ax.tick_params(labelsize=10)
fig.supxlabel(
    "296.34 GWh actual / 322.69 GWh scheduled · Revenue impact unknown\n"
    "Schedule deviations are investigation signals, not attributed or recoverable losses.",
    fontsize=10,
)
plt.show()

# %%
# A schedule-only screen would miss Huatacondo: both totals are zero. CEN's
# separate availability notice reports 0% on 8 November (SDCF 2026100475).
# The workflow flags it for status confirmation without inventing lost MWh.
huatacondo = service.review_asset("PFV Huatacondo")
print("Huatacondo:", huatacondo["state"], huatacondo["latest_notices"])
draft = service.draft_work_order("PFV Huatacondo", huatacondo["actions"][0]["action_id"])
print("Proposed investigation:", draft["title"], "—", draft["status"])

# %%
# Tirana Solar appears on only two of seven report dates. Missing days are
# retained as missing and the asset is excluded from the complete-window rank.
tirana = service.review_asset("PFV Tirana Solar")
print("Tirana Solar missing dates:", tirana["ledger"]["missing_dates"])
print("Backend executed:", result["backend"])
print("Fleet totals:", result["summary"])
