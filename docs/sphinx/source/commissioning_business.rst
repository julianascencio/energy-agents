Wind commissioning: revenue-aware acceleration
==================================================

A Project Controls Engineer helps an asset owner or EPC manager decide whether
paying for additional commissioning resources can bring commercial operation
forward enough to justify the cost. The commercial offering is an auditable
schedule/value review, not a promise of project savings.

News context and evidence
-----------------------------

`Orsted's issuer announcement dated 5 November 2026
<https://orsted.com/en/company-announcement-list/2026/11/orsted-delivers-strong-earnings-with-19--ebitda-gr-152708491>`_
reports commercial-operation milestones for Borkum Riffgrund 3 and Revolution Wind.
The official release and its EQS syndication were indexed by search; direct full-page
retrieval was unavailable during this run. The news supplies motivation only.
There is no claim of an actual delay, acceleration opportunity or private schedule
at either project. The milestone dates are not inferred from the publication date.
No claim is made about audience-level trending popularity.

**All schedule durations, intervention feasibility, prices and asset characteristics
in this example are synthetic.** No plant telemetry or private cost data is used.

Run the example
-------------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-commissioning --output outputs/wind_commissioning
   python examples/project_delivery/plot_wind_commissioning.py

.. code-block:: python

   from energy_agents.commissioning import reference_case, run_commissioning_agent

   case = reference_case()
   result = run_commissioning_agent(case)
   assert result["success"]
   print(result["reports"]["screen"]["recommended_package"])

Use the Python interface to supply a different validated case. The packaged
``data/commissioning/case.json`` contains every input and limitation.
``data/commissioning/skill.json`` contains reusable user/system prompts, handoffs,
input/output contracts, permissions and acceptance criteria.

Business result
-------------------

The hypothetical wind project is 100 MW, with a 40% capacity factor and 100%
availability during the recovered window. Expected daily generation is 960 MWh.
A EUR 75/MWh realised-price assumption less EUR 5/MWh variable cost gives an expected
contribution of EUR 67,200/day. These are scenario assumptions, not market observations.

.. list-table:: Reference package
   :header-rows: 1

   * - Metric
     - Calculated scenario result
   * - Baseline completion
     - Day 25
   * - Proposed completion
     - Day 20
   * - Selected actions
     - Extra substation crew and reserved witness slot
   * - Expected energy brought forward
     - 4,800 MWh
   * - Expected contribution brought forward
     - EUR 336,000
   * - Acceleration cost
     - EUR 140,000, within EUR 150,000 budget
   * - Expected net benefit
     - EUR 196,000

Accelerating turbine tests alone saves no completion days in this scenario and
costs EUR 40,000. This illustrates why summing individual task-day reductions
would overstate value. The export also reruns package selection at EUR 50, 75 and
100/MWh. It reoptimises the package each time rather than assuming the same decision.

Method and limits
---------------------

Earliest start equals the latest finish among a task's prerequisites. All tasks
are assumed required for commercial operation, including disconnected paths.
For each feasible package, the schedule is recomputed from scratch. Alternative
options on the same task are mutually exclusive. Every combination of up to 12
options is evaluated, subject to the spending cap. The no-action package is always
included and wins when acceleration has no positive economic value.

The objective is expected additional contribution over the fixed interval ending
at the original completion date, minus acceleration cost. The model does not claim
extra lifetime energy: it brings operation forward into that window. It omits
financing carry, discounting over the short window, tax, partial commissioning,
weather constraints, resource conflicts, capture-price effects and contract penalties.
Constant expected output and price are simplifying assumptions. Negative prices
are allowed and do not force an acceleration purchase.

Minimum durations are enforced. The reliability run cannot be shortened in the
reference case. A reserved witness slot is an explicit conditional scenario,
not an assertion that a utility will provide one. No inspection scope, test or
regulatory approval is waived. Qualified engineering and utility acceptance are
preconditions to actual execution.

Agent workflow
------------------

The previously catalogued Project Controls Engineer is now represented by a
``RoleSpec`` and executable commissioning skill. The planner may select only
``rank_acceleration`` followed by ``finish``. Inputs are copied, argument overrides
are rejected and the call budget is bounded. Completion replays the deterministic
calculation and leaves the decision ``human_review_required``.

The example uses a scripted planner and compares its results with direct execution.
There is no live LLM run or measured reasoning advantage. Live model cost/latency
remain unknown. An optional configured provider can select the same bounded tools:

.. code-block:: python

   from energy_agents.connectors import CommissioningChatCompletionsPlanner
   from energy_agents.commissioning import reference_case, run_commissioning_agent

   # Set ENERGY_AGENTS_API_KEY outside source code; this sends the case to the endpoint.
   planner = CommissioningChatCompletionsPlanner(
       "https://YOUR_PROVIDER/v1/chat/completions", "YOUR_MODEL"
   )
   result = run_commissioning_agent(reference_case(), planner)

The LLM does not generate unconstrained schedules or change the engineering inputs.
The local tools enumerate alternatives. Human users remain responsible for feasibility
and decisions; the skill does not send orders or control equipment.

Energy Data Insights context
--------------------------------

The source-derived catalogue previously pinned to
``aa842b959bebe8b4279a449f91176be26f0ad6a5`` was consulted alongside EDI source at
``600db672269079ab8a92224ad5de3cf80e8206bf``. Its wind-project catalogue can supply
identity/capacity context, and forecasting tools may support future time-varying
production inputs. They do not supply this hypothetical project's commissioning
DAG, witness availability or commercial terms. No suitable critical-path method
was found in the inspected scientific methods package, so none was imported under
a misleading adapter name. **EDI discovery occurred; no EDI method was executed
for this case.** Integration should wait for a relevant evidenced input.

Repository history and validations
--------------------------------------

This case is independent of the BESS saturation PR #4 and does not modify it.
PR #2 is on main. PR #3 was merged into the old feature branch, and its awareness
code was absent from main at inspection. Selection rationale and PR tracking are
in ``docs/cases/2026-11-05-wind-commissioning.md``.

Tests include hand-checked economics, a shifting bottleneck, zero-benefit tasks,
cycle and missing-dependency rejection, minimum durations, exclusive alternatives,
budget limits, negative prices, context isolation, forbidden actions and repeatable
exports. Local contract replay is not independent scientific verification.
