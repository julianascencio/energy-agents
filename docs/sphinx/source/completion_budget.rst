Battery project completion budget
====================================================================================================

Yukon Energy announced on **23 November 2026** that it had terminated its
Whitehorse BESS contractor and would manage completion as prime contractor.
The utility targets completion in 2027 and a CAD35m budget, with outstanding
scope and pricing still to be confirmed. The original CAD25.7m contract value
is not a paid-cost ledger. Source: `Yukon Energy announcement
<https://yukonenergy.ca/about-us/news-events/yukon-energy-terminates-contract-with-sungrid-solutions-and-announces-new-approach-to-complete-the-whitehorse-battery-storage-project>`_.

**All model inputs are synthetic. This is not an estimate of Whitehorse's
remaining cost, contractor liability, grant entitlement or battery condition.**
The announced funding figures (CAD16.5m commitment, CAD15m received and CAD1.65m
remaining) do not reconcile exactly, so they are not used as a cash ledger.

Decision and buyer
------------------

An owner, utility capital-projects team or lender could commission a remaining-
scope and funding review after contractor termination. The hypothetical offering
is an auditable invoice/quote reconciliation and scenario report, using the
existing Project Finance Analyst and deterministic tools. No new professional
agent is added. No willingness-to-pay, fee, realised saving or LLM advantage is
claimed. A commercial use of the optional EDI dependency needs appropriate rights.

The baseline is a replacement EPC quote. The intervention is owner-managed
packages for the same deficiencies, integration, commissioning and management
scope. The model rejects omitted or duplicate scope, overlapping invoice/package
IDs, invalid payment schedules and stale handoffs. This schema check cannot prove
that a real engineering scope is complete or that invoice descriptions are truthful.

Method and units
----------------

The horizon is twelve months from the hypothetical decision, in nominal CAD,
undiscounted and before tax. Let S be costs already paid, U certified unpaid
obligations and Q the new remaining-work quotes. Costs already paid are excluded
from the prospective comparison but included in the total project budget:

.. math::

   CTC_p = U + Q_p,\qquad FAC_p = S + CTC_p,\qquad H_p = B-FAC_p

.. math::

   \Delta CTC = CTC_{EPC}-CTC_{owner},\qquad
   u^* = Q_{EPC}/Q_{owner}-1

The price crossover assumes identical work scope and fixed baseline EPC quotes;
only the owner's new quotes increase. It is an algebraic cost threshold, not an
approval. Common unpaid invoices do not receive the quote multiplier. No taxes,
interest, operating cash flows, legal fees outside the quotes, discounting or
probabilistic distributions are modelled. Quotes include assumed contingency;
actual contingency must be established through client risk assessment.

Monthly funding accumulates future outflows less opening cash and eligible
receipts. All outflows occur before receipts within a month; the maximum positive
balance at that point is peak new funding. End-of-horizon funding is a separate
output. Grants are assumed conditional on completion and received at completion
plus a lag and scenario delay. Receipts after the horizon are disclosed and not
counted. Disputed recoveries are always excluded. Neither grants nor damages
reduce the gross construction budget. A funding limit is a synthetic ceiling;
borrowing, interest or financing approval is not simulated.

The same synthetic battery service assumptions apply to both plans. The check is
one fully charged event, using DC capacity times usable-capacity fraction, SOC
window and discharge efficiency, bounded by inverter MW. It does not establish
cold-exposure damage, safety, warranty validity, commissioning, winter dependable
capacity, recharge or grid-service certification. Failed service scenarios retain
the diagnostic budget ledger but return null conditional savings.

Reference results
-----------------

The example assumes CAD24m paid, CAD2m unpaid, new EPC quotes of CAD9m and owner
quotes of CAD7.6m. Both complete in month nine. CAD1m opening cash, CAD8.8m available
new funding and a CAD1.5m grant in month ten are assumptions. A disputed CAD2m claim
is excluded. The assumed battery is 10 MW / 60 MWh DC; target 10 MW for four hours,
100% initial SOC, 10% reserve and 95% discharge efficiency.

.. list-table:: Synthetic reference ledger (CAD millions)
   :header-rows: 1

   * - Metric
     - Replacement EPC
     - Owner prime
   * - Forward cost to complete
     - 11.0
     - 9.6
   * - Gross forecast at completion
     - 35.0
     - 33.6
   * - Gross budget headroom
     - 0.0
     - 1.4
   * - Peak new funding
     - 10.0
     - 8.6
   * - End-of-horizon new funding
     - 8.5
     - 7.1
   * - Peak funding shortfall
     - 1.2
     - 0.0

Conditional forward-cost reduction is CAD1.4m. Owner quote uplift of **18.4211%**
erases that reduction; at 20%, owner completion costs CAD120,000 more. Delaying
the grant to month fourteen raises horizon-end funding by CAD1.5m, with no change
to the earlier peak or gross budget. At a hypothetical 70% usable capacity, only
35.91 MWh AC / 8.9775 MW is available; the cost comparison is withheld. These are
scenario outputs, not realised savings, actual price quotes or field validation.

Workflow, evidence and reproduction
------------------------------------------------

Packaged ``data/recovery/skill.json`` contains the reusable user request, role
mandates, input schema, allowed tools, evidence requirements, handoffs, output
contract and acceptance criteria. ``source.json`` preserves the announcement
facts and dates. ``case.json`` keeps synthetic costs and performance separate.
The SHA256-bound evidence audit precedes finance; finance recomputes it to reject
altered or stale handoffs. External actions are unavailable to the orchestrator.

From the repository root::

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-recovery --output outputs/recovery
   python examples/business/plot_completion_budget.py
   python -m pytest tests/test_recovery.py
   ruff check .
   python -m build

The core screen needs Python 3.11+ and no keys or network. It exports inputs,
report, audit, workflow, skill, capability provenance and actual EDI execution
status. The direct deterministic calculation is the scripted workflow's baseline;
parity is checked, with no claimed agent superiority. No LLM runs were performed;
LLM cost, latency and tokens remain unknown.

Optional local EDI execution on Python 3.12+::

   python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
   energy-agents-recovery --edi --output outputs/recovery_edi
   MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

The existing pinned ``energy-methods==0.1.1`` wheel supplies the stdlib-only
``bess_service_envelope``. Its source was re-inspected at EDI commit
``eea4916ef3cd43a5805c9584b7f4bcf5df4c3505``; blob
``c3d2936e718bb7f30546aa5a15910c92230f1b54`` is unchanged from the augmentation
adapter. Installed source SHA256 must match
``0653d403fe530320e2d8f517d055ba1fb3c81ad86343e16222a707fa29cec2dd``.
The adapter actually executes four service scenarios when requested, crosschecking
MW and MWh. Discovery alone is not execution. Merchant-finance and margin-relief
methods were inspected but do not reconcile construction budgets; no upstream
source or scientific method is copied. This is a focused catalogue refresh,
not a claim that all EDI capabilities were revalidated.

See the :doc:`gallery/business/plot_completion_budget` for the tables and plots.
