Energy Agent Orchestrator
========================================

The orchestrator routes explicit tasks to registered specialist runners. Each task
has an ID, role, dependencies and payload. Dependencies form a validated acyclic
graph: only ready tasks may run, and each specialist runs at most once per task.
Use it to coordinate discovery, implementation and other explicitly registered
energy workflows without giving the scheduling model arbitrary tool access.

Behavior and limits
----------------------------------------

* Completed: the specialist returned boolean success, not independent validation.
* Failed: the specialist failed, raised an exception or returned a malformed result.
* Blocked: an upstream dependency failed or was blocked; the specialist is not called.
* Pending: the scheduler budget ended before this task could run.

Independent branches continue after failures. Upstream results are copied into
handoffs, preventing one runner from mutating another's recorded output. The trace
records delegated tasks and rejected scheduling actions. Invalid graphs fail before
execution. There is no automatic deployment, publication or code execution tool.
Registered callbacks are trusted Python code and are **not sandboxed**; configure
their own timeouts, model-call limits and permissions. The scheduler's call budget
bounds delegation attempts, not callback duration or nested model calls.

The default scheduler deterministically chooses the first ready task. Optional
``OrchestratorPlanner`` uses the existing explicitly configured Chat Completions
adapter to prioritize ready tasks. Task metadata, payloads, states and history are
sent to that provider; specialist result bodies are passed to dependent runners,
not the scheduling model. Provider errors propagate. Invalid model actions consume
the scheduler budget. Live LLM scheduling quality has not been measured.

Run the offline example
----------------------------------------

.. code-block:: bash

   python examples/orchestration/plot_orchestrator.py

It uses synthetic runner fixtures to demonstrate successful routing and blocked
implementation. It does not simulate measured customer results or generate code.

Compose the delivery specialists
----------------------------------------

``run_delivery_team`` connects the AI Forward-Deployed Engineer (PR #8) to the
Python/Data Science/ML Engineer (PR #7), passing the former's full Python handoff
into the latter. These specialist PRs must be installed/merged for this adapter;
otherwise it raises an explicit dependency error. The standalone orchestrator and
its offline gallery example run without those unmerged modules.

.. code-block:: python

   from energy_agents.orchestrator import run_delivery_team

   result = run_delivery_team(
       brief, reviewed_repository_context, delivery_planner, coding_planner,
   )
   print(result["states"])

The delivery planner retains its 8-call limit, and the coding planner its 3-call
limit. The orchestrator defaults to 4 scheduling attempts for this two-task flow.
A failed delivery proposal blocks coding. A completed coding proposal remains
unexecuted and unreviewed: use external lint, tests and review before accepting it.

Other professional agents
----------------------------------------

Register additional trusted runners by role name and return a dictionary with a
boolean ``success``. A runner receives ``task_id``, ``payload`` and ``upstream``.
Use adapters around the PV workflow or future specialist APIs rather than asking
the scheduling model to invent imports or execution commands. The orchestrator
role contract is exposed as ``ORCHESTRATOR.as_dict()``; PV roles remain unchanged.

.. automodule:: energy_agents.orchestrator
   :members: AgentTask, ReadyTaskPlanner, OrchestratorPlanner, run_orchestrator, run_delivery_team
