"""
Preferred equity: capital released is not additional project value
================================================================================

Captona's 10 November 2026 announcement motivates a financing screen for solar
and storage developers. ALL financial inputs below are synthetic, unrelated to
actual transaction terms. Announced portfolio metadata does not scale this model.
"""
from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.business.equity import reference_case, run_workflow, screen_equity

case = reference_case()
r = screen_equity(case)
assert run_workflow(case)['results']['finance']['report'] == r
print('SYNTHETIC nominal USD; after-debt cash; 5 years; no investment authorized')
for key in ('sponsor_initial_cash_saved_usd','common_only_sponsor_npv_usd',
            'preferred_funded_sponsor_npv_usd','preferred_investor_npv_usd',
            'sponsor_incremental_npv_usd','terminal_capital_shortfall_usd'):
    print(f'{key}: {r[key]:,.2f}')
print('Year | Available | Coupon | Arrears | Capital returned | Common')
for row in r['annual']:
    print(' | '.join(f'{row[k]:,.0f}' for k in ('year','available_usd','coupon_paid_usd',
        'coupon_arrears_usd','redemption_usd','common_distribution_usd')))
print('Unresolved:', r['evidence_gaps'])
fig, axes = plt.subplots(1,2,figsize=(11,4.5))
years = [x['year'] for x in r['annual']]
coupon = [x['coupon_paid_usd']/1e6 for x in r['annual']]
redemption = [x['redemption_usd']/1e6 for x in r['annual']]
common = [x['common_distribution_usd']/1e6 for x in r['annual']]
axes[0].bar(years,coupon,label='Preferred coupon')
axes[0].bar(years,redemption,bottom=coupon,label='Preferred capital')
axes[0].bar(years,common,bottom=[a+b for a,b in zip(coupon,redemption,strict=True)],label='Common')
axes[0].set(xlabel='Year',ylabel='USD millions',title='Synthetic cash allocation')
axes[0].legend(fontsize=8)
exits = list(range(0,16000001,500000))
for scale in (.25,1):
    values=[]
    for exit_value in exits:
        c = deepcopy(case)
        c['assumptions'].update(terminal_equity_proceeds_usd=exit_value,
            annual_cash_usd=[v*scale for v in case['assumptions']['annual_cash_usd']])
        values.append(screen_equity(c)['sponsor_incremental_npv_usd']/1e6)
    axes[1].plot([v/1e6 for v in exits],values,label=f'{scale:.0%} operating cash')
axes[1].axhline(0,color='black',linewidth=.8)
axes[1].set(xlabel='Assumed after-debt exit proceeds (USD millions)',
            ylabel='Sponsor incremental NPV (USD millions)',title='Value transfer, not project uplift')
axes[1].legend(fontsize=8)
fig.tight_layout()
