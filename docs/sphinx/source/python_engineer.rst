Python, data science and ML engineer
====================================

The ``python_ml_engineer`` role turns energy questions into reviewable Python
source bundles: reusable methods, tests, runnable examples and explanations.
It covers scientific Python, data pipelines, forecasting, ML evaluation,
performance and reproducibility across renewable technologies.

Discover it with ``role_catalogue(include_engineering=True)`` from
``energy_agents.roles``. The default catalogue preserves the existing PV contract.

The implementation has a provider-independent bounded proposal/repair loop and
an optional live LLM adapter. It does not autonomously edit repositories or run
shell commands. A syntactically accepted proposal is **not tested code**, a secure
program, a verified scientific method, or evidence of expert model performance.
Human or CI review must assess semantics, dependencies, data leakage and results.

Energy Data Insights alignment
------------------------------

The role instruction incorporates the inspected upstream
`README <https://github.com/julianascencio/energy-data-insights/blob/main/README.md>`_
and `contributing guide <https://github.com/julianascencio/energy-data-insights/blob/main/CONTRIBUTING.md>`_
(read 2026-11-05; contributing blob ``3140ffbe009e3ec4dbce3d929648fe4712a920ec``).
It separates provider connectors, reusable methods and study orchestration;
requires units, timestamps, provenance, missing-value handling and offline examples;
and requests chronological ML validation with physical/persistence baselines.

This is an engineering contract, not an automatically refreshed index of every
upstream function. Supply current repository instructions, dependency files,
relevant source and examples as context for each task. The agent must acknowledge
missing API evidence rather than invent imports. Target-repository quality commands
must come from its current configuration (EDI uses uv/ruff/ty/pytest; this repository
uses pip/ruff/pytest). It does not install or depend on Energy Data Insights.

Live use
--------

.. code-block:: python

   from energy_agents.python_engineer import (
       PythonEngineeringPlanner, run_python_engineer,
   )

   planner = PythonEngineeringPlanner(
       endpoint="https://YOUR_PROVIDER/chat/completions",
       model="YOUR_MODEL",
   )
   # Supply reviewed contents from the target checkout, including relevant APIs.
   context = {
       "CONTRIBUTING.md": contributing_text,
       "pyproject.toml": dependency_text,
       "existing_method.py": relevant_source,
   }
   result = run_python_engineer(
       "Implement a leakage-free solar forecasting benchmark with physical and "
       "persistence baselines, chronological holdout and a runnable gallery example.",
       context, planner, max_calls=3,
   )

Set ``ENERGY_AGENTS_API_KEY`` in the environment. Only send context appropriate
for disclosure to the explicitly configured provider; no automatic credential or
repository discovery occurs. Provider/network failures propagate to the caller.
Rejected protocol or syntax responses can be repaired within 1–5 calls. The
returned bundle remains in memory; neither its code nor suggested commands run.
No live-provider run has been validated by the offline example.

Review and handoff
------------------

Review proposed paths, code, dependencies, licenses and assumptions, then apply
approved files in an isolated checkout. Run target lint, type checks, independent
tests, package and strict documentation builds. Evaluate forecasting quality on
untouched data, document uncertainty and verify business assumptions separately.
The role can receive tasks from asset/performance agents, but is deliberately
separate from the five-role operational PV workflow and its accounting outputs.

Run the deterministic gallery example:

.. code-block:: bash

   python examples/engineering/plot_python_engineer.py

It returns a synthetic forecast-error utility proposal and clearly reports that
only shape, paths and syntax were checked. It neither trains a model nor claims
ML accuracy or revenue improvement.
