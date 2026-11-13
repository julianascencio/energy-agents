"""
Storage bid: stage spending without assuming award revenue
================================================================================

Synthetic development-budget decision inspired by NYSERDA's 12 November 2026
solicitation. This compares three spend strategies, not actual project returns.
No bid is an explicit zero-value alternative. Probabilities are assumptions.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.bid import reference_case, run_workflow, screen_bid

case = reference_case()
report = screen_bid(case)
assert run_workflow(case)['results']['finance']['report'] == report
print('SYNTHETIC USD at decision date; no spending authorized')
print('Strategy | Expected net value | Expected spend | Worst-case loss')
for name, row in report['strategies'].items():
    print(f"{name} | {row['expected_net_value_usd']:,.2f} | "
          f"{row['expected_spend_usd']:,.2f} | {row['worst_case_loss_usd']:,.2f}")
print('Unresolved evidence:', report['evidence_gaps'])
fig, ax = plt.subplots(figsize=(8, 4.8))
for haircut in (0, .1, .3):
    values = []
    probabilities = [i/20 for i in range(21)]
    for p in probabilities:
        c = deepcopy(case)
        c['assumptions'].update(qualification_probability=p,
                                staging_award_probability_haircut=haircut)
        values.append(screen_bid(c)['staged_incremental_expected_value_usd']/1000)
    ax.plot(probabilities, values, label=f'{haircut:.0%} relative award-probability haircut')
ax.axhline(0, color='black', linewidth=.8)
ax.set(xlabel='Assumed qualification probability',
       ylabel='Staged minus upfront expected value (USD thousands)',
       title='Synthetic bid preparation: staging can destroy value')
ax.legend(fontsize=8)
fig.tight_layout()
