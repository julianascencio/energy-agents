"""
Maintaining four-hour battery capacity over fifteen years
====================================================================================================

The Dominican Republic's November 2026 renewable tender motivates this developer
cost screen. Every project, cost and retention input below is SYNTHETIC, not a
supplier quote or warranty. See :doc:`/battery_augmentation` for source boundaries,
equations and reproduction. The direct calculation is also the scripted workflow's
baseline; no LLM benefit or field performance is claimed.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.augmentation import reference_case, run_workflow, screen_augmentation

case = reference_case()
report = screen_augmentation(case)
workflow = run_workflow(case)
assert workflow['success'] and workflow['results']['finance']['report'] == report
print('SYNTHETIC 20 MW / four-hour event; 15 years; constant-real USD at service start')
print('Scenario | plan | DC additions (year, MWh) | cost PV USD | first failing year')
for comparison in report['comparisons']:
    for plan in comparison['plans']:
        print(comparison['scenario'], '|', plan['plan'], '|',
              [(a['added_at_year'],a['nameplate_mwh_dc']) for a in plan['additions']], '|',
              round(plan['total_cost_pv_usd'],2), '|', plan['first_failing_year'])
    print('Valid conditional cost reduction USD:',comparison['cost_reduction_pv_usd'])
print('Future equipment price multiplier at break-even:',
      report['break_even_future_equipment_price_multiplier'])
print('Direct/scripted parity: True; LLM executed: False; LLM tokens/cost/latency: unknown')

fig, axes = plt.subplots(1,3,figsize=(14,4.6))
for comparison, style in [(report['comparisons'][0],'-'),(report['comparisons'][-1],'--')]:
    for plan, color in zip(comparison['plans'],['tab:blue','tab:orange'],strict=True):
        axes[0].plot(range(1,16),[r['available_ac_energy_mwh'] for r in plan['years']],
                     style, color=color,label=plan['plan']+' / '+comparison['scenario'])
axes[0].axhline(80,color='black',linewidth=1,label='Required single-event energy')
axes[0].set(xlabel='Year end, before next addition',ylabel='Available AC energy (MWh)',
            title='Fixed designs: 2% vs 3% annual fade')
axes[0].legend(fontsize=6)
plans=report['comparisons'][0]['plans']
for key,label,bottom in [('capex_pv_usd','Installed capacity and events',[0,0]),
                        ('opex_pv_usd','Capacity-based O&M',
                         [p['capex_pv_usd']/1e6 for p in plans])]:
    axes[1].bar(['Upfront','Staged'],[p[key]/1e6 for p in plans],bottom=bottom,label=label)
axes[1].set(ylabel='15-year present cost (USD millions)',title='Conditional capacity-cost comparison')
axes[1].legend(fontsize=7)
prices=[.5+i*.1 for i in range(36)]
reductions=[]
for price in prices:
    c=deepcopy(case)
    c['scenarios'][0]['future_price_multiplier']=price
    reductions.append(screen_augmentation(c)['comparisons'][1]['cost_reduction_pv_usd']/1e6)
axes[2].plot(prices,reductions,color='tab:green')
axes[2].axhline(0,color='black',linewidth=1)
axes[2].axvline(report['break_even_future_equipment_price_multiplier'],color='grey',linestyle=':')
axes[2].set(xlabel='Future installed equipment price / base price',
            ylabel='Staged cost reduction (USD millions PV)',title='No assumed future price decline')
fig.suptitle('Synthetic screening only — compatibility, outage and tender eligibility unverified')
fig.tight_layout()
