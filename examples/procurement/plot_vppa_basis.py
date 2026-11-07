"""
Equal energy volumes do not remove VPPA basis risk
====================================================================================================

Synthetic 24-hour screening case in four six-hour blocks. The news motivates
procurement diligence; none of these prices or profiles are Ahold contract data.
The scripted workflow matches direct deterministic calculation; no LLM run.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.vppa import reconcile_vppa, reference_case, run_vppa_workflow

case = reference_case()
report = reconcile_vppa(case)
run = run_vppa_workflow(case)
assert run['success'] and run['results']['finance']['report'] == report
print('SYNTHETIC EUR per example day; all alternatives total 400 MWh')
print('Unhedged:', report['unhedged_cost_eur'])
for name, row in report['alternatives'].items():
    print(name, 'receipt:', row['buyer_receipt_eur'], 'net cost:', row['net_cost_eur'])
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')
names = list(case['mixes'])
axes[0].bar(names, [report['alternatives'][n]['net_cost_eur'] / 1000 for n in names])
axes[0].axhline(report['unhedged_cost_eur'] / 1000, color='black', label='Unhedged baseline')
axes[0].axhline(case['budget_eur'] / 1000, color='red', linestyle='--', label='Assumed budget')
axes[0].set(ylabel='Net buyer cost (EUR thousand/day)', title='Equal 400 MWh, different settlement')
axes[0].legend()
for name in names:
    values = []
    shifts = [-20, 0, 20, 40, 60]
    for shift in shifts:
        stress = deepcopy(case)
        for row in stress['intervals']:
            row['reference_price_eur_mwh'] += shift
        values.append(reconcile_vppa(stress)['alternatives'][name]['net_cost_eur'] / 1000)
    axes[1].plot(shifts, values, 'o-', label=name)
axes[1].axhline(32, color='black', linestyle='--', label='Unhedged')
axes[1].set(xlabel='Reference-market price shock (EUR/MWh)',
            ylabel='Net buyer cost (EUR thousand/day)', title='Synthetic basis sensitivity; load price fixed')
axes[1].legend()
plt.show()
