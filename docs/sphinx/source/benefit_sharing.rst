Benefit-sharing cash flows
====================================================================================================

The `CIS Tender 12 page <https://asl.org.au/tenders/cis-tender-12-nem-generation>`_
opened on 27 November 2026. The 26 November guidelines, section 4.3, describe an
optional 500 MW First Nations allocation within a 5 GW generation tender.
They request financial evidence for an interest of at least 5%, or equivalent
sharing, alongside engagement, governance and commercial evidence. Assessment
remains discretionary. This example makes **no tender qualification finding**.

**All financial data below are synthetic.** A gifted 5% equity stake is a model
assumption, not a tender requirement. Equal discounted receipts do not establish
equivalent rights, risk, liquidity, voting power, consent or eligibility.

Buyer and decision
------------------

A renewable-project developer, community investment adviser or finance team could
pay for an auditable comparison of proposed benefit-sharing cash flows. The
commercial offering would be scenario preparation and financial review alongside
qualified community and legal advisers. No willingness-to-pay or actual fee is
measured. The existing Project Finance Analyst and orchestrator suffice; no new
professional agent or external-action capability is added.

The decision is how two specified proposals allocate financial value and funding
risk. Baseline: common-equity sharing. Intervention: gross-revenue sharing.
The no-sharing sponsor NPV is a diagnostic reference, not a recommended policy.
This differs from the preferred-equity financing example: no coupon seniority,
redemption waterfall, refinancing benefit or award probability is modelled.

Model and output contract
-------------------------

Inputs are nominal AUD, annual year-end cash flows over 1..50 years, and a common
nominal discount rate. Gross revenue and cash distributable after debt and project
tax but before sharing are independent supplied forecasts. Cash must be between
zero and gross revenue. Terminal proceeds are after debt and tax, separately
supplied; they are not annual revenue. The cash forecasts remain fixed across
plans: tax shields or covenant changes caused by sharing are not modelled.

Let D_t be distributable cash, G_t gross revenue, T terminal proceeds at H,
e equity fraction, s revenue fraction and I_t an indicator for the inclusive
revenue-sharing years. Contributions C are paid by recipients at year zero,
and reduce sponsor initial funding. Setup S is sponsor-paid at year zero;
annual administration A is sponsor-paid only while the arrangement is active.

.. math::

   B_{equity,t}=eD_t+eT\mathbf{1}_{t=H},\qquad B_{revenue,t}=sG_t I_t

.. math::

   V_p=\sum_{t=1}^H\frac{B_{p,t}}{(1+r)^t}-C_p,\qquad
   K_p=V_p+S_p+\sum_{t=1}^H\frac{A_{p,t}}{(1+r)^t}

Recipient NPV V and incremental sponsor cost PV K are separate KPIs. Sponsor
NPV equals the no-sharing NPV less K. Contributions are transfers, not project
revenue. Equity contribution is bounded by its share of initial equity; revenue
contribution cannot exceed total initial equity in this simplified model.

.. math::

   s^*=\frac{V_{equity}+C_{revenue}}{\sum_t G_t I_t/(1+r)^t}

This is only a recipient-NPV parity fraction. A zero denominator or negative
numerator returns null; a fraction above one is reported as infeasible. It is
not an official calculation of economic interest. The model cannot assess a
real arrangement's nonfinancial rights or tender merit.

Operating funding gaps are max(0, operating payment + admin - D_t). Payments are
not silently capped: sponsor top-ups would be needed. Terminal receipts cannot
cover earlier operating shortages within that year. The total gap sums annual
requirements; it is not peak borrowing or a financing commitment. No capital
calls, borrowing costs, recipient tax, stochastic probability or field validation
is included. Tax and debt treatment must be reworked for any actual project.

Reference assumptions and results
---------------------------------

Twenty years; AUD50m initial equity; AUD30m annual gross revenue; AUD8m annual
distributable cash; AUD40m terminal equity proceeds; 8% discount. Both recipient
upfront contributions are zero. Equity: 5%, AUD100k setup, AUD20k/year admin.
Revenue: 1.5% for years 1..20, AUD200k setup, AUD50k/year admin. All are assumptions.

.. list-table:: Modelled values, nominal AUD discounted to year zero
   :header-rows: 1

   * - Proposal
     - Recipient NPV
     - Sponsor incremental cost PV
   * - Gifted equity
     - 4,356,355
     - 4,652,718
   * - Revenue sharing
     - 4,418,166
     - 5,109,074

The revenue proposal adds about AUD61,811 recipient NPV while costing the sponsor
about AUD456,355 more. Neither number is realised revenue or saving. Algebraic
recipient parity is approximately 1.4790% of gross revenue, holding all other
assumptions fixed. Shorter sharing duration requires a larger fraction for the
same NPV. The gallery varies duration and discount rate and stresses operating
cash, including cases where revenue payments require additional funding.

Workflow and reproduction
-------------------------

``data/sharing/skill.json`` is the versioned reusable user request, role mandate,
input schema, allowed tools, evidence gate, handoffs and acceptance contract.
The evidence runner checks the packaged source snapshot and schema; it does not
verify external truth or consent. Finance recomputes the SHA256-bound audit to
reject altered handoffs. The orchestrator admits only registered ready tasks;
agreements, contacts, bid submissions, trading and controls are unavailable.

From the repository root::

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-sharing --output outputs/sharing
   MPLBACKEND=Agg python examples/business/plot_benefit_sharing.py
   python -m pytest tests/test_sharing.py
   ruff check .
   python -m build
   MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

Core execution needs Python 3.11+ and no network or keys. JSON exports include
inputs, audit, report, workflow, prompts and source-derived EDI catalogue.
The direct deterministic calculation is the scripted workflow baseline; exact
parity is checked. No LLM has been run: cost, latency and tokens are unknown,
and no agent advantage is claimed. There is no optional live submission path.
To build the entire existing gallery, also install its pinned operations backend::

   python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt

The focused EDI catalogue records commit
``0f3c90cbb13b8ecc72f5d6c6b44beb319a7d4aaf``. The merchant BESS method supplies
EUR operating/debt cashflows, not AUD community rights; the previously verified
service-envelope method checks physical capacity. Neither is appropriate to run
here. The bounded adapter exposes only packaged capability metadata. This is
consultation, not EDI execution; no upstream source or new dependency is copied.

See :doc:`gallery/business/plot_benefit_sharing` for executable plots and tables.
