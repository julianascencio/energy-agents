Operations and asset management
===============================

Ask: **Where is the portfolio losing energy and money, which evidence is
missing, and what should the team investigate first?**

The first executable slice connects the existing five PV professional roles to
Energy Data Insights through a shared service, Python API, CLI and local MCP
server. It includes a portable HTML decision workspace and JSON audit exports.
The four-site example is entirely synthetic; the calculations actually execute
in ``energy_methods.operations``. No LLM key is needed for the deterministic demo.

.. raw:: html

   <p><a class="sd-btn sd-btn-primary" href="_static/operations/report.html">Open the interactive portfolio demo</a></p>

.. image:: gallery/operations/images/sphx_glr_plot_asset_management_001.png
   :alt: Four synthetic assets, their event-associated losses and conditional repair economics

Product pattern
---------------

`PVSpec <https://pvspec.com/>`_ presents design through a web app, API and MCP.
Its `onboarding guide <https://pvspec.com/wp-content/uploads/2026/10/Onboarding_Guide_User_v0.3.pdf>`_
describes conversational access to design tools. This project applies that
interaction pattern to operations with original implementation and interfaces;
it does not integrate with PVSpec or reuse its implementation.

.. list-table:: Ownership across the repositories
   :header-rows: 1
   :widths: 30 70

   * - Layer
     - Responsibility
   * - MCP client / user
     - Ask questions, select tools, review evidence and proposed actions.
   * - Energy Agents
     - Portfolio snapshots, role handoffs, evidence checks, economic ranking,
       work-order drafts, reports and tool interfaces.
   * - Energy Data Insights
     - Reusable methods and data connectors. This slice executes the daily
       operations ledger; weather, reliability and other methods remain extension points.
   * - Source systems
     - SCADA, meters, event logs, baseline models, contracts and CMMS. This slice
       accepts a prepared JSON snapshot; live source connectors are not added here.

Implemented workflow
--------------------

1. Load a portfolio snapshot and validate each asset's existing PV case schema.
2. Execute EDI daily energy accounting, keeping faults, curtailment, unresolved
   deficits, surplus and missing days separate.
3. Run Performance Engineer, Reliability Engineer, Commercial Asset Manager,
   Maintenance Planner and Technical Asset Manager. Reconcile their accounting
   to EDI and reject disagreements.
4. Hold incomplete datasets out of economic ranking. Rank positive conditional
   repair opportunities only within the same currency, date window and timezone.
5. Return evidence-linked drafts and required closure evidence for human review.

An MCP host LLM decides which tools to call and how to explain results. The
default internal role sequence is scripted and labelled accordingly. Python
callers can supply the existing role planner adapters through
``service.review_asset(asset_id, planners=...)``. The live LLM quality of this
portfolio workflow has not been evaluated; the protocol and tools are tested.

Install and run
---------------

Use **Python 3.12+** for this integration; the base Energy Agents package still
supports Python 3.11. From the Energy Agents checkout:

.. code-block:: bash

   python -m pip install -e ".[dev,docs,mcp]"
   python -m pip install -r requirements/operations.txt
   energy-agents-ops --output outputs/operations
   python examples/operations/plot_asset_management.py

Open ``outputs/operations/report.html``. The export also includes input and result
JSON, work-order drafts and a SHA-256 manifest. CLI writes to its explicit output
directory; MCP tools only return objects and do not write files.

``requirements/operations.txt`` pins the public PyPI release and wheel SHA-256
tested with this workflow.
The operations module itself uses only the standard library; CI and docs install
that package with ``--no-deps`` to avoid unrelated scientific/model dependencies.
Normal installation includes EDI's declared dependencies for its wider methods.
The backend retains its own repository license; importing it does not relicense it.

.. code-block:: python

   from energy_agents.operations import OperationsService, synthetic_portfolio

   service = OperationsService(synthetic_portfolio())
   review = service.review_portfolio()
   action = review["summaries"][0]["ranked_actions"][0]
   draft = service.draft_work_order(action["asset_id"], action["action_id"])
   assert draft["status"] == "draft"
   assert draft["external_work_order_id"] is None

Bring a real portfolio
----------------------

Replace ``assets`` with existing PV cases as documented in :doc:`pv_operations`:

.. code-block:: python

   portfolio = {
       "schema_version": "1.0",
       "portfolio_id": "my-portfolio",
       "assets": [validated_pv_case],
   }

.. code-block:: bash

   energy-agents-ops --input portfolio.json --output outputs/my_portfolio

Each case needs a unique ``plant_id``, currency, timezone, version, evidence
registry, expected/actual daily MWh, daily prices, mutually exclusive event
labels and explicit recurrence/recovery/cost assumptions. ``None`` actual energy
means missing data, not a zero-production day. Expected energy must use the same
meter boundary and daily window as the actual measurement. Event associations
must be reconciled upstream. Dates omitted between the first and last record
are detected; dates missing outside the supplied window are unknowable.

MCP connection
--------------

For a client that supports local stdio servers, configure absolute paths:

.. code-block:: json

   {
     "mcpServers": {
       "energy-operations": {
         "command": "/absolute/path/to/venv/bin/energy-agents-ops-mcp",
         "args": ["--input", "/absolute/path/to/portfolio.json"]
       }
     }
   }

Omit ``args`` for the synthetic demo. The operator chooses the input file at
startup; model tools cannot supply arbitrary file paths or network URLs.
This is a local connection, not a hosted OAuth endpoint. The SDK dependency is
bounded to its documented v1 maintenance API (``mcp<2``).

.. list-table:: Tools
   :header-rows: 1

   * - Tool
     - Result
   * - ``list_assets``
     - Asset IDs, technology, currencies, periods and evidence origins.
   * - ``review_asset``
     - EDI ledger, five role reports, trace, assumptions and proposed actions.
   * - ``review_portfolio``
     - Grouped review and eligible economic investigation ranks.
   * - ``get_evidence``
     - Source descriptions, origin and verification labels.
   * - ``draft_work_order``
     - Draft linked to a valid asset/action snapshot, with preconditions and closure evidence.

Suggested prompt: "Review this portfolio. Show missing data, rank economically
attractive fault investigations, explain the leading case, and draft its work
order with source evidence. Keep curtailment and unverified causes separate."

Evidence and decision boundaries
--------------------------------

The demo's northern asset has 40 fault-associated MWh at 50 EUR/MWh. At 80%
conditional recovery, gross value is 1,600 EUR and net after a 100 EUR intervention
is **1,500 EUR**. The same defect at the southern asset has a 2,000 EUR intervention
cost, making its scenario negative. Western missing data blocks ranking. The grid
asset's curtailment produces a commercial investigation, not repair value.

Negative prices remain signed; surplus is not silently netted into positive losses.
No missing energy is invented, no six-day value is annualized, and no currencies
are converted. The data hold is a ranking rule, not a calibrated confidence score.
Synthetic evidence stays labelled. Unverified evidence can support an investigation
proposal, never a verified diagnosis or approved work order. Economic ranking does
not replace safety criticality, engineering review or constrained crew scheduling.

The report carries input and backend source hashes, evidence IDs, role traces,
limitations and assumptions. Numerical reconciliation does not validate the
baseline or establish the truth of source labels. No SCADA command, procurement,
CMMS dispatch, payment, email or other external write exists in this interface.

Expansion path
--------------

.. list-table:: Follow-on product modules (not implemented in this slice)
   :header-rows: 1
   :widths: 30 70

   * - Module
     - Required next integration
   * - Automated daily briefing
     - Authenticated SCADA/event ingestion, freshness checks and scheduled snapshots.
   * - Predictive maintenance
     - EDI failure-rate/lifetime methods with device exposure, censored history and calibrated validation.
   * - Cleaning and weather response
     - EDI weather/degradation methods, ground measurements and intervention-specific economics.
   * - Warranty and contract management
     - Structured contract obligations, evidence packs and approved claim workflows.
   * - Closed-loop maintenance
     - CMMS adapter, approval persistence, idempotent writes and post-intervention verification.
   * - Wind and BESS portfolios
     - Technology-specific schemas, diagnostics and revenue contracts before enabling ranking.
   * - Hosted platform
     - Tenant isolation, identity, asset-level permissions, persistent audit storage and authenticated MCP/API.

Validation
----------

.. code-block:: bash

   python -m pytest tests/test_operations_service.py tests/test_operations_mcp.py
   ruff check .
   sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

The protocol test starts a real stdio subprocess, initializes an MCP session,
discovers tools, reviews the portfolio, obtains a draft and rejects an unknown
asset. EDI independently tests arithmetic, missingness, invalid inputs, calendar
gaps, negative prices and exclusion of curtailment from repair recovery.
