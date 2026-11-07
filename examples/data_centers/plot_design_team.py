"""
Fourteen specialists review a 20 MW AI data center concept
=====================================================================

Synthetic assumptions, deterministic planners and advisory reports. No actual
Microsoft design, LLM evaluation, CAD execution or engineering approval is implied.
The 24 MW utility offer falls short of the 26 MW peak facility planning estimate.
"""
import matplotlib.pyplot as plt

from energy_agents.data_center import reference_case, run_design_team, screen_design

case = reference_case()
result = run_design_team(case)
screen = screen_design(case)
assert result['success']
print('Completed specialist protocols:', len(result['results']))
print('Design approved:', result['design_approved'])
print('Synthetic annual facility energy (MWh):', screen['annual_facility_mwh'])
print('Synthetic site water (m3/year):', screen['annual_site_water_m3'])
print('Purely illustrative liquid mass flow (kg/s):', screen['liquid_flow_kg_s'])

fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout='constrained')
labels = ['Grid / facility', 'UPS / IT', 'Air cooling / IT heat', 'Liquid cooling / IT heat']
headroom = [screen[f'{name}_headroom_mw'] for name in ('grid', 'ups', 'air', 'liquid')]
axes[0].barh(labels, headroom, color=['#bd3a3a' if x < 0 else '#117c83' for x in headroom])
axes[0].axvline(0, color='black', linewidth=1)
axes[0].set(xlabel='Available minus demand (MW)', title='Capacity screen, not topology validation')
for i, value in enumerate(headroom):
    axes[0].annotate(f'{value:+.1f} MW', (value, i), xytext=(5, 0),
                     textcoords='offset points', va='center')
roles = list(result['results'])
gaps = [len(result['results'][r]['review']['missing_documents']) for r in roles]
axes[1].barh([r.replace('_', ' ') for r in roles], gaps, color='#213b58')
axes[1].invert_yaxis()
axes[1].set(xlabel='Missing document references', title='All disciplines require human review')
fig.suptitle('Synthetic 20 MW IT campus — 14-agent design review')
plt.show()
