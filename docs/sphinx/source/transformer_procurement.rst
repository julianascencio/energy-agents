Transformer manufacturing-slot reservation
==========================================

A wind developer's procurement and investment committee must decide whether to
pay for a transformer slot before approval. The reusable screen compares
reservation with ordering at approval, accounting for site readiness,
cancellation, fees and a maximum tolerable loss. A plausible paid offering is
an auditable procurement-option review using client schedules and supplier term
sheets. No customer purchase, willingness-to-pay or realised revenue is measured.

Evidence and business boundary
------------------------------

`ENTSO-E's 3 November 2026 announcement
<https://www.entsoe.eu/news/2026/11/03/entso-e-report-sets-out-europe-s-transmission-investment-needs-to-2035/>`_
reports planned transmission equipment additions. The linked report's p. 16
states a typical minimum 36-month lead time for 245–420 kV power transformers.
This motivates an early procurement decision; it supplies neither a supplier
quote nor cancellation likelihoods. Publication and report-release event are
both 3 November; the underlying survey is not a one-day event. No trending claim.

The numerical example is **entirely synthetic**. Month zero is the decision to
reserve; project approval/cancellation occurs in month 12. Both choices must
wait for approval, equipment and site readiness before three months of
installation. The existing Project Controls Engineer's dependency scheduler is
reused with 30-day planning months; these are not calendar delivery forecasts.

The assumed wind project earns EUR 400,000 per operating month, already net of
operating and route-to-market costs. The horizon ends in month 72. Cash arrives
at month-end, first in the month after completion. Discounting uses an assumed
8% effective annual rate. The non-creditable EUR 600,000 reservation fee is paid
now; EUR 200,000 exercise premium is paid at approval only if proceeding. The
base case has no cancellation refund. A hypothetical quote must explicitly
permit manufacturing before approval on these terms; no actual supplier does
so on the evidence available here.

Common transformer price/payment timing is assumed identical at approval and
cancels in the incremental comparison. If a real quote requires earlier capital
payments, storage, engineering or additional insurance, those differences must
be added before using the screen. No tax, financing, inflation, terminal value,
residual equipment value, lifetime valuation or grid welfare benefit is modelled.

.. list-table:: Synthetic joint scenarios and results
   :header-rows: 1

   * - Scenario
     - Probability
     - Wait / reserve COD month
     - Incremental NPV, EUR
   * - Site ready
     - 50%
     - 51 / 39
     - 2,800,861
   * - Site delayed
     - 30%
     - 57 / 57
     - -785,185
   * - Cancelled at approval
     - 20%
     - No operation
     - -600,000

Expected incremental NPV is **EUR 1,044,875**, with a **50% probability of loss**
under the stated joint assumptions. Worst loss among positive-probability
scenarios is **EUR 785,185**, within the assumed EUR 900,000 downside limit.
Reducing that limit to EUR 700,000 changes the screened choice to waiting despite
positive expected NPV. These are modelled outcomes, not observed profits.

The economic fee ceiling is EUR 1,644,875, holding all other assumptions fixed.
It is an expected-value break-even, not a quote recommendation: the downside
constraint must also be checked. A negative ceiling means no nonnegative fee
breaks even; null means the fee coefficient is zero. Cancellation sensitivity
holds the conditional site-ready/site-delayed mix fixed. The expected value
crosses zero near 70.8% cancellation; these probabilities are not estimated data.

Method and acceptance
---------------------

For scenario s, completion is max(approval, site readiness, delivery) plus
installation. Let C be monthly net contribution, F the fee, P the exercise
premium, R the cancellation refund and d(m)=(1+r)^(-m/12). Incremental NPV is
sum over m=1..H of C*(reserve_operating - wait_operating)*d(m) - F
- proceed*P*d(decision) + cancel*R*d(decision). Joint probabilities sum to one
without normalization. Negative contributions and reservation delays remain
negative. No independent-probability assumption is imposed on delivery and site
readiness. Zero-probability states are excluded from the worst-loss measure.

Inputs use ``case.json`` schema 1.0 with ISO dates, explicit evidence classes,
EUR, bounded integer months (0..120), finite amounts (absolute maximum EUR 1e12),
1..20 unique joint scenarios and declared cost boundaries. Source observations
are kept outside the financial assumptions. The gate checks declarations and
chronology; it does not verify source truth or engineering feasibility.

``src/energy_agents/data/procurement/skill.json`` saves the actual user request,
evidence and role mandates, input schema, allowed tools, scheduler prompt,
handoffs, output contract and acceptance criteria. The fixed workflow is:
evidence gate, existing Project Controls Engineer, existing Project Finance
Analyst. Finance rechecks the received schedule. Failed evidence blocks both
roles; scheduler actions are restricted to ready-task delegation. There are no
purchase, contract, email, trading or equipment-control tools. No new role.

Output contains the input hash, source, state-specific cash ledger and COD,
expected NPV, loss probability, maximum loss, fee ceiling and advisory choice.
The direct deterministic baseline equals the scripted workflow output exactly.
This establishes routing/accounting correctness, not LLM advantage. Live LLM
success, tokens, cost and latency are unknown because no provider was run.

Reproduce offline
-----------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-procurement --output outputs/procurement
   python examples/procurement/plot_transformer_reservation.py
   python -m pytest -q
   python -m ruff check .
   python -m build
   python -m sphinx -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

The CLI exports the input, full handoff trace, cash ledgers, parity result and
cancellation sensitivity to ``report.json``. The gallery prints a scenario table
and plots state outcomes and sensitivity. All default paths are key-free and
offline. An optional explicitly configured ``OrchestratorPlanner`` can be passed
to ``run_procurement_workflow``; it only chooses ready tasks, and sends its
context to that configured provider. No live-provider outcome is claimed.

Bounded Energy Data Insights reuse
----------------------------------

Source-derived five-file capability catalogue refreshed at
``f08cc14998ec291b28e7132d4cd0a826825bd9e0`` using the existing committed-blob/AST
builder. Files include the wind loader, grid-milestone evidence method,
offshore-wind economics, dependency metadata and license. This is a focused
catalogue, not exhaustive awareness. No suitable manufacturing-slot valuation
method was found in this inspected scope; offshore-wind LCOE is not a substitute
for this option's incremental cash accounting.

The **existing** ``business.vppa.inspect_edi_wind`` bounded read-only adapter was
actually executed against three Romanian wind records, preserving the loader's
validation. The execution record in ``data/procurement/edi_execution.json`` gives
the commit, input hash, dependency versions and one observed 1.68-second elapsed
time (includes imports; not a benchmark). This context cannot establish supplier
lead times, completion, prices or probabilities. No EDI numerical/scientific
method was executed. No catalogue records or upstream source code are vendored.

Optional full dependency installation and explicit local replay (Python >=3.12):

.. code-block:: bash

   git clone https://github.com/julianascencio/energy-data-insights.git ../energy-data-insights
   git -C ../energy-data-insights checkout f08cc14998ec291b28e7132d4cd0a826825bd9e0
   python -m pip install -e ../energy-data-insights/data-retrieval
   python scripts/refresh_procurement_capabilities.py ../energy-data-insights \
     --output src/energy_agents/data/procurement/edi_capabilities.json
   python -c "from energy_agents.business.vppa import inspect_edi_wind; print(inspect_edi_wind('../energy-data-insights/catalogues/wind'))"

EDI ``energy-data-retrieval`` 0.1.0 declares NumPy, pandas, SciPy, PyArrow
19..<25, httpx, openpyxl, xarray, h5netcdf and rasterio; exact bounds are in the
pinned metadata. The recorded adapter-only run used a no-dependencies editable
install plus PyArrow 24 and existing imports, not a validation of all EDI
connectors. EDI uses ``LicenseRef-ASVA-Noncommercial-1.0``; commercial inclusion
requires rights under its separate terms. The standalone energy-agents screen
does not require EDI. Procurement terms and engineering approval remain human
responsibilities.

API
---

.. automodule:: energy_agents.business.procurement
   :members: reference_case, validate_case, delivery_scenarios, screen_reservation, run_procurement_workflow, cancellation_sensitivity
