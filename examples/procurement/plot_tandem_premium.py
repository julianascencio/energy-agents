"""
Tandem modules: what premium can a constrained roof justify?
====================================================================================================

Synthetic fixed-area tender inspired by the 10 November 2026 Heliene/Caelux
announcement. Manufacturer claims are not field-validated annual yields.
Hourly clipping was executed with pinned EDI code; the default example replays
its packaged annual energy outputs without network or an EDI installation.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.tandem import reference_case, run_workflow, screen_premium

case = reference_case()
run = run_workflow(case)
assert run['success']
report = run['results']['finance']['report']
assert report == screen_premium(case)  # deterministic baseline parity, not LLM advantage
print('SYNTHETIC, USD, 20 years; no purchase approval or realized savings')
for name, r in report['scenarios'].items():
    print(f"{name}: ceiling ${r['premium_ceiling_usd']:,.0f}; NPV ${r['incremental_npv_usd']:,.0f}")

fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
for name, values in case['energy']['alternatives'].items():
    axes[0].plot(range(1, 21), values, label=name.replace('_', ' '))
axes[0].plot(range(1, 21), case['energy']['baseline_mwh'], 'k--', label='conventional baseline')
axes[0].set(xlabel='Operating year', ylabel='Delivered MWh/year', title='Synthetic energy after clipping')
axes[0].legend(fontsize=8)
prices = [0, 50, 100, 150, 200]
for name in report['scenarios']:
    npvs = []
    for price in prices:
        c = deepcopy(case)
        c['value_usd_mwh'] = price
        npvs.append(screen_premium(c)['scenarios'][name]['incremental_npv_usd'] / 1000)
    axes[1].plot(prices, npvs, label=name.replace('_', ' '))
axes[1].axhline(0, color='black', linestyle='--')
axes[1].set(xlabel='Energy value (constant USD/MWh)', ylabel='Incremental NPV (thousand USD)',
            title='USD 50,000 premium + USD 500/year extra O&M')
fig.suptitle('Tandem tender screen — synthetic scenarios, not manufacturer economics')
plt.show()
