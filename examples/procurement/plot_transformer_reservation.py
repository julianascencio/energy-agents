"""
Reserve a transformer slot or wait for project approval?
====================================================================================================

Synthetic wind-developer scenario motivated by ENTSO-E's 3 November 2026
supply-chain report. The fee, probabilities, delivery dates and operating
contribution are assumptions, not supplier offers or realised benefits.
See :doc:`/transformer_procurement` for sources, contracts and cost boundaries.

Earlier equipment only creates revenue if the site and approval are ready.
The deterministic baseline and fixed three-task workflow use identical tools.
No LLM was executed or superiority claimed.
"""
import matplotlib.pyplot as plt

from energy_agents.business.procurement import (
    cancellation_sensitivity,
    reference_case,
    run_procurement_workflow,
    screen_reservation,
)

case = reference_case()
report = screen_reservation(case)
run = run_procurement_workflow(case)
assert run['success'] and run['results']['finance']['report'] == report
print('SYNTHETIC; incremental EUR NPV versus ordering at approval; 72-month horizon')
print(f"{'Scenario':25} {'p':>6} {'Wait COD':>10} {'Reserve COD':>12} {'NPV EUR':>14}")
for s in report['scenarios']:
    print(f"{s['id']:25} {s['probability']:6.0%} {str(s['wait_cod_month']):>10} "
          f"{str(s['reserve_cod_month']):>12} {s['incremental_npv_eur']:14,.0f}")
print(f"Expected NPV: EUR {report['reserve_expected_npv_eur']:,.2f}")
print(f"Worst loss: EUR {report['reserve_worst_loss_eur']:,.2f}; "
      f"loss probability {report['reserve_loss_probability']:.0%}")
print(f"Economic fee ceiling: EUR {report['break_even_reservation_fee_eur']:,.2f}")
print('Workflow success and deterministic parity:', run['success'], True)
print('LLM cost / latency / tokens: unknown (not run)')

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
values = [s['incremental_npv_eur'] / 1e6 for s in report['scenarios']]
axes[0].bar(['Site ready\n50%', 'Site delayed\n30%', 'Cancelled\n20%'], values,
            color=['#25847b', '#c45b42', '#c45b42'])
axes[0].axhline(0, color='black', linewidth=0.8)
axes[0].axhline(report['reserve_expected_npv_eur'] / 1e6, color='#344c86',
               linestyle='--', label='Probability-weighted expectation')
axes[0].set(ylabel='Incremental NPV (EUR million)', title='Synthetic scenario outcomes')
axes[0].legend(fontsize=8, loc='upper right')
for i, value in enumerate(values):
    axes[0].annotate(f'{value:+.3f}', (i, value), xytext=(0, 5 if value >= 0 else -14),
                     textcoords='offset points', ha='center')
axes[0].set_ylim(-1.2, 3.2)

rows = cancellation_sensitivity(case)
axes[1].plot([r['cancellation_probability'] * 100 for r in rows],
             [r['expected_npv_eur'] / 1e6 for r in rows], 'o-', color='#344c86')
axes[1].axhline(0, color='black', linestyle='--', label='Wait baseline')
axes[1].scatter([20], [report['reserve_expected_npv_eur'] / 1e6], s=70,
                color='#c45b42', zorder=3, label='Example assumption')
axes[1].set(xlabel='Assumed cancellation probability (%)',
            ylabel='Expected incremental NPV (EUR million)',
            title='Conditional site-readiness mix held fixed')
axes[1].legend(fontsize=8)
plt.show()
