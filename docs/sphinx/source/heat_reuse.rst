Data-centre heat recovery investment screen
==========================================================================================

A district-heating operator must decide whether recovered data-centre heat can
displace enough marginal supply cost to justify heat pumps and connections.
This example provides a reusable advisory screen, combining the existing Liquid
Cooling Engineer and Project Finance Analyst through the bounded orchestrator.
A plausible paid offering is a heat-offtake feasibility and contract-input audit;
customer willingness to pay and realised benefits are unverified.

News and source boundary
------------------------

`Infomaniak's announcement <https://api.sttinfo.fi/tiedote/72501998/infomaniak-and-gruyere-energie-develop-a-data-center-project-in-bulle-designed-to-limit-its-footprint?lang=en&publisherId=69821841>`_
was published on 13 November 2026, the planning-application public-display date.
The Bulle proposal targets 2.5 MW IT and 28 GWh/year of heat **including heat pumps**,
with commissioning planned for 2028. Permits and contracts remain outstanding.
These are announced targets, not operating measurements. No actual costs or
returns are inferred. The synthetic operating case deliberately does not calibrate
to the announced annual heat target.

Thermal and financial boundaries
--------------------------------

Heating COP is heat-pump output divided by electrical input, as defined by
`DOE FEMP <https://www.energy.gov/cmei/femp/incorporate-minimum-efficiency-requirements-heating-and-cooling-products-federal>`_.
The model uses conservation of energy: output equals recovered source heat plus
pump electricity. For source heat S, heating COP C and network efficiency e,
potential delivered heat is ``min(S / (1 - 1/C), output_capacity * hours) * e``.
Delivered heat is the smaller of that potential and simultaneous demand.
Electricity is ``delivered / (e*C)``. The rest of demand stays on existing supply.
Unused server heat is bypassed; it earns no savings and uses no heat-pump energy.

Each period assumes flat simultaneous profiles. Monthly averaging is an optimistic
screen for unresolved intra-month matching; there is no heat storage or guarantee
of hourly delivery. The annual-only matching ceiling is displayed separately.
COP and capacity require temperature-specific evidence; this is no equipment,
network, hydraulic, ramping or minimum-load simulator. Recovery dispatch follows
available heat and demand, without price optimization or contractual guarantees.

All financial and operating inputs are **synthetic constant real CHF**, before
tax and financing. A 2.5 MW illustrative IT facility runs at 80% load; 90% of IT
heat is recoverable. Assume a 3 MW heat-pump output limit, COP 4, 95% delivery
efficiency and the twelve monthly heat-demand assumptions in ``case.json``.
CAPEX is CHF 4m; fixed O&M CHF 100k/year; electricity CHF 120/MWh; source heat
fee CHF 5/MWh recovered; variable O&M CHF 3/MWh delivered. Existing marginal heat
cost is CHF 80/MWh delivered. The same steady-state year repeats for 15 years,
discounted at 6%, with CAPEX at time zero and savings at year-end.

Baseline: keep existing supply. Intervention: add heat recovery and retain existing
supply for unmet demand. Avoid only displaced marginal cost; existing fixed costs
are unchanged. Server electricity and server CAPEX are unchanged in both options
and excluded. The source-heat fee is an explicit operating cost. No cooling credit,
carbon credit, subsidy or additional heat-sale revenue is stacked on the savings.
No construction delay, ramp-up, outage, degradation, inflation, tax, residual value
or replacement investment is modelled. Extra electrical auxiliaries require an
effective COP or explicit costs. No emissions reduction is computed.

Results and sensitivity
------------------------

The reference scenario delivers **13,024.32 MWh/year**, consuming 3,427.45 MWh of
heat-pump electricity. Annual-only matching would allow 15,852 MWh, overstating
period-matched delivery by 2,827.68 MWh. Supply cost falls from CHF 1,268,160 to
CHF 827,993.47/year. Net savings are **CHF 440,166.53/year**, incremental NPV
**CHF 275,006.98**, and break-even avoided supply cost **CHF 77.83/MWh**.
These are modelled scenario results, not realised customer earnings.

The gallery varies heat demand and electricity price without assigning probabilities.
Zero available or usable heat retains committed investment/fixed costs and returns
no finite break-even heat price. The screen does not recommend executing a contract.
Quotes, load profiles, metered COP, permits and commercial terms require diligence.

Reusable workflow and EDI adapter
---------------------------------

``data/heat_reuse/skill.json`` saves the actual user request, role mandates, schema,
allowed tools, evidence requirements, handoffs, outputs and acceptance criteria.
Evidence precedes thermal calculation, which precedes finance. Finance recomputes
the input-bound balance before accepting the handoff. Unknown actions and premature
delegation fail; no external execution capability is registered.
Scripted workflow and direct deterministic calculation agree. This is no measured
LLM advantage; provider cost, latency and tokens are unknown.

``edi_capabilities.json`` records inspected EDI commit
``edd4086a207e95651dc1e8096004b3db71c33e9c`` and source hash. The optional adapter
executes ``energy_methods.hybrid_dispatch.simulate_hybrid`` solely as a no-storage
MW/MWh matching check. Thermal potential maps to its supply channel; solar and
battery inputs are zero. One independent call per period supports different hours.
The electrical API's names do not imply wind generation or thermal-storage physics.
Heating conversion and cash flows remain local. A source-hash mismatch fails closed;
metadata discovery alone is not execution. No upstream scientific code is copied.

Reproduction
------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-heat --output outputs/heat_reuse
   python examples/business/plot_heat_reuse.py
   python -m pytest tests/test_heat_reuse.py

The default path needs no keys, network or EDI after installation. ``--case`` accepts
an explicitly synthetic scenario. Optional local EDI execution, also key-free:

.. code-block:: bash

   python -m pip install --no-deps --require-hashes -r requirements/operations.txt
   energy-agents-heat --edi --output outputs/heat_reuse_edi

The existing hash-pinned energy-methods 0.1.1 distribution requires Python 3.12+.
JSON exports include inputs, workflow trace, economic/energy report, capability
metadata and separate actual EDI execution status. No automatic live source retrieval,
private-data access or plant connection is provided. A configured optional
``OrchestratorPlanner`` can prioritize ready tasks; calculations remain deterministic
and no live provider evaluation has been performed.
