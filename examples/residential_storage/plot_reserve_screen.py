"""
Household backup reserve versus grid-service revenue
====================================================================================================

SYNTHETIC cohorts and economics inspired by National Grid's 6 November 2026
BackupBattery+ announcement. EDI energy-balance results were executed and saved;
the offline example replays them, validates identities and evaluates economics.
It does not execute EDI or an LLM during the default gallery build.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.reserve import data_file, run_reserve_workflow, screen_event

case, envelope = data_file('case.json'), data_file('envelope.json')
report = screen_event(case, envelope)
run = run_reserve_workflow(case, envelope)
assert run['success'] and run['results']['finance']['screen'] == report
print('SYNTHETIC USD/event; 125 hypothetical homes, three-hour event; no annualization')
print('Reserve h | offer kW | delivered kWh | net USD | nameplate net USD')
for row in report['scenarios']:
    print(*(round(row[k], 2) for k in ('reserve_hours', 'reserve_limited_offer_kw',
                                     'delivered_kwh', 'reserve_net_usd', 'nameplate_net_usd')))
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')
hours = [r['reserve_hours'] for r in report['scenarios']]
axes[0].plot(hours, [r['reserve_limited_offer_kw'] for r in report['scenarios']],
             'o-', label='Reserve-limited offer')
axes[0].axhline(550, color='darkred', linestyle='--', label='Naive nameplate offer')
axes[0].set(xlabel='Critical-load backup reserve (hours)', ylabel='Flat three-hour offer (kW)',
            title='Synthetic fleet: usable service capacity')
axes[0].legend()
for penalty in [0, 1, 3]:
    stressed = deepcopy(case)
    stressed['economics']['shortfall_usd_per_kwh'] = penalty
    result = screen_event(stressed, envelope)
    axes[1].plot(hours, [r['nameplate_net_usd'] for r in result['scenarios']], 'o--',
                 label=f'Naive; shortfall USD {penalty}/kWh')
axes[1].plot(hours, [r['reserve_net_usd'] for r in report['scenarios']], 'o-',
             color='black', label='Reserve-limited')
axes[1].axhline(0, color='grey', linewidth=1)
axes[1].set(xlabel='Critical-load backup reserve (hours)', ylabel='Net contribution (USD/event)',
            title='Synthetic shortfall-price sensitivity')
axes[1].legend(fontsize=8)
plt.show()
