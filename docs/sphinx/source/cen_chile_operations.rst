CEN Chile: real operations and asset management
================================================

The operations service now runs on **actual downloaded CEN Chile daily reports**.
The preserved example covers **2–8 November 2026**, using only plant names
beginning with ``PFV`` followed by a space in section 1.1. This is a selected fleet, not all Chilean solar
generation: PMGD, other name prefixes, BESS and CSP are outside this extraction.

`Open the searchable CEN operations report <_static/cen_chile/report.html>`_.
The report includes plant-level observations, source-page links, availability
notices, missing dates and draft investigations. JSON exports include input
provenance, SHA-256 hashes, backend identity, role reports and proposed work orders.

Run the preserved real case
-----------------------------------

With Python 3.12 or newer, from this checkout:

.. code-block:: bash

   python -m pip install -e ".[docs,mcp]"
   python -m pip install --no-deps -r requirements/operations.txt
   energy-agents-cen --output outputs/cen_chile
   python examples/operations/plot_cen_chile_operations.py

Open ``outputs/cen_chile/report.html``. No API key or network is needed for
replay. The snapshot was obtained from the public CEN index and PDFs, not generated
by an LLM. Reports can be revised; the hashes identify the downloaded versions.
The packaged JSON retains numerical rows and notice identifiers, not full report prose.

The resulting observations
--------------------------

.. list-table:: Selected fleet, 2–8 November 2026
   :header-rows: 1
   :widths: 65 35

   * - Metric
     - Result
   * - Unique source PFV names
     - 84
   * - Comparable plant-days
     - 583 of 588 possible
   * - Scheduled generation
     - 322,685.04 MWh
   * - Actual generation
     - 296,344.82 MWh
   * - Sum of positive daily schedule shortfalls
     - 82,148.40 MWh
   * - Sum of positive daily generation above schedule
     - 55,808.18 MWh
   * - Net actual minus scheduled generation
     - −26,340.22 MWh
   * - Revenue impact / recoverable energy
     - Unknown / unknown

Daily deficits and excesses offset across dates and plants. The identity
``actual - scheduled = above_schedule - shortfall`` is checked independently
for every asset. Only days with both observations enter these totals.

The largest complete-window investigation signals are Atacama Solar II
(5,460.77 MWh), CEME 1 (5,122.29 MWh), Finis Terrae (4,915.55 MWh), Gran Teno
(4,338.94 MWh) and Sol del Desierto (4,056.35 MWh). This ranks the sum of daily
positive schedule gaps, **not technical fault severity, recoverable energy or
commercial value**. Safety and current site status need a separate review.

Two useful asset-management findings
------------------------------------

* **Huatacondo:** zero scheduled and actual generation throughout the window,
  but CEN's 8 November report lists 0% availability under section 3.1,
  ``Desconexión Forzada``, notice ``SDCF 2026100475`` (PDF page 16).
  The reliability role raises a status-confirmation draft despite the absence
  of a schedule gap. A reported availability value is not a time-weighted KPI
  or proof of lost production. Current status must be confirmed.
* **Tirana Solar:** absent from the selected table on 2–6 November and present
  on 7–8 November. It is held out of the complete-window investigation ranking.
  Absent records are not silently filled with zero generation.

There are eight assets with below-100% reported availability notices in the
final report. The report displays this queue separately from the MWh queue.
Plant identities remain the exact CEN source names; reconciliation to stable
InfoTecnica identifiers has not yet been established.

Get new data directly from CEN
------------------------------

Install the pinned retrieval package and its PDF extra, then retrieve a window
of at most 31 days currently present in the public index:

.. code-block:: bash

   python -m pip install -r requirements/cen-retrieval.txt
   python -m energy_data_retrieval.sources.cen.daily_report \
     --start 2026-11-02 --end 2026-11-08 --output outputs/cen_download
   energy-agents-cen --input outputs/cen_download/snapshot.json \
     --output outputs/cen_review

For a network requiring the configured HTTPS proxy, append ``--use-env-proxy``
to the retrieval command. The client otherwise uses EDI's default transport.
The connector discovers actual links from the CEN index, downloads the PDFs
with HTTP manifests, verifies dates and supported table structure, and records
source pages and SHA-256 checksums. Missing report dates and conflicting revisions
fail explicitly. The live index is rolling; retain snapshots and raw PDFs for
long-term reproduction. Format changes require parser review.

No CEN API key was configured for this run. EDI's existing authenticated hourly
generation connector is separate and requires credentials; this example uses
the public daily reports. Daily aggregation cannot diagnose intra-day trips,
clipping or dispatch curtailment. Operational reports are subject to revision
and are not treated as final settlement records.

Use the same agent tools
------------------------

.. code-block:: bash

   energy-agents-ops-mcp --input outputs/cen_chile/input.json

The existing stdio MCP interface exposes ``list_assets``, ``review_portfolio``,
``review_asset``, ``get_evidence`` and ``draft_work_order``. For example:

   Review this CEN fleet. Separate schedule gaps from reported unavailability.
   Inspect Huatacondo and Gran Teno, show source pages and missing inputs, and
   draft the next investigation without attributing lost revenue.

The shipped execution is deterministic across performance, reliability,
commercial, maintenance and technical asset-management roles. An LLM host can
select the tools; no live LLM execution or autonomous dispatch is claimed.
Drafts remain local, with evidence and closure requirements.

Before estimating business value, add interval SCADA, irradiance/weather and an
appropriate technical baseline; reconcile grid instructions and outage history;
then join nodal/PPA prices and repair scope/cost. The commercial role reports
these missing inputs and returns ``null`` for unsupported financial results.

Sources and provenance
----------------------

* `CEN daily reports index <https://www.coordinador.cl/operacion/documentos/novedades-cdc/>`_.
* `8 November daily report <https://www.coordinador.cl/wp-content/uploads/2026/11/Informe-Diario-08-11-2026.pdf>`_: generation table and availability notices.
* `8 November executive report <https://www.coordinador.cl/wp-content/uploads/2026/11/Resumen-Ejecutivo-de-Operacion-08-11-2026-V1.pdf>`_: explicit daily energy units (MWh). Its all-solar total has a different scope from our selected PFV table.
* `Snapshot with all seven exact URLs and hashes <_static/cen_chile/input.json>`_.
* `Computed portfolio and role reports <_static/cen_chile/portfolio.json>`_.
* :doc:`gallery/operations/plot_cen_chile_operations`: executed chart and step-by-step review.
