Preferred equity cash waterfall
===============================

A solar/storage developer can reduce initial common-equity funding by introducing
preferred capital, but gives up future distributions. This advisory screen reuses
the Project Finance Analyst and the bounded evidence-to-finance orchestrator.
A plausible paid offering is a financing term-sheet scenario audit; willingness
to pay and customer benefit are unverified.

News and evidence
-----------------

`Captona's 10 November 2026 announcement <https://www.businesswire.com/news/home/20261110915054/en/Sunrun-Partners-with-Captona-on-its-Latest-Preferred-Equity-Project-Finance-Transaction>`_
reports investment across 9,400 residential projects, with 74 MW solar and 110 MWh
storage. These observed portfolio facts are separate from the illustrative model.
No actual coupon, invested capital, fees or cash distribution terms were disclosed.
The model is not a valuation of that portfolio and does not compute its tax credits.

Method and assumptions
----------------------

All economics are **synthetic nominal USD**. Both strategies use identical cash
already net of operating costs and senior debt. Baseline: common equity supplies
the entire USD 10m equity requirement. Intervention: USD 4m preferred capital,
8% annual cumulative non-compounding coupon, USD 100k initial fee. Horizon is five
years; discount rate is 10%. Annual available cash is USD 0.5/0.6/0.8/1.0/1.2m;
terminal sale proceeds after debt repayment add USD 12m in year five.

Each year pays current and unpaid coupons first. Terminal remaining cash repays
preferred capital before common equity; unpaid capital/coupons are reported as
shortfalls. No interim redemption or residual preferred participation occurs.
Each year's available cash equals coupon, redemption and common distributions.
Sponsor NPV subtracts its initial contribution, including fees. Investor NPV
subtracts its initial preferred capital. With a shared discount rate, incremental
sponsor NPV plus investor NPV equals minus the fee: this is allocation of project
value, not new operational value. Initial cash saved is not profit.

The gallery varies exit proceeds and operating cash. It assigns no scenario
probabilities. No extra debt, capital calls, refinancing, taxes, legal guarantees
or dispatch are modelled. Negative cash inputs are rejected because this bounded
waterfall does not fund deficits. Real documents may allocate losses differently.
Schema validation is not source verification, credit approval or legal review.

Workflow and reproduction
-------------------------

``data/equity/skill.json`` contains the reusable request, mandate, schema, tools,
handoffs, output contract and acceptance criteria. Invalid evidence blocks finance;
unknown actions and premature handoffs are rejected. Outputs retain input hash,
evidence gaps, cash ledger and unknown LLM cost/latency/tokens. Scripted workflow
matches the deterministic baseline; no agent superiority is claimed.

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   python -m pip install --no-deps --require-hashes -r requirements/operations.txt
   energy-agents-equity --output outputs/preferred_equity
   python examples/business/plot_preferred_equity.py
   python -m pytest tests/test_equity.py

The case, CLI and gallery need no network or keys after installation. ``--case``
accepts an explicitly synthetic scenario JSON; it does not retrieve private terms.
``edi_context()`` returns bounded source-derived metadata recorded at EDI commit
``3d6000b9d981bbbf594eeee296a391c03f78c6e7``. The inspected real-JPY wind LCOE
method has no financing model and is not executed here. The full repository gallery
uses the existing public hash-pinned energy-methods dependency where applicable.
