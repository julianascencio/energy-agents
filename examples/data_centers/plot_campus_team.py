"""
Six team functions carry campus design gaps through delivery
===============================================================

Seventeen generic advisory specialists reuse fourteen existing roles and add
campus design, hall/site planning and facilities development. Inputs are synthetic;
the default planners are scripted, with no live LLM, CAD or simulator execution.
Resolving arithmetic gaps does not establish design approval or service readiness.
"""

from copy import deepcopy

import matplotlib.pyplot as plt

from energy_agents.campus import campus_reference_case, run_campus_team
from energy_agents.data_center import screen_campus_layout, screen_design

case = campus_reference_case()
revised = deepcopy(case)
revised['grid_mw'] = 26
revised['layout']['rack_slots_per_hall'] = 100
results = [run_campus_team(c) for c in (case, revised)]
assert all(r['success'] and not r['readiness']['ready_for_service'] for r in results)

for label, result in zip(('Initial concept', 'Revised assumptions'), results):
    issues = result['readiness']['issues']
    print(label, ':', len(result['results']), 'completed protocols;',
          sum(i['kind'] == 'capacity_shortfall' for i in issues),
          'role-owned capacity findings;',
          sum(i['kind'] == 'missing_document_reference' for i in issues),
          'missing-reference findings; design approved:', result['design_approved'])

fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), layout='constrained')
labels = ['Initial', 'Revised']
colors = ['#bf5145', '#287b8e']
grid = [screen_design(c)['grid_headroom_mw'] for c in (case, revised)]
slots = [screen_campus_layout(c)['layout_headroom_racks'] for c in (case, revised)]
gaps = [sum(i['kind'] == 'missing_document_reference' for i in r['readiness']['issues'])
        for r in results]
for ax, values, title, unit in zip(axes, [grid, slots, gaps],
                                  ['Utility margin', 'Hall layout margin', 'Evidence still missing'],
                                  ['MW', 'Rack slots', 'Role-owned reference gaps']):
    bars = ax.bar(labels, values, color=colors)
    ax.bar_label(bars, padding=4, fmt='%g')
    ax.axhline(0, color='#263649', linewidth=0.8)
    ax.set(title=title, ylabel=unit)
    span = max(abs(v) for v in values) or 1
    ax.set_ylim(min(0, min(values)) - 0.2 * span, max(0, max(values)) + 0.25 * span)
fig.suptitle('Synthetic 20 MW campus | Six functions, 17 advisory specialists')
plt.show()
