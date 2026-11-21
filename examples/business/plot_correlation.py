"""
Spanish data-centre hourly correlation: price the shaping decision
=====================================================================

SYNTHETIC February 2027 scenario, not an official bill or compliance finding.
The 21 November BOE publication motivates a standard-path cost screen.
See :doc:`/correlation_cost` for rules, assumptions, boundaries and reproduction.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.correlation import reference_case, run_workflow, screen_correlation

case = reference_case()
report = screen_correlation(case)
workflow = run_workflow(case)
assert workflow['success'] and workflow['results']['finance']['report'] == report
print('SYNTHETIC: EUR, February 2027, 672 hours, 20 MW; no realised savings')
print('Scenario | deviation % | rate EUR/MWh | compensation EUR | premium EUR | total relevant EUR')
for row in report['scenarios']:
    print(row['scenario'], row['mean_hourly_deviation_percent'], row['rate_eur_mwh'],
          row['modelled_compensation_eur'], row['topup_premium_eur'], row['relevant_cost_eur'])
print('Net modelled cost reduction EUR:', report['net_cost_reduction_eur'])
print('Break-even shaping quote EUR/MWh:', report['break_even_topup_eur_mwh'])
print('Direct/scripted parity: True; LLM not run; cost/latency/tokens: unknown')

fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
x = range(24)
base = [r['backing_mwh'] for r in case['hours'][:24]]
shaped = [r['backing_mwh']+r['topup_mwh'] for r in case['hours'][:24]]
axes[0].step(x, base, where='mid', label='Baseline backing')
axes[0].step(x, shaped, where='mid', label='With shaping')
axes[0].axhline(16, linestyle=':', color='black', label='80% of 20 MW')
axes[0].set(xlabel='Hour in synthetic day', ylabel='Backing (MWh per hour)', title='Monthly 80% hides gaps')
axes[0].legend(fontsize=8)
bottom = [0, 0]
for key, label in [('modelled_compensation_eur', 'Correlation exposure'),
                   ('topup_premium_eur', 'Shaping premium'), ('implementation_eur', 'Implementation')]:
    values = [r[key]/1000 for r in report['scenarios']]
    axes[1].bar(['Baseline', 'Shaped'], values, bottom=bottom, label=label)
    bottom = [a+b for a, b in zip(bottom, values, strict=True)]
axes[1].set(ylabel='Relevant monthly cost (thousand EUR)', title='Conditional cost reduction')
axes[1].legend(fontsize=8)
quotes = range(0, 81, 5)
for fraction in (.5, 1):
    values = []
    for quote in quotes:
        c = deepcopy(case)
        c['topup_eur_mwh'] = quote
        for h in c['hours']:
            h['topup_mwh'] *= fraction
        values.append(screen_correlation(c)['net_cost_reduction_eur']/1000)
    axes[2].plot(list(quotes), values, label=f'{fraction:.0%} of proposed top-up')
axes[2].axhline(0, color='black', linewidth=.8)
axes[2].set(xlabel='All-in incremental premium (EUR/MWh)',
            ylabel='Net cost reduction (thousand EUR)', title='Quote and delivery uncertainty')
axes[2].legend(fontsize=8)
fig.suptitle('Synthetic standard-path screen — assumed eligibility; no compliance certification')
fig.tight_layout()
