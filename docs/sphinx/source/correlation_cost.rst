Spanish data-centre hourly correlation cost screen
=====================================================

Business decision and evidence
---------------------------------

A data-centre energy procurement manager and the existing project finance analyst
compare a shaping offer with monthly hourly-correlation compensation exposure.
A plausible paid offering is a metering-and-contract diligence report or a
procurement-screening module. No new professional agent is created.

`Real Decreto 1032/2026, BOE-A-2026-24439
<https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-24439>`_ was adopted on
20 November, published on 21 November and enters into force on 22 November 2026.
The BOE XML was retrieved on 21 November; its SHA256 and a packaged, verbatim
articles 8–9 excerpt hash are recorded in ``data/correlation/case.json``.
The announcement is an observed publication, not evidence of customer savings.

Article 8.1 specifies the standard 80% hourly backing requirement. Article 9.3
uses an **arithmetic mean of hourly percentage deviations**, then applies a
banded EUR/MWh rate to total consumption. Article 9.4 makes monthly charges
provisional and subject to annual official regularisation. This screen implements
that bounded calculation; it is neither an official invoice nor legal certification.
The zero-deviation rate is zero because article 9.3 applies when coverage falls
short. Any positive deviation below 5% uses 2 EUR/MWh.

Scope is an assumed in-scope new 20 MW mainland Spanish centre on the standard
pathway. Article 2 includes access power **equal to or above 10 MW**, with scope
and exclusions that require review. Additionality is assumed separately satisfied;
its annual calculation and article 9.2 charges are excluded. SRAP and strategic
project transitions, the national-renewable-share exception, storage attribution,
PUE/WUE, sanctions, connection suspension and sovereignty requirements are excluded.
Paying compensation is not permission to disregard obligations. The published
SRAP transition has distinct P1/P2 rules; no press-summary simplification is encoded.

This differs from ``firm_supply``: the grid is assumed to serve all demand here;
renewable backing gaps are not physical outages. EDI energy matching is only a
comparator, not an eligibility check or a tariff calculation.

Synthetic example and economics
----------------------------------

February 2027 contains 672 mainland civil hours. Demand is 20 MW throughout.
Backing repeats 20 MWh/hour for 18 hours and 4 MWh/hour for six hours each day:
10,752 MWh against 13,440 MWh consumption, or 80% monthly matched energy. A
proposed top-up adds 12 MWh in each low-backing hour, totalling 2,016 MWh.
These constructed traces are not a generation design, metered data or quotes.
Eligible allocation and absence of double counting are explicit assumptions.

.. list-table:: Computed EUR scenario, one month, before tax and discounting
   :header-rows: 1

   * - Metric
     - Baseline
     - With shaping
   * - Mean hourly deviation
     - 18.75%
     - 0%
   * - Correlation rate, EUR/MWh consumed
     - 8
     - 0
   * - Modelled correlation compensation, EUR
     - 107,520
     - 0
   * - Incremental shaping premium, EUR
     - 0
     - 80,640
   * - Implementation cost, EUR
     - 0
     - 5,000
   * - Total relevant cost, EUR
     - 107,520
     - 85,640

The assumed all-in incremental shaping premium is 40 EUR per top-up MWh.
It includes replacement/settlement effects by assumption; this is not a payment
for additional customer consumption. Common electricity supply costs cancel.
No extra resale value or avoided wholesale energy purchase is credited.
Conditional net cost reduction is **21,880 EUR**; the break-even premium after
implementation cost is **50.85 EUR/MWh**. At 60 EUR/MWh the intervention costs
18,440 EUR more. At half delivery the remaining deviation is 9.375%, with a
5 EUR/MWh rate: at the base quote the net reduction becomes -5,000 EUR.
The gallery plots both quote and delivery sensitivities. No annual extrapolation,
realised revenue, field validation or technology superiority is claimed.

Method, prompts and controls
-------------------------------

For hour h, deviation is max(0, 1 - backing_h / (0.8 * demand_h)). The monthly
mean is unweighted by demand. Surplus in one hour cannot cancel another hour's
deficit. Rates are 0 for no deviation; 2 below 5%; 5 from 5% to below 10%; 8
from 10% to below 20%; 11 from 20% to below 50%; and 16 at or above 50%.
Compensation equals the rate times total month MWh, not deficient MWh.
Exact rational arithmetic prevents floating-point boundary misclassification.

``data/correlation/skill.json`` saves the user request, role mandates, input
schema, tool allowlist, evidence requirements, handoffs, output and acceptance
contract. ``reference_case`` expands the documented synthetic profile;
``--case`` accepts the expanded JSON emitted as ``inputs.json``. Validation
requires a full Europe/Madrid calendar month in contiguous canonical UTC hours,
including DST, positive demand each hour, finite bounded nonboolean numbers,
explicit synthetic scope and pinned source provenance. Zero-load treatment is
not established here and is rejected. No live data connector is added.

Evidence produces ``correlation_audit`` bound to the input SHA256. Finance
recomputes and compares it before accepting a handoff. Invalid evidence blocks
finance; unregistered actions and premature delegation are rejected. Output
always states that purchasing and compliance certification are not authorized.
The scripted workflow equals the direct deterministic baseline. No live LLM ran;
LLM cost, latency and tokens are unknown, and no agent benefit is claimed.

Energy Data Insights reuse and reproduction
----------------------------------------------

The source-derived catalogue was refreshed at EDI commit
``e72d9d822b442f6392c80ce12dfc62f738f51ddd``. The generic
``methods/src/energy_methods/hybrid_dispatch.py`` remains blob
``9a3f8bf79cce6d00d62adcf2ae3a23c9718de82e``. The optional adapter reuses the
existing hash-pinned ``energy-methods==0.1.1`` package and checks its source SHA256.
It executes ``simulate_hybrid`` with backing in the generic supply channel, zero
solar and battery, one-hour intervals, and customer load. It verifies the physical
min(backing,load) comparator for both profiles, not legal attribution or tariffs.
Execution evidence is saved separately from discovery metadata.

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-correlation --output outputs/correlation
   python examples/business/plot_correlation.py
   # Optional EDI cross-check, Python 3.12+:
   python -m pip install --no-deps --require-hashes -r requirements/operations.txt
   energy-agents-correlation --edi --output outputs/correlation_edi
   python -m pytest tests/test_correlation.py
   ruff check .
   python -m pytest
   python -m build
   sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

After installation the example is offline and key-free. JSON outputs retain
inputs, full audit, workflow trace, report and separate EDI execution/catalogue.
The source can be retrieved independently with:

.. code-block:: bash

   curl -L 'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-24439' -o boe.xml
   sha256sum boe.xml

Compare with the recorded raw XML hash. A changed source requires substantive
review; do not silently treat a historical snapshot as current legislation.
The bundled excerpt permits offline inspection of the calculation's source.
