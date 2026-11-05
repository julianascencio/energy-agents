AI Forward-Deployed Engineer
========================================

``ai_forward_deployed_engineer`` owns the path from a customer problem to an
inspectable AI pilot proposal. It identifies the workflow, decision owner,
business KPI and baseline; designs integrations; specifies evaluation gates;
and prepares monitoring, adoption and rollback. It works across solar, wind,
BESS, hydro and energy markets.

The role complements the Python/data-science/ML engineer: the forward-deployed
engineer defines what to build, how it fits the customer's workflow and how to
accept it. The Python engineer proposes implementation, tests and examples.
Neither this workflow nor its accepted proposal deploys anything automatically.

Executable workflow
-------------------

The runner enforces discovery → solution → evaluation → rollout → finish.
Each stage requires its documented fields; missing/empty fields, repeated or
out-of-order actions are rejected and consume the bounded call budget. Accepted
reports and rejected-action errors remain available for subsequent decisions.
A valid complete plan returns a Python handoff; an incomplete run returns none.

**Validation checks structure and order only.** Plausible text can still be
incorrect, impractical or unsupported. Success means a complete proposal, not
customer acceptance, tested integration, achieved savings or production readiness.
The final report always marks deployment as unauthorized by this workflow.

Offline example
---------------

.. code-block:: bash

   python examples/delivery/plot_forward_deployed_engineer.py

The deterministic example proposes a read-only solar alarm-triage copilot. It
includes manual and rules-only baselines, a proposed held-out evaluation, citation
checks, tenant isolation tests, cost/latency budgets, analyst review and a manual
fallback. All customer inputs and thresholds are synthetic assumptions. The pilot
remains NO-GO until evidence and owner approval exist. No LLM or customer API runs.

Live planner
------------

.. code-block:: python

   from energy_agents.forward_deployed import (
       ForwardDeployedPlanner, run_forward_deployed_engineer,
   )

   planner = ForwardDeployedPlanner(
       endpoint="https://YOUR_PROVIDER/chat/completions", model="YOUR_MODEL",
   )
   result = run_forward_deployed_engineer(
       customer_brief={
           "problem": "Reduce evidence-gathering time for PV alarm triage",
           "users": "O&M analysts",
           "evidence": "Baseline not measured; acquisition is a pilot prerequisite",
           "constraints": "Read-only access and analyst approval",
       },
       repository_context={"approved_api_contract": reviewed_api_text},
       planner=planner,
       max_calls=8,
   )

Set ``ENERGY_AGENTS_API_KEY`` in the environment. The supplied customer and
repository context is sent to the explicitly configured endpoint; use only
material approved for that provider. No repository discovery, credential loading
beyond that API key, shell execution or customer-system access occurs. Provider
errors propagate; malformed actions can be repaired within the call budget.
Live model competence and pilot performance have not been benchmarked here.

Python engineering handoff
----------------------------------------

The returned ``python_handoff`` contains ``target_role``, ``task`` and
``repository_context`` (including the complete proposed delivery plan). When the
Python engineer from PR #7 is available, pass it directly to that workflow:

.. code-block:: python

   from energy_agents.python_engineer import run_python_engineer

   handoff = result["python_handoff"]
   if handoff is not None:
       coding_result = run_python_engineer(
           handoff["task"], handoff["repository_context"], coding_planner,
       )

This PR remains runnable without PR #7; the handoff is a serializable contract,
not an automatic invocation or a dependency on an unmerged module. Supply current
Energy Data Insights instructions and relevant APIs to support concrete reuse.
No complete or automatically refreshed upstream catalogue is implied.

Role and API
------------

The independent role contract is available as
``FORWARD_DEPLOYED_ENGINEER.as_dict()``. The existing PV role catalogue is unchanged.

.. automodule:: energy_agents.forward_deployed
   :members: ForwardDeployedPlanner, run_forward_deployed_engineer
