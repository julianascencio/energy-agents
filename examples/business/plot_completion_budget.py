"""
Completing a battery project after contractor termination
====================================================================================================

Yukon Energy's 23 November 2026 announcement motivates an owner/finance workflow.
ALL project, quote, service and funding inputs below are SYNTHETIC. These are not
Whitehorse costs or performance estimates. See :doc:`/completion_budget` for the
source, equations and assumptions. The baseline is a replacement EPC; the
intervention is owner-managed completion with equivalent assumed work scope.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.recovery import reference_case, run_workflow, screen_recovery

case = reference_case()
report = screen_recovery(case)
workflow = run_workflow(case)
assert workflow['success'] and workflow['results']['finance']['report'] == report
print('SYNTHETIC CAD; 12 months; nominal, undiscounted, before tax')
print('Scenario | plan | gross completion cost | budget headroom | peak / end funding CAD')
for comparison in report['comparisons']:
    for name, plan in comparison['plans'].items():
        print(comparison['scenario'], '|', name, '|', plan['gross_forecast_at_completion_cad'],
              '|', plan['budget_headroom_cad'], '|', plan['peak_new_funding_cad'], '/',
              plan['terminal_new_funding_cad'])
    print('Conditional cost reduction CAD:', comparison['conditional_cost_reduction_cad'])
print('Owner quote uplift at equal prospective cost:',
      report['algebraic_owner_quote_uplift_at_cost_parity'])
print('Direct/scripted parity: True. No LLM run; tokens, cost and latency unknown.')
print('Disputed CAD2m damages excluded; grant does not reduce gross budget.')

fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
base = report['comparisons'][0]['plans']
labels = ['Replacement EPC', 'Owner prime']
for key, label, bottom in [
    ('sunk', 'Already paid', [0, 0]),
    ('unpaid', 'Certified unpaid', [24, 24]),
    ('new_quote_cost_cad', 'New remaining-work quotes', [26, 26]),
]:
    values = [24, 24] if key == 'sunk' else [2, 2] if key == 'unpaid' else [
        p[key]/1e6 for p in base.values()]
    axes[0].bar(labels, values, bottom=bottom, label=label)
axes[0].axhline(case['budget_cad']/1e6, color='black', linestyle='--', label='Gross budget')
axes[0].set(ylabel='Gross project cost (CAD millions)', title='Budget is separate from funding')
axes[0].legend(fontsize=7)
for name, p in base.items():
    axes[1].step(range(1,13), [r['funding_before_receipts_cad']/1e6 for r in p['monthly']],
                 where='mid',label=name.replace('_',' '))
axes[1].axhline(case['funding_limit_cad']/1e6, color='black', linestyle='--', label='Funding limit')
axes[1].set(xlabel='Month (outflows before receipts)', ylabel='New funding (CAD millions)',
            title='Peak funding exceeds closing balance')
axes[1].legend(fontsize=7)
uplifts = [i/100 for i in range(31)]
savings = []
for uplift in uplifts:
    changed = deepcopy(case)
    changed['scenarios'][0]['owner_quote_uplift'] = uplift
    savings.append(screen_recovery(changed)['comparisons'][0]['conditional_cost_reduction_cad']/1e6)
axes[2].plot([100*x for x in uplifts], savings)
axes[2].axhline(0, color='black', linewidth=1)
axes[2].axvline(100*report['algebraic_owner_quote_uplift_at_cost_parity'],
                color='grey', linestyle=':')
axes[2].set(xlabel='Owner quote uplift (%)', ylabel='Conditional reduction (CAD millions)',
            title='Scope-equivalent quote sensitivity')
fig.suptitle('Synthetic completion screen — no procurement, legal or technical approval')
fig.tight_layout()
