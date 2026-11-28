"""
Comparing equity and revenue-sharing cash flows
====================================================================================================

CIS Tender 12 motivates this advisory workflow. ALL financial inputs are
SYNTHETIC; no community agreement or tender qualification is established.
See :doc:`/benefit_sharing` for the source, assumptions and equations.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.sharing import reference_case, run_workflow, screen_sharing

case = reference_case()
report = screen_sharing(case)
workflow = run_workflow(case)
assert workflow['success'] and workflow['results']['finance']['report'] == report
print('SYNTHETIC nominal AUD; 20 years, year-end, 8% common discount rate')
print('Plan | recipient NPV | sponsor incremental cost PV | operating funding gaps')
for name, plan in report['plans'].items():
    print(name, '|', plan['recipient_npv_aud'], '|', plan['sponsor_incremental_cost_pv_aud'],
          '|', plan['total_operating_funding_gap_aud'])
print('Algebraic recipient-NPV parity revenue fraction:',
      report['revenue_fraction_at_recipient_npv_parity'])
print('Qualification: not determined. Scripted/direct parity: True. No LLM runs.')

fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
for name, p in report['plans'].items():
    axes[0].plot([r['year'] for r in p['annual']],
                 [r['recipient_total_aud']/1e6 for r in p['annual']],
                 marker='.',label=name.replace('_',' '))
axes[0].set(xlabel='Year',ylabel='Recipient receipts (AUD millions)',
            title='Equity includes terminal proceeds')
axes[0].legend(fontsize=8)
for i, (name,p) in enumerate(report['plans'].items()):
    axes[1].bar(i-.18,p['recipient_npv_aud']/1e6,.36,color='teal',
                label='Recipient NPV' if i == 0 else None)
    axes[1].bar(i+.18,p['sponsor_incremental_cost_pv_aud']/1e6,.36,color='orange',
                label='Sponsor cost PV' if i == 0 else None)
axes[1].set(xticks=[0,1],xticklabels=['Gifted equity','Revenue share'],
            ylabel='AUD millions',title='Administration changes sponsor cost')
axes[1].legend(fontsize=8)
for rate in (.04,.08,.12):
    fractions=[]
    for end in range(5,21):
        changed=deepcopy(case)
        changed['revenue_share']['end_year']=end
        changed['discount_rate']=rate
        fractions.append(100*screen_sharing(changed)['revenue_fraction_at_recipient_npv_parity'])
    axes[2].plot(range(5,21),fractions,label=f'{rate:.0%} discount')
axes[2].set(xlabel='Last revenue-sharing year',ylabel='Revenue fraction (%)',
            title='Equal recipient NPV is timing-sensitive')
axes[2].legend(fontsize=8)
fig.suptitle('Synthetic benefit sharing — no regulatory equivalence or consent finding')
fig.tight_layout()

stress=deepcopy(case)
for row in stress['annual']:
    row['gross_revenue_aud'] *= .7
    row['distributable_cash_aud'] = 100000
stressed=screen_sharing(stress)
print('Stress: 30% less revenue; AUD0.1m/year distributable cash (assumptions)')
for name,p in stressed['plans'].items():
    print(name, 'recipient NPV AUD',p['recipient_npv_aud'],
          'total operating funding gaps AUD',p['total_operating_funding_gap_aud'])
# Save only when run directly; Sphinx Gallery captures figures itself.
if __name__ == '__main__':
    from pathlib import Path
    Path('outputs/sharing').mkdir(parents=True,exist_ok=True)
    fig.savefig('outputs/sharing/comparison.png',dpi=150)
