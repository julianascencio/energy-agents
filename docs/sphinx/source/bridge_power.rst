Data centre bridge-power screen
================================

A temporary power service can unlock earlier operation, but the incremental
contribution must cover electricity, fixed service costs and mobilization.
This screen reuses the Project Finance Analyst role and existing orchestrator;
it adds no new professional agent or provider dependency.

News and economic scope
-----------------------

`NTT DATA / Bloom announcement, 5 November 2026 <https://www.bloomenergy.com/news/ntt-data-announces-agreement-with-bloom-energy-for-900-mw-of-onsite-power-generation-across-multiple-data-center-projects/>`_
reports an agreement for 900 MW across multiple projects, with initial shipments
planned for 2027. This is an issuer statement about plans, not operating capacity.
It does not disclose prices or project cash flows. No claim of trending status.

All example economics are **synthetic**: 10 MW IT, PUE 1.3, utilization 80%,
availability 95%, contribution before electricity EUR 300/IT-MWh, electricity
EUR 140/facility-MWh, fixed service EUR 100,000/month and EUR 2m upfront.
The bridge is ready at month 3 and grid at month 12. The horizon is the nine
incremental months, each modelled as 730 hours. End-month cash is discounted at
10% annually; upfront expense is paid today. Future common operations cancel.
This is not a full data centre valuation or a forecast of NTT returns.

IT energy = IT MW * hours * utilization * availability. Facility energy = IT
energy * PUE. Contribution is after non-energy variable cost, before electricity.
Power price includes fuel, conversion losses and variable O&M; do not subtract
fuel again. Net cash is contribution minus power and fixed fees. Incremental NPV
subtracts upfront expense and compares with waiting (zero incremental NPV).

The default yields EUR 554,664 monthly cash, **EUR 2,685,637.47 incremental NPV**,
and a break-even contribution of EUR 242.70/IT-MWh. The gallery varies contribution
margin and grid-ready month. Scenarios are sensitivities, not probabilities.
The tool retains the wait option when bridge economics are negative. When no
energy or operating months exist, break-even is undefined (null).

Commercial application and limits
----------------------------------

Potential buyers are developers, infrastructure funds and enterprise capacity
procurement teams. A plausible paid offering is an auditable pre-investment
screen plus customer-specific contract and sensitivity review. No willingness
to pay, realised savings or commercial price has been measured.

The tool assumes ready customers, adequate fuel, permissions and service quality.
Average availability scaling does not establish redundancy or SLA compliance.
Synthetic contribution and occupancy must be replaced with customer evidence.
All incremental fixed costs must be included in upfront/fixed fees. Tax, finance,
carbon cost, outage penalties, minimum-take commitments and stranded contracts
are excluded; any could reverse the decision. Natural-gas fuel cells are not
assumed carbon-free. No dispatch, purchases or third-party communications occur.

Reproduce and inspect
----------------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-bridge --output outputs/bridge_power
   python examples/data_centers/plot_bridge_power.py
   python -m pytest
   ruff check .
   python -m build
   sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/_build/html

The CLI saves a workflow trace, evidence classification, input hash and cash
flows. It asserts parity with direct deterministic execution. This is an offline
scripted workflow; no measured LLM benefit. LLM latency, cost and tokens remain
unknown. Optional live scheduling can use the existing OrchestratorPlanner with
explicit caller configuration; it is unbenchmarked and not needed for economics.

Versioned prompts and schemas are packaged in
``energy_agents/data/bridge_power/skill.json`` and ``case.json``. Validation gates
schema/classification only, not factual truth. The finance task receives an
isolated validated case. Forbidden tools and out-of-order handoffs are rejected.

Energy Data Insights integration
--------------------------------

Source-derived inventory refreshed from EDI commit
``036429f93354749517d91ac62b18390ec7bccddc`` (735 indexed files, 1,481 public
symbols, zero parse errors); a focused excerpt and the full coverage manifest
are packaged as ``edi_capabilities.json``. This is a pinned snapshot, not a claim
of latest remote coverage. The existing awareness PR #3 was merged into the old
role feature branch and its module is absent from main; it is not silently imported.

The optional bounded adapter executes EDI's existing data centre record loader
and validator. It validated 3,330 records at the recorded checkout; the execution
manifest records the input hash. It supplies context only, not finance calibration,
PUE estimates or additive capacity totals. No suitable bridge-economics method
was identified in the inspected inventory, so this small decision tool lives here.
EDI source discovery and execution are separately recorded.

To repeat the optional adapter, install ``energy-data-retrieval`` 0.1.0 from that
commit's ``data-retrieval`` directory (Python 3.12+, dependencies declared there),
then call:

.. code-block:: python

   from energy_agents.business.bridge_power import inspect_edi_inventory
   print(inspect_edi_inventory("/path/to/energy-data-insights/catalogues/data_centers"))

The default offline path does not require EDI installation or network keys.

.. automodule:: energy_agents.business.bridge_power
   :members:
