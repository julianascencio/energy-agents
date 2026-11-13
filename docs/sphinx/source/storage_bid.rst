Storage bid preparation stage gate
==================================

`NYSERDA's 12 November 2026 announcement <https://www.nyserda.ny.gov/About/Newsroom/2026-Announcements/2026-11-12-NYSERDA-Announces-2026-Bulk-Energy-Storage-Solicitation>`_
introduces a two-step bulk-storage procurement: qualification precedes invited
bids. This motivates a developer's decision about when to spend on preparation.
The release's weekday and calendar deadline disagree; confirm the actual tender
documents before relying on a date. This example does not determine eligibility.

Business and model
------------------

A development director or finance analyst could buy a tender-readiness review
and development-budget sensitivity pack. Willingness to pay is unmeasured.
Baseline: pay qualification and full preparation costs now. Intervention: pay
qualification and staging overhead now, then full preparation only if qualified.
No bid is a third alternative, with zero incremental cash flow. Existing sunk
costs are excluded from every strategy.

All economic inputs and results are **synthetic**, in USD present value at the
decision date. Qualification probability p is 60%; conditional award probability
q is 25%. Staging reduces q by an assumed relative 10% (to 22.5%). Qualification
cost is $40,000, full preparation $200,000 and staging overhead $10,000. Staged
preparation is paid after three months, discounted at 8% annually. Project NPV
conditional on award is $2 million, already at decision date, net of all project
costs but excluding application costs. It is not grant income, ISC income or an
estimate for any actual project. There is no additional discount on that NPV.

With D = (1+r)^(-months/12), upfront expected net value is p*q*V-C1-C2.
Staged expected net value is p*q*(1-h)*V-C1-H-p*C2*D. Thus staging saves
unnecessary preparation spending but may lose expected project value. The tool
also reports expected spending, worst loss across nonzero-probability branches,
and break-even award-conditional project NPV. A zero award probability yields
an undefined break-even (JSON null). No bid can dominate both strategies.
There is no calibrated probability, risk utility, bid-price optimization,
financing, tax or ISC settlement model. A positive expected value is not approval.

Reusable workflow and provenance
---------------------------------

The existing finance role and bounded orchestrator run evidence validation then
finance. The gate checks schemas, not the truth of external evidence. All gaps
survive the handoff. Packaged ``data/bid/skill.json`` contains the actual request,
role mandate, schema, allowed tools, handoffs and acceptance criteria. Only
registered callbacks run; the optional planner cannot submit bids, spend money,
contact third parties or execute controls. The default path is scripted and
key-free. No live LLM was run; tokens, latency and provider cost are unknown.
Direct deterministic calculation and workflow outputs must match exactly;
there is no agent-superiority claim.

The bounded ``edi_context`` adapter exposes source-derived metadata at EDI commit
``53f47b87fe9a6213e85a7fe60d4cf2599ec26658``. The BESS catalogue source was fetched
and its public symbols and SHA-256 recorded. It validates asset provenance and
capacity scope; it cannot establish solicitation eligibility or win probability.
Existing procurement/debt catalogues were also consulted. No EDI numerical method
is executed here and no dependency or duplicated asset validator is introduced.
The full pre-existing gallery uses the pinned public energy-methods distribution.

Reproduce
---------

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-bid --output outputs/storage_bid
   energy-agents-bid --case my_case.json --output outputs/my_bid
   python examples/business/plot_storage_bid.py
   python -m pytest tests/test_bid.py

The CLI exports exact inputs, input hash, workflow trace, report and EDI metadata.
The gallery prints a numerical table and plots qualification/competitiveness
sensitivity. No live data service is needed. Optional new inputs must preserve
synthetic classification until a separately validated observed-data path exists.
