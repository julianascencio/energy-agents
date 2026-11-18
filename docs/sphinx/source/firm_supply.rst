Firm renewable supply: audit the gaps before buying backup
==========================================================

Business decision and news
--------------------------

An industrial power buyer must shortlist renewable delivery offers and provision
backup. A procurement adviser could sell a profile diligence report or integrate
this evidence-gated screen into a buyer's tender workflow. The existing finance
role runs the economics; no new professional agent is introduced.

`GWEC's 16 November announcement
<https://www.gwec.net/news/increasing-wind-in-the-clean-energy-mix-cuts-the-cost-of-electricity-by-nearly-20>`_
reports an event on 13 November in Antalya. It presents Ember model medians of
105 and 86 USD/MWh for solar/battery and wind-inclusive configurations supplying
90% of demand. These are global model results, not observed customer savings or
offers used below. The `atlas methodology
<https://ember-labs-org.github.io/WindSolarBatteryAtlas_Labs/>`_ defines coverage
as the share of energy demand served, explicitly distinguishing it from the
share of hours with full supply. The `atlas landing page
<https://ember-labs.org/experiments/wind-solar-battery-atlas>`_ was updated on
16 November; accessed 17 November 2026. No trending claim is made.

This screen turns that distinction into a customer decision: how much shortfall
can available backup actually cover, and what is the remaining economic exposure?
It differs from the VPPA basis case (financial settlement), residential reserve
(battery commitments), and non-firm service proposal (optional load curtailment).

Synthetic seven-day example
---------------------------

All customer data and prices are deliberately synthetic. Two net-delivery
profiles supply 1,512 MWh against 1,680 MWh of constant 10 MW demand over 168
hours. One supplies 10 MW for 18 hours/day and 6 MW for six hours/day; the other
supplies 9 MW throughout. These are counterexample traces, not physical designs,
Ember data, or evidence of wind superiority. Fees are 126,000 and 133,000 USD
for the complete window, independent of delivered energy.

The base scenario has 2 MW of continuously available backup, a capacity charge
of 200 USD/MW/day, variable cost of 200 USD/MWh and lost contribution of
2,000 USD per residual unserved MWh. All values are undiscounted USD over seven
days, before tax. No annual extrapolation is made.

.. list-table:: Computed scenario results
   :header-rows: 1

   * - Metric
     - Concentrated gap
     - Distributed gap
   * - Renewable energy coverage
     - 90%
     - 90%
   * - Full-load served hours before backup
     - 126
     - 0
   * - Peak shortfall, MW
     - 4
     - 1
   * - Full-load served hours after backup
     - 126
     - 168
   * - Residual unserved energy, MWh
     - 84
     - 0
   * - Cash supply cost, USD
     - 145,600
     - 169,400
   * - Scenario lost contribution, USD
     - 168,000
     - 0
   * - Total economic cost, USD
     - 313,600
     - 169,400

Selecting solely by the offer fee chooses the concentrated-gap offer. With the
stated backup and lost-contribution assumptions, the distributed-gap offer has
144,200 USD lower economic cost, but requires **23,800 USD more cash spending**.
The difference is conditional avoided opportunity loss, not realised profit.
The break-even lost contribution is 283.33 USD/MWh. At zero lost contribution
the lower-fee offer wins. With 4 MW backup both serve the full load and the
concentrated-gap offer costs 165,200 versus 172,200 USD. The gallery plots both
sensitivities; neither offer is universally preferable.

Equations and boundary
----------------------

For each one-hour interval, renewable service is min(demand, net delivery).
Shortfall is max(0, demand - net delivery); backup supplies min(shortfall, backup
MW); the remainder is unserved. Excess is recorded without resale value and
cannot fill another hour's gap. Demand equals renewable service plus backup
plus residual unserved energy. Full-load served hours use a 1e-9 MWh tolerance;
zero-demand hours count as fully served, but a zero-demand window is rejected.

Cash cost equals the fixed window fee plus backup MW times its daily capacity
charge times hours/24, plus backup MWh times its variable rate. Economic cost
adds residual unserved MWh times lost contribution. The break-even rate for an
alternative with less residual loss is its incremental cash cost divided by
avoided unserved MWh; it is undefined when it does not reduce unserved energy.

Inputs are **net deliveries after any upstream storage**. There is no generation,
weather or battery dispatch model here and no claim that these profiles are
buildable. Backup is instant, perfectly available and has unlimited fuel. The
screen omits ramping, minimum loading, start/restart costs, network constraints,
sub-hourly outages, fuel constraints and correlated failures. Hourly adequacy
does not certify service reliability. Meter traces, engineering evidence,
quotes and customer lost-margin estimates are needed for an actual purchase.

Reusable capability and handoffs
--------------------------------

The versioned ``data/firm_supply/skill.json`` contains the actual user prompt,
role mandates, input schema, allowed tools, evidence requirements, handoffs,
output contract and acceptance criteria. ``validate_case`` accepts labelled
synthetic scenarios only, finite bounded nonboolean numbers, aligned contiguous
UTC hours, unique offers, chronological evidence dates and explicit limitations.
The evidence task calculates ``delivery_audit``. The existing
``project_finance_analyst`` recomputes that input-hash-bound handoff before
``screen_firm_supply`` accepts it. The orchestrator exposes only ready task
delegation. Invalid evidence blocks finance; external tools and premature
handoffs are rejected. No purchasing, contracts, communications or controls run.

The scripted workflow equals the direct deterministic baseline numerically.
There is no measured LLM benefit: no live LLM was run, and LLM cost, latency and
tokens are unknown. A schema pass is not source verification or independent review.

Energy Data Insights reuse
--------------------------

The source-derived catalogue records EDI commit
``fc63c5f97e6513e7f290340ddfdce0b80962644a`` and the unchanged
``methods/src/energy_methods/hybrid_dispatch.py`` blob
``9a3f8bf79cce6d00d62adcf2ae3a23c9718de82e``. The existing hash-pinned public
``energy-methods==0.1.1`` dependency is reused. With ``--edi`` the adapter checks
the installed source SHA256, then executes ``simulate_hybrid`` on each offer
using its generic supply channel, zero solar and zero battery. This verifies
net energy matching only; it neither attributes supply to wind nor re-dispatches
storage. The no-dependency default uses the transparent min/max audit. The
execution result is saved separately from catalogue discovery and report output.
No new retrieval connector or credentials are needed.

Reproduction and checks
-----------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-firm --output outputs/firm_supply
   python examples/business/plot_firm_supply.py
   # Optional executed EDI cross-check, Python 3.12+:
   python -m pip install --require-hashes --no-deps -r requirements/operations.txt
   energy-agents-firm --edi --output outputs/firm_supply_edi
   python -m pytest tests/test_firm_supply.py
   ruff check .
   python -m pytest
   python -m build
   sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

After installation, the example and optional EDI run are offline and key-free.
``--case`` accepts a local v1 JSON case; there is no live retrieval or live LLM
mode in this screen. Outputs include inputs, delivery ledger, scripted trace,
report, catalogue and separate EDI execution evidence. Required CI includes
both supported Python versions, operations integration with the EDI adapter,
the existing quantum backend job, and strict documentation/gallery execution.
