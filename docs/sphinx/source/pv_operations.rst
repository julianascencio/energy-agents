PV operations: investigate, value, recommend
================================================

Run the offline reference workflow
--------------------------------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-pv --output outputs/pv_operations
   python examples/operations/plot_pv_role_team.py
   # Your own versioned daily case, with the same schema:
   energy-agents-pv --input case.json --output outputs/my_case

.. code-block:: python

   from energy_agents.pv import synthetic_pv_case, run_pv_workflow

   case = synthetic_pv_case()
   result = run_pv_workflow(case)
   assert result["success"]
   print(result["reports"]["asset_summary"]["data"])

``success`` means workflow completion and accounting/contract checks passed.
It does not mean a plant is healthy, data is sufficient, or an intervention is
approved. Zero coverage can still produce a valid report stating the evidence gap.

Input contract
------------------

``case.json`` exported by the CLI is a complete editable example. Schema 1.0 has:

* Identity: ``case_id``, positive integer ``revision``, ``plant_id``,
  ``technology=solar_pv``, IANA ``timezone`` and three-letter ``currency``.
* ``evidence``: ID-keyed records with ``source``, ``kind`` (measured, imported,
  modelled or synthetic) and separate ``verification`` (verified or unverified).
  These are supplied metadata, never automatically verified by the runner.
* ``days``: unique ISO dates in the stated timezone, ``expected_mwh``,
  ``actual_mwh`` (nullable), ``price_per_mwh``, ``event`` and ``evidence_ids``.
  Expected and actual values must use the same daily energy/export boundary.
* ``event``: none, equipment_fault or curtailment. Reconcile overlapping events
  upstream. Daily labels cannot identify within-day causal losses.
* ``evidence_ids``: expected, actual, price and (when present) event references.
* ``assumptions``: recovery_fraction in [0, 1], nonnegative intervention_cost,
  scenario_description and an evidence_id for those assumptions.

Negative prices are supported. Missing actual energy excludes the day from both
expected and actual totals. No interpolation, price conversion or annualisation
occurs. Expected energy is user supplied; this release has no calibrated PV model,
weather connector, anomaly detector or causal root-cause engine.

Accounting and limitations
------------------------------

For each day with actual energy, deficit is max(expected - actual, 0), and surplus
is max(actual - expected, 0). Their difference equals the signed energy shortfall.
Deficits are grouped by the supplied event label; an unlabelled deficit remains
unresolved. Equipment-fault association is an upper-bound investigative scenario,
not proof that repairing the equipment recovers the entire associated deficit.

Historical deficit value is the sum of daily deficit times daily price. Conditional
recovery energy is fault-associated deficit times recovery_fraction. Conditional
gross value uses the same fraction and corresponding prices; net value subtracts
the assumed intervention cost. The synthetic scenario explicitly assumes recurrence
over a comparable six-day period. It is not a forecast, lifetime NPV, settlement
calculation or compensation entitlement. Surplus value is not included in deficit value.

The reference case contains 500 MWh expected and 435 MWh actual on five valid days,
70 MWh deficit and 5 MWh surplus. Its deficit split is 40 MWh fault-associated,
20 MWh curtailment and 10 MWh unresolved. One day is excluded. At illustrative
prices and assumptions the conditional recovery is 32 MWh, gross value EUR 1,600
and net value EUR 1,500. Every input is synthetic and unverified.

Execution and evaluation
----------------------------

Three modes use exactly the same tools and input:

.. list-table:: Offline reference execution
   :header-rows: 1

   * - Mode
     - Planner calls
     - Tool calls
   * - deterministic
     - 0
     - 5
   * - single_agent (scripted reference)
     - 6
     - 5
   * - role_team (five scripted reference planners)
     - 10
     - 5

These modes establish report parity and quantify orchestration overhead. They are
not measured LLM benchmarks and do not establish a multi-agent quality advantage.
Live model cost is unknown. The runner accepts injected Planner-compatible objects
for comparative experiments. Role tools are allowlisted, dependencies enforced,
input copies isolated and the total planner budget bounded (default 12, maximum 100).
``finish`` also consumes a call. A rejected action or exhausted budget stops the
run with ``success=False``; any partial reports are for inspection, not acceptance.

The evidence reviewer independently reconciles raw arithmetic and replays tool
contracts to detect modified values, missing evidence and altered authority labels.
It is independent of planner text, but shares domain tools for contract checks;
it is not an independent scientific implementation of the model.

Exports contain the input case, role contracts, three complete runs and SHA-256
checksums. The case digest covers the full versioned snapshot. Review the full
trace and ``review`` result before using outputs.

Optional LLM planning
-------------------------

.. code-block:: python

   from energy_agents.connectors import PVChatCompletionsPlanner
   from energy_agents.roles import PV_ROLES
   from energy_agents.pv import run_pv_workflow, synthetic_pv_case

   # Configure ENERGY_AGENTS_API_KEY outside the source code.
   planners = {
       role.id: PVChatCompletionsPlanner(
           "https://YOUR_PROVIDER/v1/chat/completions", "YOUR_MODEL"
       )
       for role in PV_ROLES
   }
   result = run_pv_workflow(synthetic_pv_case(), planners=planners)

The full case and report context are sent to the explicitly configured endpoint.
No live provider run is claimed. Transport and prompt selection are covered by
mocked tests; usage metadata is available on each planner's ``usage`` list. Tools
compute numerical results locally; the model selects permitted actions, not new
numerical findings. This intentionally narrow first version does not implement
open-ended diagnosis, agent debate or autonomous field action.

Next evaluation milestones
------------------------------

Use a consented real plant case with independent event labels and a calibrated
baseline, then compare repeated single-planner and role-team runs with the same
model, tools, inputs and call budget. Measure completion, unsupported claims,
missed issues, reproducibility, latency and tokens/cost. Expand tool capabilities
only when the case demonstrates an unmet need. Wind/BESS/hydro roles and persistent
asset memory remain planned.
