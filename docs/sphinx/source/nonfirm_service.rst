Non-firm service interruption economics
==========================================================================================

A data-centre developer or industrial energy buyer can use this advisory screen
to compare all-firm service with a fully curtailable non-firm tranche. A plausible
paid offering is a contract-input and workload-economics diligence report. No
customer revenue, willingness to pay or realised savings is evidenced.

`ISO-NE's 13 November 2026 announcement <https://isonewswire.com/2026/11/13/iso-ne-files-proposal-with-ferc-to-address-large-loads/>`_
describes proposed service options and re-dispatch at local prices reaching
USD 250/MWh. This remains a **proposal**, not an effective rule. The linked
information summary was updated 9 November. The screen does not implement the
full tariff, determine eligibility, or reproduce ISO dispatch instructions.

Method
------

Both alternatives have the same constant load and connection date. Whenever the
supplied price is at or above the scenario threshold, the entire non-firm tranche
is removed. Adjacent high-price blocks are one event. The annual accounting window
starts with no active event. No work is recovered later, and no onsite generation
or battery is modelled. Operators must supply a fully curtailable tranche.

Annual net benefit equals assumed avoided firm-service costs plus avoided energy
purchases, minus lost business contribution, event restart costs and flexibility
O&M. Business contribution **excludes electricity**, preventing double counting.
NPV discounts repeated year-end net benefits and subtracts time-zero flexibility
CAPEX. The break-even annual firm-cost saving includes annualized flexibility CAPEX.
The input annual firm-cost saving is a customer assumption, not a quoted tariff,
capacity-market price or guaranteed exemption. No speed-to-power benefit is added.

The reference case is **synthetic constant-real USD**: 100 MW load, 40 MW fully
curtailable, two 60-hour interruptions at USD 300 and 500/MWh, lost contribution
USD 500/MWh, restart USD 20k/event, avoided firm costs USD 1.2m/year, flexibility
O&M USD 100k/year, flexibility CAPEX USD 2m, 10 years and 8% discount.
Results: 4,800 MWh curtailed, USD 2.4m contribution lost, USD 1.92m energy purchases
avoided and USD 40k restart costs. Annual net benefit is USD 580k; NPV is about
USD 1.892m. The gallery separately stresses event duration and lost contribution.
These are scenarios, not likelihood-weighted forecasts. Historical regional
high-price frequency does not calibrate this synthetic customer chronology.

No ramping, minimum load, workload rebound, SLA model, tax, financing, inflation,
residual value or non-price reliability instructions are included. Firm service is
not outage insurance. Negative electricity prices are permitted in input, but
threshold-triggered removal is mandatory in the scenario even if economically
unfavourable. The screen does not optimize voluntary dispatch.

Workflow, evidence and reproduction
--------------------------------------

The existing Project Finance Analyst and bounded orchestrator execute evidence then
finance. Versioned ``data/nonfirm/skill.json`` contains the reusable request, role
mandates, input schema, tools, evidence gates, handoffs and acceptance contract.
Invalid evidence blocks finance; only ready registered tasks can be delegated.
Eligibility remains unknown and dispatch authority is false. The scripted workflow
equals the direct deterministic baseline; live LLM tokens/cost/latency are unknown.

EDI source metadata is recorded at ``fc63c5f97e6513e7f290340ddfdce0b80962644a``.
Its hybrid supply/storage balance does not implement mandatory load removal or
contractual opportunity costs. The bounded ``edi_context`` adapter exports this
capability boundary without claiming execution. Existing repository EDI execution
adapters remain available; no duplicate connector or scientific method is added.

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum,mcp]'
   energy-agents-nonfirm --output outputs/nonfirm
   python examples/business/plot_nonfirm_service.py
   python -m pytest tests/test_nonfirm.py

Default and custom ``--case`` runs are offline/key-free after installation. Exports
contain input, workflow/report, input digest and EDI metadata. No live market feed,
trading or physical control is connected. The existing optional OrchestratorPlanner
can prioritize ready tasks; no provider execution or measured agent advantage is
claimed. Full gallery installation also uses ``requirements/operations.txt``.
