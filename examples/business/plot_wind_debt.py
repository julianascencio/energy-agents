"""
Wind financing: commitments are not debt capacity
====================================================================================================

Synthetic operating-period debt screen inspired by RWE's 11 November 2026
Vanguard financing announcement. The observed facility amounts are context,
not drawn debt. No lender term sheet or actual project economics are modelled.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.debt import reference_case, run_workflow, screen_debt

case = reference_case()
run = run_workflow(case)
assert run['success']
report = run['results']['finance']['report']
assert report == screen_debt(case)
print('SYNTHETIC: constant-real GBP; 20 operating years; no financing approval')
print('Scenario | DSCR | supported debt GBP bn | debt reduction GBP bn')
for name, r in report['scenarios'].items():
    print(f"{name} | {r['dscr']:.3f} | {r['supported_debt_gbp']/1e9:.3f} | "
          f"{r['debt_reduction_gbp']/1e9:.3f}")
print(f"Break-even capacity factor: {report['break_even_capacity_factor']:.2%}")
fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
names = list(report['scenarios'])
axes[0].bar(names, [report['scenarios'][n]['dscr'] for n in names])
axes[0].axhline(1.3, color='red', linestyle='--', label='Assumed minimum 1.3')
axes[0].set(ylabel='Debt-service coverage ratio', title='GBP 6.5bn proposed debt')
axes[0].legend()
for rate in [.03, .05, .07]:
    values = []
    cfs = [.30, .35, .40, .45, .50, .55, .60]
    for cf in cfs:
        c = deepcopy(case)
        c['assumptions'].update(real_interest_rate=rate, capacity_factors={'s':cf})
        values.append(screen_debt(c)['scenarios']['s']['supported_debt_gbp']/1e9)
    axes[1].plot(cfs, values, label=f'{rate:.0%} real interest')
axes[1].axhline(6.5, color='black', linestyle='--', label='Proposed debt')
axes[1].set(xlabel='Net capacity factor', ylabel='Supported debt (GBP bn)',
            title='Synthetic resource and rate sensitivity')
axes[1].legend()
fig.suptitle('Advisory wind debt screen — synthetic assumptions')
plt.show()
