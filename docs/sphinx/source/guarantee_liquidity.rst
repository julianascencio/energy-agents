Bank-guarantee liquidity and economic cost
==========================================

The existing Project Finance Analyst supports a developer's treasury team in
comparing hypothetical collateral terms for equal bank-guarantee liabilities.
A plausible paid offering is a bank-offer and contingent-liquidity diligence
report. No customer demand, actual bank offer or realised saving is evidenced.

News and boundaries
-------------------

`Enlight's 16 November 2026 announcement <https://www.globenewswire.com/news-release/2026/11/16/3403923/0/en/enlight-renewable-energy-and-shemen-yielding-real-estate-sign-agreement-to-advance-development-of-a-data-center-with-planned-power-capacity-of-up-to-150-mw-in-israel.html>`_
reports estimated aggregate guarantees of NIS 334 million, split equally between
the partners, for a proposed 150 MW data-centre connection. Final regulation,
connection approval and other approvals remain conditions. The estimate is source
metadata; every bank term and risk parameter below is synthetic.

Method
------

For sponsor guarantee face G, collateral fraction c, annual fee f, horizon T,
setup fee S, net opportunity spread r, call probability p and net loss fraction L:

* Restricted cash = G c; guarantee face remains G under both offers.
* Upfront fees = G f T + S (all horizon fees paid upfront by assumption).
* Opportunity cost = G c r T; r is net of collateral interest.
* Expected net call loss = G p L, independent of collateral under equal-risk assumptions.
* Total economic cost = fees + opportunity cost + expected net call loss.
* Initial cash needed = collateral + upfront fees.
* Additional cash on a full call before recovery = G (1-c).
* Full-call cash including initial cash = G + upfront fees.

Collateral is released at expiry if not applied to a call. It is neither expense
nor profit. Opportunity cost is an economic counterfactual, not another bank
payment. Expected loss is not a liquidity reserve. Net recoveries occur after the
full-call cash requirement. This simple undiscounted nominal-NIS screen has no
compounding, tax, FX, lease, construction cash, legal eligibility or dispatch model.
A liquidity test against the initial budget does not establish full-call solvency.

Synthetic example
-----------------

One partner has NIS 167m face exposure. The horizon is two years, net opportunity
spread 4%/year, full-horizon call probability 2%, conditional net loss fraction 40%,
and initial liquidity budget NIS 60m. Baseline: 100% collateral, 0.5% annual fee,
no setup fee. Alternative: 25% collateral, 1.5% annual fee, NIS 0.2m setup fee.

Baseline economic cost is NIS 16.366m versus NIS 9.886m for the alternative:
NIS 6.48m modelled reduction. Restricted cash falls by NIS 125.25m. Initial cash
needs are NIS 168.67m versus NIS 46.96m. The alternative fits the initial budget,
but a full call requires another NIS 125.25m before recovery. Total full-call cash,
including initial cash and fees, is NIS 172.21m. Both retain NIS 167m liability.
The gallery stresses collateral fractions and fees; positive savings are not
forecast probabilities. Rates and counterparty risk could change together in practice.

Workflow and reproduction
-------------------------

``data/guarantee/skill.json`` stores the actual request, role mandates, input schema,
allowed tools, evidence requirements, handoffs and acceptance criteria. The
bounded orchestrator validates evidence metadata before handing isolated input to
the existing finance role. Unknown tools and premature finance actions fail.
Human legal, engineering and bank review remain mandatory for real decisions.

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-guarantee --output outputs/guarantee
   python -m pytest tests/test_guarantee.py
   python examples/business/plot_guarantee_liquidity.py

After installation, default and custom ``--case`` runs need no keys or network.
Exports include the input hash, workflow report, source status and evidence gaps.
The scripted workflow equals the direct deterministic baseline. No LLM was run;
provider cost, latency and tokens are unknown. No agent superiority is claimed.

The bounded EDI metadata adapter records source inspection at commit
``fc63c5f97e6513e7f290340ddfdce0b80962644a``. The inspected wind LCOE method has
real-JPY unlevered economics and does not implement guarantee liabilities. It is
not executed or duplicated. Existing repository EDI execution adapters remain
available. Full gallery validation uses the public wheel pinned in
``requirements/operations.txt``.
