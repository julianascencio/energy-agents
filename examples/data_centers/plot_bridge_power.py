"""
Bridge power: is earlier operation worth the cost?
====================================================================================================

SYNTHETIC inputs, not NTT commercial terms. Inspired by the 5 November 2026
NTT/Bloom announcement; see the bridge-power methodology for sources and scope.
Existing orchestrator and finance role match the direct deterministic screen.
No LLM runs, physical operation or field validation are claimed.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.bridge_power import (
    reference_case,
    run_bridge_workflow,
    screen_bridge_power,
)

case = reference_case()
screen = screen_bridge_power(case)
workflow = run_bridge_workflow(case)
assert workflow['success']
assert workflow['results']['finance']['screen'] == screen
print('SYNTHETIC; EUR; nine early operating months; 730 hours per model month')
print('Bridge incremental NPV: EUR {:,.2f}'.format(screen['bridge_incremental_npv_eur']))
print('Wait baseline incremental NPV: EUR 0')
print('Break-even contribution margin: EUR {:.2f}/IT MWh'.format(
    screen['break_even_margin_eur_per_it_mwh']))
print('Month | IT MWh | facility MWh | net cash EUR')
for row in screen['monthly']:
    print(row['month_end'], row['it_mwh'], row['facility_mwh'], row['net_cash_eur'])

margins = [180, 220, 260, 300, 340]
fig, ax = plt.subplots(figsize=(8, 4.5), layout='constrained')
for grid_month in [6, 9, 12]:
    values = []
    for margin in margins:
        stress = deepcopy(case)
        stress['assumptions'].update(grid_month=grid_month, margin_eur_per_it_mwh=margin)
        values.append(screen_bridge_power(stress)['bridge_incremental_npv_eur'] / 1e6)
    ax.plot(margins, values, marker='o', label=f'Grid ready month {grid_month}')
ax.axhline(0, color='black', linewidth=1)
ax.set(xlabel='Contribution before electricity (EUR / IT MWh)',
       ylabel='Incremental NPV versus waiting (EUR million)',
       title='Synthetic bridge-power screen — bridge ready month 3')
ax.legend()
ax.grid(alpha=.2)
plt.show()
