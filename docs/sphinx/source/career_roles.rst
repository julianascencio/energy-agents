Public-career role agents
====================================================================================================

Research through 10 November 2026 covered **57 public role descriptions**, represented
by **53 generic agent contracts** across AI, data, energy operations, commercial,
finance, IT, security, marketing, strategy, HR and legal support.

The packaged catalogue contains generic responsibilities and a neutral source
index. Employer names, source URLs, original posting identifiers and titles,
departments, locations and document hashes are omitted. The index preserves
coverage and deduplication; it is not publicly verifiable source attribution.
Full job descriptions are not redistributed. This package does not monitor hiring.

Agent titles and instructions are neutral original syntheses. They do not imply
employer endorsement, reproduce internal procedures, or confer professional
qualifications. Intern and working-student roles become supervised assistants.

Coverage and normalization
----------------------------------------------------------------------------------------------------

Three procurement listings map to one procurement agent; two equivalent
forward-deployed engineering listings map to one applied AI agent; two language
variants of customer support map to one agent covering their combined scope.
The two IoT product-lead roles remain separate because one also owns shared agent
platform capabilities. No listed opening is omitted.

.. include:: career_role_mapping.inc

Run the agents
----------------------------------------------------------------------------------------------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-roles --list
   energy-agents-roles --output outputs/career_roles
   energy-agents-roles --role career_powergrid_expert --output outputs/grid_role
   python examples/enterprise/plot_career_role_agents.py

The CLI exports deterministic work plans for all roles by default. Each role
first inspects its required inputs and then proposes its named deliverables.
Missing inputs, evidence types, review checks, suggested KPIs and handoffs are
retained separately from planner text. Counts measure input presence only.

.. code-block:: python

   from energy_agents.career_roles import run_career_agent, synthetic_career_case

   result = run_career_agent("career_powergrid_expert", synthetic_career_case())
   print(result["inspection"]["missing_inputs"])
   print(result["proposal"])

Supply your own brief
----------------------------------------------------------------------------------------------------

A case has exactly ``id``, ``objective``, ``inputs`` and ``evidence``. Each named
input has ``text`` and ``evidence_ids``. Each evidence entry has a ``kind``
(``synthetic``, ``user_supplied`` or ``reference_only``) and a ``summary``.
No evidence kind implies independent verification. A URL in a summary is not
automatically fetched. Neutral source labels record role coverage and cannot serve
as evidence for a customer's project.

.. code-block:: python

   case = {
       "id": "ems-review", "objective": "Prepare an EMS acceptance plan",
       "inputs": {
           "acceptance_criteria": {
               "text": "Review the supplied criteria and identify gaps.",
               "evidence_ids": ["criteria-v1"],
           },
       },
       "evidence": {
           "criteria-v1": {"kind": "user_supplied", "summary": "Customer's draft criteria"},
       },
   }
   result = run_career_agent("career_scada_ems_engineer", case)

Live model proposals
----------------------------------------------------------------------------------------------------

``CareerRolePlanner`` uses the existing explicit HTTPS Chat Completions adapter.
The endpoint receives generic role metadata, the objective, the role's required
inputs and their referenced evidence, and any caller-supplied upstream handoffs.
Unrelated case inputs are excluded. Upstream text is caller-controlled and should
contain only information permitted for that endpoint. The offline example makes
no model calls; live quality has not been evaluated.

.. code-block:: python

   from energy_agents.career_roles import CareerRolePlanner

   planner = CareerRolePlanner(
       "career_scada_ems_engineer",
       endpoint="https://your-provider.example/v1/chat/completions",
       model="your-model",
       api_key_env="ENERGY_AGENTS_API_KEY",
   )
   # Sends the selected inputs to your configured endpoint:
   # result = run_career_agent("career_scada_ems_engineer", case, planner)

The model must return one ``inspect_role_inputs`` call with empty arguments,
followed by ``submit_proposal``. A proposal includes every required deliverable
with ``name``, ``content``, ``evidence_ids`` and ``assumptions``, plus an
``open_questions`` list. Unsupported deliverables require assumptions. The runner
checks tool order, deliverable names, reference membership and call budgets;
it does **not** check whether narrative claims follow from those references.

Orchestration and existing workflows
----------------------------------------------------------------------------------------------------

``career_roles()`` returns the existing ``RoleSpec`` type.
``career_runners()`` registers every role for ``run_orchestrator``; task payloads
are cases and upstream reports are copied into the next role's context. The
gallery chooses five roles for value discovery, requirements, solution planning,
security and implementation handoff. Failed dependencies block downstream work.
Choose an explicit DAG of at most 50 tasks, consistent with the existing runner;
the CLI's 53 independent work plans are not one dependency graph.

Suggested handoffs are routing hints, not automatically scheduled work. Existing
:doc:`forward_deployed`, :doc:`python_engineer`, :doc:`pv_operations`, and
:doc:`data_center_design` workflows retain their contracts. These new role agents
can prepare inputs for them but do not silently run their tools. Before proposing
an Energy Data Insights integration, inspect its capability manifest and verify
the exact connector or method; an agent prompt cannot create an integration.

Scope and review
----------------------------------------------------------------------------------------------------

Default results are **scripted work plans**. Optional model results are proposals.
Neither is proof of completed engineering, finance, audit, legal or HR work.
Success means the bounded protocol accepted the proposal's structure. Required
input gaps cannot be removed by planner text; human review always remains true.
There are no deployment, plant-control, banking, purchasing, CRM-writing or
messaging tools in this runtime. KPIs are proposed measurements, not calculated
business results. The runner does not read linked standards or certify compliance.

API
---

.. automodule:: energy_agents.career_roles
   :members:
