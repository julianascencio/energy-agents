"""
Firm power procurement: 90% energy is not 90% fully served hours
================================================================================

The November 2026 Ember/GWEC study motivates an industrial buyer's delivery audit.
These deliberately constructed profiles and all costs are SYNTHETIC. They are
not the atlas data, a reconstruction of its economics, or measured wind benefit.
See :doc:`/firm_supply` for evidence, equations, prompts and reproduction.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.firm_supply import reference_case, run_workflow, screen_firm_supply

case = reference_case()
report = screen_firm_supply(case)
workflow = run_workflow(case)
assert workflow['success'] and workflow['results']['finance']['report'] == report
print('SYNTHETIC: 168 hours, 10 MW demand, 2 MW backup; USD, no annualization')
print('Offer | Renewable MWh | Fully served hours before/after backup | Residual MWh | Cash USD | Economic USD')
for row in report['offers']:
    print(row['offer_id'], '|', row['renewable_served_mwh'], '|',
          row['fully_served_hours_without_backup'], '/', row['fully_served_hours_with_backup'], '|',
          row['residual_unserved_mwh'], '|', row['cash_cost_usd'], '|', row['economic_cost_usd'])
print('Break-even lost contribution USD/MWh:',report['offers'][1]['break_even_lost_contribution_usd_mwh'])
print('Direct/scripted parity: True; live LLM run: False; LLM cost/latency/tokens: unknown')

fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
x = list(range(24))
for offer in case['offers']:
    axes[0].step(x, [10-v for v in offer['delivered_mw'][:24]], where='post', label=offer['id'])
axes[0].axhline(2, color='black', linestyle=':', label='Backup limit')
axes[0].set(xlabel='Hour in synthetic day', ylabel='Residual need before backup (MW)',
            title='Same energy coverage, different gaps')
axes[0].legend(fontsize=7)
bottom = [0, 0]
for key, label in [('window_fee_usd','Offer fee'), ('backup_capacity_cost_usd','Backup capacity'),
                   ('backup_variable_cost_usd','Backup energy'),
                   ('modelled_lost_contribution_usd','Scenario lost contribution')]:
    values = [r[key]/1000 for r in report['offers']]
    axes[1].bar([0, 1], values, bottom=bottom, label=label)
    bottom = [a+b for a,b in zip(bottom,values,strict=True)]
axes[1].set(xticks=[0,1], xticklabels=['Concentrated','Distributed'], ylabel='USD thousands / 7 days',
            title='Cash costs and opportunity loss')
axes[1].legend(fontsize=7)
loss_values = list(range(0, 2001, 100))
for capacity in [0, 1, 2, 4]:
    savings = []
    for loss in loss_values:
        c = deepcopy(case)
        c['assumptions'].update(backup_mw=capacity, lost_contribution_usd_mwh=loss)
        savings.append(screen_firm_supply(c)['offers'][1]['economic_cost_reduction_vs_baseline_usd']/1000)
    axes[2].plot(loss_values,savings,label=f'{capacity} MW backup')
axes[2].axhline(0,color='black',linewidth=.8)
axes[2].set(xlabel='Assumed lost contribution (USD/MWh)', ylabel='Distributed-offer cost reduction (kUSD)',
            title='Conclusion depends on backup and loss')
axes[2].legend(fontsize=7)
fig.suptitle('Synthetic decision screen — no realised savings or technology advantage')
fig.tight_layout()
