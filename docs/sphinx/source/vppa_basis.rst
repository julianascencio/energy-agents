VPPA buyer profile and market-basis screen
====================================================================================================

`Ahold Delhaize's 5 November 2026 announcement
<https://newsroom.aholddelhaize.com/ahold-delhaize-signs-new-power-purchase-agreement-further-supporting-renewable-energy-development-in-romania/>`_
describes a wind-and-solar VPPA with planned project operation in 2029. This motivates
procurement diligence; prices, generation profiles and settlement clauses below
are entirely synthetic, not reconstructed commercial terms.

Decision and method
-------------------

Corporate procurement/treasury teams need to distinguish the electricity bill
from a financial VPPA settlement. This capability reuses the Project Finance
Analyst and orchestrator, adds a deterministic reconciliation tool and saves an
explicit prompt/workflow contract. A plausible offering is a paid term-sheet and
cash-flow sensitivity review. No customer demand or willingness to pay is measured.

The buyer pays its retail bill on consumed MWh, pays a fixed VPPA strike and receives
the generation-location reference price on contracted generation MWh:

* Retail bill = sum(load MWh * retail price EUR/MWh).
* Buyer receipt = sum(contracted generation MWh * (reference price - strike)).
* Net buyer cost = retail bill - buyer receipt + contract fees.

A negative receipt is a payment by the buyer. Generation is not delivered physically
to the buyer in this model and does not reduce the retail bill. Negative prices
remain signed; no floor, suspension or negative-price exclusion is assumed.
Contract-specific volume, floor, reference, settlement and guarantee-of-origin
provisions need a separate review. This is not legal interpretation or hedge accounting.

All profiles have equal contracted MWh. Alternative solar fractions blend those
profiles without normalizing energy. Contiguous UTC intervals reject gaps and
duplicates. Energy is supplied in MWh, not MW; hours describe interval boundaries
and must not multiply MWh again. Prices are constant within each synthetic block.
Real data require settlement-resolution alignment; a simple average price times
aggregated energy may introduce error when generation varies within the interval.

The generation-to-load ratio is only an energy-volume ratio across the example
horizon. It proves neither physical matching, renewable consumption, 24/7 matching,
additionality, nor valid environmental claims. The tool does not value certificates.

Results and sensitivities
-------------------------

The synthetic horizon is one 24-hour day in four six-hour blocks. Retail consumption
and each contracted profile total 400 MWh. Strike EUR 65/MWh, fee EUR 2/MWh and
assumed daily budget EUR 40,000 give:

.. list-table:: Synthetic buyer cash flows (EUR/example day)
   :header-rows: 1

   * - Profile
     - Buyer receipt
     - Net cost
   * - Unhedged
     - 0
     - 32,000
   * - Solar
     - -20,000
     - 52,800
   * - 50/50 blend
     - -12,500
     - 45,300
   * - Wind
     - -5,000
     - 37,800

All hedged alternatives cost more in this scenario; the unhedged baseline stays
visible. This is not an instruction to choose no hedge: risk tolerances, long-term
prices and environmental objectives are absent. Capture reference prices are
EUR 15/MWh for solar and EUR 52.50/MWh for wind. Their break-even strikes versus
unhedged cost, after fees, are EUR 13 and EUR 50.50/MWh respectively.

The gallery varies reference prices while holding retail prices fixed. A separate
test raises retail prices by EUR 25/MWh and confirms an unchanged settlement with
EUR 10,000 higher buyer cost. These are deterministic stress scenarios, not
probabilities or forecasts. No annualization, NPV, realised savings, collateral,
credit risk, imbalance cost, tax, FX or financial-advice recommendation is supplied.

Evidence, reuse and boundaries
------------------------------

The versioned user request, role mandate, inputs, tools, handoffs, outputs and
acceptance criteria are in ``energy_agents/data/vppa/skill.json``. An evidence gate
checks schema and chronology, not source truth. Failed evidence blocks finance;
only registered evidence and finance tasks can be delegated. Human review required.
There are no trade, purchase, contract, control or messaging tools.

Inspected current EDI commit ``15da19b4a0631dd3ef4e9523fb655388f4c98107`` after
consulting the prior source-derived catalogue. A focused five-file refresh records
signatures, hashes and pinned URLs in ``edi_capabilities.json``. Elexon provides
GB generation settlement data, not the required Romanian VPPA prices; offshore
wind economics is a different decision model. Neither was claimed executed.
No suitable VPPA buyer reconciliation method was identified in the inspected scope.

The optional ``inspect_edi_wind`` adapter reuses EDI's wind loader and validator.
Its execution manifest records the Romanian inventory count and input hash.
Inventory provides context only: records may represent phases or equipment, and
neither generation nor prices are inferred from them. No copied connector or
scientific forecasting method. EDI 0.1.0 requires Python 3.12+ and dependencies
in its data-retrieval package. The recorded loader-only run used an editable
no-deps install in an existing runtime; full package validation is not claimed.
Upstream ``LicenseRef-ASVA-Noncommercial-1.0`` remains separate; commercial
use of the optional dependency needs appropriate owner permission.

Reproduction
------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-vppa --output outputs/vppa
   python examples/procurement/plot_vppa_basis.py
   python -m pytest -q
   ruff check .
   python -m build
   sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

Optional inventory: install EDI's data-retrieval package from the pinned commit,
then call ``inspect_edi_wind('/path/to/edi/catalogues/wind', 'ROU')``.
Refresh source discovery with ``python scripts/refresh_vppa_capabilities.py
/path/to/edi --output catalogue.json``. Default CLI/gallery need no keys or EDI.
They compare the scripted handoff against direct deterministic execution and
write a report with signed interval cash flows and case hash. No live LLM runs:
latency, token count and provider cost remain unknown. The optional existing
OrchestratorPlanner can schedule tasks but has no established advantage here.

.. automodule:: energy_agents.business.vppa
   :members:
