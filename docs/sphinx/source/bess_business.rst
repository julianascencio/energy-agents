BESS revenue concentration: news to investment screening
============================================================

Business decision
---------------------

A developer, fund or lender needs to know whether a battery investment remains
viable when ancillary-service income erodes. A possible commercial service is an
auditable investment-screening report that challenges optimistic revenue paths,
shows missing evidence and supports human due diligence. No consulting price,
customer commitment or realised savings is assumed.

The selected primary source is `Clean Horizon's 4 November 2026 analysis
<https://www.cleanhorizon.com/news/where-are-battery-storage-revenues-heading-in-europe/>`_,
which discusses changing battery revenue composition. It follows a presentation
on 1 October 2026; those dates are distinct. Two imported model outputs anchor
this example: Poland's annualised January-August gross index of EUR 587,000/MW/year,
including EUR 456,000/MW/year of ancillary income for a two-hour system. These are
published modelled benchmarks, not metered revenue or a project forecast.

The three future paths below are **our illustrative assumptions**, not the
publisher's forecast. No claim is made that this story is trending by audience size.

Run and inspect
-------------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-bess --output outputs/bess_saturation
   python examples/business/plot_bess_saturation.py

.. code-block:: python

   from energy_agents.business import reference_case, run_bess_agent

   result = run_bess_agent(reference_case())
   assert result["success"]
   print(result["reports"]["screen"]["scenarios"])

The packaged case and reusable prompts are in
``src/energy_agents/data/business/bess_saturation.json`` and
``bess_skill.json``. Pass ``--input case.json`` for an explicitly edited case.
Outputs contain the complete case, role contract, action trace, annual cash flows,
review result, sensitivity results and checksums.

Assumptions and results
---------------------------

The example is a hypothetical 10 MW / 20 MWh asset, EUR 12m upfront cost, 15 years,
10% real discount rate, 95% availability, 1.5% annual revenue derating and
EUR 45,000/MW/year recurring cost. The recurring-cost figure is an illustrative
combined O&M/grid/service allowance, not a country tariff quote. Year-zero capex
and year-end cash flows use constant-real EUR. No inflation is separately added.

.. list-table:: Calculated unlevered pretax scenarios
   :header-rows: 1

   * - Path
     - NPV, EUR million
     - Zero-NPV upfront budget, EUR million
   * - Flat market index
     - 23.815
     - 35.815
   * - Saturation stress
     - 1.555
     - 13.555
   * - Severe stress
     - -3.884
     - 8.116

The saturation path reduces NPV by EUR 22.260m relative to flat market revenues.
That is modelled valuation sensitivity, **not cash saved or earned by the agent**.
A zero-NPV upfront budget is the discounted operating cash under these assumptions;
it is not an independently assessed market value or recommended acquisition price.
Negative operating cash and negative NPV remain visible.

The flat path holds market revenue rates constant but still applies the common
availability and annual derating assumptions. The saturation path retains 10% of
initial ancillary income and 80% of other income from year five; severe stress
retains zero ancillary and 60% of other income from year four. The JSON contains
every annual multiplier. No probability is attached to these paths. The export
also recalculates NPV at 6%, 10% and 14% discount rates.

For each year, gross cash equals MW times availability times annual derating times
the sum of the two independently scaled revenue components. Subtract recurring
cost, discount to time zero, then subtract upfront capex. The non-ancillary component
is the residual between total and ancillary index values; it is not relabelled
as pure arbitrage. Round-trip efficiency is already embedded in the source index,
so it is not applied again.

Tax, leverage, subsidies, augmentation, residual value, decommissioning and
project-specific market eligibility are excluded. Uniform availability/derating is
simplified. This is not a dispatch optimisation, bankable valuation or saturation
forecast. A user must replace assumptions with project evidence before decisions.

Agent capability and prompts
--------------------------------

The Project Finance Analyst implements the previously planned finance role as a
bounded BESS skill using the shared ``RoleSpec`` contract. It executes
``stress_revenues``, then ``review_screen``, then ``finish``. Tool arguments are
empty: a planner cannot modify case inputs, issue commitments or place trades.
Missing prerequisites, repeated tools and exhausted budgets stop the run.
The reviewer replays the contract; it is not an independent scientific model.

``bess_skill.json`` records the complete user/system prompts, tool permissions,
input/output contracts, handoffs and acceptance criteria. The Commercial Asset
Manager supplies assumptions, the finance role screens them, and a human investment
committee owns the decision. Every completed result remains ``human_review_required``.

An optional live planner uses the existing explicit endpoint adapter:

.. code-block:: python

   from energy_agents.connectors import BESSChatCompletionsPlanner
   from energy_agents.business import reference_case, run_bess_agent

   # Configure ENERGY_AGENTS_API_KEY outside code. The case goes to this endpoint.
   planner = BESSChatCompletionsPlanner(
       "https://YOUR_PROVIDER/v1/chat/completions", "YOUR_MODEL"
   )
   result = run_bess_agent(reference_case(), planner)

The runnable gallery uses a scripted reference planner and compares its report
with direct deterministic execution. This demonstrates accounting parity and
bounded handoffs, not superior LLM reasoning. No live LLM was run; live token cost
and latency are unknown. HTTP behavior is tested with a mock.

Energy Data Insights reuse
------------------------------

The earlier source-derived catalogue at commit
``aa842b959bebe8b4279a449f91176be26f0ad6a5`` identified the existing BESS loader.
Its implementation was then inspected at EDI commit
``600db672269079ab8a92224ad5de3cf80e8206bf``. There is no generic BESS revenue-path
finance method in the inspected methods package; the PV lifetime calculator is
not repurposed as a battery model.

The optional adapter reuses EDI's real ``load_records`` and ``validate_record``
functions to report the Polish project inventory by status. It does not sum
possibly overlapping phases, infer operational capacity, or calibrate saturation
from an incomplete project database. Financial results remain independent of this
context. Both the loader and schema validation must succeed; failures are visible.

.. code-block:: bash

   git clone https://github.com/julianascencio/energy-data-insights.git edi
   git -C edi checkout 600db672269079ab8a92224ad5de3cf80e8206bf
   # EDI requires Python 3.12+; install its dependencies in a suitable environment.
   python -m pip install ./edi/data-retrieval
   energy-agents-bess --edi-catalogue edi/catalogues/bess --output outputs/bess_saturation

The core example remains offline and works without EDI installed. Optional adapter
output records IDs, status counts and input hash rather than redistributing project
records. The dependency version is 0.1.0 at the pinned source commit; do not assume
another release has identical schema. Source-only indexing does not mean EDI ran.

Case history
----------------

Selection, alternatives, implementation evidence and PR tracking are recorded in
``docs/cases/2026-11-05-bess-revenue-saturation.md``. No prior news case existed in
main at inspection. PR #2 was merged; PR #3 was merged into its old feature branch
and its awareness code was absent from main. This case preserves main's public APIs
and does not silently merge that separate feature.
