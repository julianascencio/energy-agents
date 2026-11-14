"""
Data-centre heat reuse: useful heat must meet demand
==========================================================================================

Infomaniak's 13 November 2026 Bulle announcement motivates this district-heating
investment screen. All operating and economic inputs are SYNTHETIC. No actual
project return, measured heat delivery or emissions reduction is inferred.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.heat_reuse import reference_case, run_workflow, screen_heat_reuse

case = reference_case()
r = screen_heat_reuse(case)
workflow = run_workflow(case)
assert workflow['success'] and workflow['results']['finance']['report'] == r
print('SYNTHETIC real CHF, 15 years, 6% discount; no investment authorized')
print('Period | Demand MWh | Delivered MWh | Pump electricity MWh | Bypassed source MWh')
for row in r['periods']:
    print(row['id'], '|', ' | '.join(f'{row[k]:,.2f}' for k in
        ('demand_mwh','delivered_mwh','pump_electricity_mwh','bypassed_source_mwh')))
for key in ('baseline_annual_supply_cost_chf','intervention_annual_supply_cost_chf',
            'annual_net_savings_chf','incremental_npv_chf','break_even_avoided_cost_chf_mwh'):
    print(f'{key}: {r[key]:,.2f}')
print('Annual energy-only ceiling MWh:',r['annual_matching_ceiling_mwh'])
print('Period-matched delivered MWh:',r['annual_energy']['delivered_mwh'])
print('Workflow/direct baseline parity:',True,'; live LLM executed:',r['llm']['executed'])
print('Unresolved evidence:',r['evidence_gaps'])

fig,axes = plt.subplots(1,2,figsize=(12,4.7))
months = range(1,13)
axes[0].plot(months,[p['demand_mwh']/1000 for p in r['periods']],marker='o',label='Demand')
axes[0].plot(months,[p['potential_delivered_mwh']/1000 for p in r['periods']],
             linestyle='--',label='Available after network losses')
axes[0].bar(months,[p['delivered_mwh']/1000 for p in r['periods']],alpha=.55,label='Delivered')
axes[0].set(xlabel='Month',ylabel='Heat (GWh)',title='Synthetic seasonal matching',xticks=[1,3,5,7,9,12])
axes[0].legend(fontsize=8)
prices = list(range(40,241,10))
for scale in (.5,1,1.5):
    values=[]
    for price in prices:
        c = deepcopy(case)
        c['assumptions']['electricity_chf_mwh'] = price
        for p in c['periods']:
            p['demand_mw'] *= scale
        values.append(screen_heat_reuse(c)['incremental_npv_chf']/1e6)
    axes[1].plot(prices,values,label=f'{scale:.0%} reference heat demand')
    print(f'Demand {scale:.0%}; NPV at electricity 120 CHF/MWh: {values[8]:.6f} million CHF')
axes[1].axhline(0,color='black',linewidth=.8)
axes[1].axvline(120,color='gray',linestyle=':')
axes[1].set(xlabel='Assumed electricity price (CHF/MWh)',ylabel='Incremental NPV (CHF millions)',
            title='Synthetic cost and demand sensitivity')
axes[1].legend(fontsize=8)
fig.tight_layout()
