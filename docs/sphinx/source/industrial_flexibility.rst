Industrial load shifting with solar
===================================

Business decision
-----------------
An industrial energy manager recommends when to run fixed production batches.
The buyer is a factory operator or energy-services provider. A paid feasibility
review could use this workflow; no customer fee or realised saving is asserted.
The role, prompt, tool and bounded agent loop live in ``energy_agents.flexibility``.
The packaged ``data/flexibility/skill.json`` describes inputs and acceptance.

Run after installation::

   energy-agents-flex --output outputs/industrial_flexibility
   python examples/demand_flexibility/plot_industrial_load_shifting.py

For custom data call ``optimise_batches(case)`` or ``run_flexibility_agent(case)``.
``FlexibilityChatPlanner`` accepts the existing explicit HTTPS provider settings;
it sends case contents to that endpoint. The gallery uses deterministic replay,
not a live LLM. The solver, not the model, chooses the schedule. No LLM performance
advantage, token cost or realised saving is claimed.

Reference outcome: daily cost EUR 3,320 to EUR 2,240, including EUR 160 in
rescheduling fees and EUR 280 of lost export revenue. Net saving is EUR 1,080
for this synthetic day; batch energy remains 8 MWh. Peak import falls from
3 MW to 1 MW, with no demand-charge saving claimed.

Method and safeguards
---------------------
Enumerate joint allowed starts of contiguous, constant-power batches. Keep each
batch's duration and energy fixed. Reject schedules above the grid import limit.
Minimise hourly import cost minus export credit plus the supplied fee for each
shifted batch. Include the unchanged feasible baseline, so recommendations cannot
increase modelled cost. The exact optimum is only within the supplied candidate
starts (up to 100,000 combinations). Equal-cost schedules retain the baseline
when possible. There are 24 one-hour UTC intervals: convert local DST days before
use; do not silently truncate 23/25-hour days. No storage or simultaneous grid
import/export is modelled. Export is unconstrained and mandatory for surplus.

The offline trace permits one optimisation and finish, independently verifies
results, and requires human approval. No physical controls or commitments exist.
Output files include inputs, results, shift-fee sensitivity and SHA-256 hashes.

All plant inputs and tariffs are synthetic. Prices must be the customer's marginal
contract prices, including relevant variable charges, not a wholesale proxy.
Demand charges, taxes, degradation, ramping, machine-sharing, production precedence,
uncertainty and export caps are excluded. Allowed starts need plant approval.
Repeated-day annualisation and emissions claims are deliberately absent.

News and repository evidence
----------------------------
The `IEA press release of 5 November 2026
<https://www.iea.org/news/accelerating-electrification-can-unlock-the-full-benefits-of-spains-renewables-leadership>`_
highlights electrification and demand flexibility in Spain. It motivates the
business question; none of the site's numerical inputs come from that report.
The indexed primary release was retrieved; full report page retrieval failed.

Energy Data Insights source commit ``600db672269079ab8a92224ad5de3cf80e8206bf``
was inspected: ``examples/connectors/plot_generation_ree.py`` demonstrates national
daily generation, and ``methods/src/energy_methods/hybrid_dispatch.py`` covers
hybrid storage dispatch. These are discovery context, not executed dependencies.
National daily energy must not be substituted for site hourly PV or retail tariffs.
Real deployment requires aligned meter data, solar forecasts, tariff terms and
approved production windows. No live EDI integration is claimed.

API
---
.. automodule:: energy_agents.flexibility
   :members:
