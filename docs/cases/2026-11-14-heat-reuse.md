# 14 November 2026 — Data-centre heat recovery investment screen

## News selection and chronology

Selected [Infomaniak's primary announcement](https://api.sttinfo.fi/tiedote/72501998/infomaniak-and-gruyere-energie-develop-a-data-center-project-in-bulle-designed-to-limit-its-footprint?lang=en&publisherId=69821841), published 13 November 2026 at 15:05 EET; event: planning application public display that day. Its proposed Bulle data centre and district-heating connection motivate a heat-offtake decision. Planned heat includes heat-pump electricity; it is not measured heat sales. Permits and commercial agreements remain outstanding. No trending claim.

Compared other primary announcements inside the 72-hour window:

- [EPE pumped-storage information call, 13 November](https://www.epe.gov.br/pt/imprensa/noticias/epe-abre-chamada-para-recebimento-de-projetos-de-sistemas-de-armazenamento-hidraulico-sah-): planning information, explicitly not qualification for future procurement. No contract revenue or eligibility benefit can be inferred. Existing policy/bid roles already cover much of the work-plan need.
- [NeoVolta supply agreement, 13 November](https://neovolta.com/blog/neovolta-signs-116m-master-purchase-agreement-to-deliver-battery-energy-storage-): reported USD 116m master agreement for 2027 deliveries. Reviewed announcement/indexed facts do not establish volumes, margins or payment timing needed for a distinctive working-capital case. Contract value is not realised revenue.
- The morning preferred-equity case already covers new financing allocation, and prior records cover bridge power, battery reserve/revenue/bids, VPPA risk, wind debt, commissioning, tandem PV and transformer procurement. Repeating those would add less capability than linking thermal matching to a heat buyer's incremental costs. Broad searches included solar, wind, BESS, hydro, grids and hybrid projects as well as buildings/data centres.

## Repository inspection and current status

Energy-agents main inspected at `38e3d435396a4e14417c7ea816b27710dfee9394`; no AGENTS.md or open PRs returned before implementation. Read README, current roles, orchestrator, finance/physical adapters, gallery, tests, CI and case records. PR #2 is merged into main; awareness PR #3 merged into the earlier professional-role branch, not evidence that its entire module is on main. Existing published operations adapters execute EDI independently.

Earlier preferred-equity [PR #24](https://github.com/julianascencio/energy-agents/pull/24) is now merged: merge commit `c1cae53dcc80f72f168a7b50c3ca4dc46da48964`, merged `2026-11-14T10:36:10Z`; not merged by this occurrence. The energy-policy role is also on current main. Neither observation establishes deployment.

Read current company role/scope registry; this job belongs to the energy specialist. The independent scheduled-run authorization governs execution without a new intake. Company-state contained only the older no-change mission for this job, with no current integration claim. No intake or schedule was created or changed.

## Business and implementation

Customer/payer: district-heating developer or operator evaluating recovered heat and negotiating input contracts. Offering hypothesis: feasibility and heat-offtake diligence report, with reusable inputs and a traceable financial screen. No willingness-to-pay or customer-sales evidence.

Baseline: existing heat supply. Intervention: invest in recovery and heat pumps, dispatch to contemporaneous demand, retain existing supply for deficits. KPI: avoided marginal supply cost less incremental electricity, source-heat fee, variable/fixed O&M; incremental NPV and break-even avoided CHF/MWh. Server electricity/CAPEX and existing supply fixed costs are unchanged. No extra heat-sale revenue or cooling/emissions credits are stacked.

Added `business/heat_reuse.py`, versioned `data/heat_reuse/{case,skill,edi_capabilities}.json`, CLI, tests, methodology and business gallery. Reuses Liquid Cooling Engineer, Project Finance Analyst and orchestrator, with evidence → thermal → finance dependencies. The saved skill includes actual user request, role mandates, schema, allowed tools, evidence requirements, handoffs, outputs and acceptance rules. Financial handoff is bound to an input hash and a recomputed heat balance. No new agent, external action, contact or plant control.

Source-derived EDI snapshot: commit `edd4086a207e95651dc1e8096004b3db71c33e9c`. Inspected hybrid dispatch, data-centre wind and thermal-counterfactual sources. Reuse `simulate_hybrid` through an optional no-storage MW/MWh adapter: heat potential enters the supply channel, all battery/solar parameters are zero, one call per period. Thermal conversion remains local. This is a dimensional energy-matching check, not wind or thermal-storage simulation. Installed module SHA256 `e404a6724ea9f3a332fb50e307e048edde610e8569a230b5177ca1350d536a39` must match inspected source; the existing public hash-pinned energy-methods 0.1.1 wheel supplies it. The adapter actually executed locally and matched. Other inspected capabilities were unsuitable and are documented as discovery only. No copied scientific method or private dependency.

## Synthetic assumptions and results

All operating profiles and costs are synthetic constant real CHF, not actual project terms. Assumptions: illustrative 2.5 MW IT, 80% load, 90% recoverable fraction, COP 4, 3 MW heat-pump output limit, 95% network delivery efficiency, monthly demand 0.4–3.5 MW. Initial investment CHF 4m; 15 years; 6% discount; fixed O&M CHF 100k/year; electricity CHF 120/MWh; source heat CHF 5/MWh recovered; variable O&M CHF 3/MWh delivered; displaced supply CHF 80/MWh delivered.

Reference delivery: 13,024.32 MWh/year; pump electricity: 3,427.45 MWh/year. Annual-only matching ceiling is 15,852 MWh: 2,827.68 MWh above period-matched delivery. Annual supply costs: baseline CHF 1,268,160; intervention CHF 827,993.47. Net savings **CHF 440,166.53/year**, incremental NPV **CHF 275,006.98**, break-even avoided cost **CHF 77.83/MWh**. At half reference demand, NPV falls to **negative CHF 1.779m**; at 150% demand it rises to CHF 1.076m with unchanged electricity price. Gallery also stresses electricity prices CHF 40–240/MWh. No probabilities assigned.

COP follows the [DOE FEMP definition](https://www.energy.gov/cmei/femp/incorporate-minimum-efficiency-requirements-heating-and-cooling-products-federal), heat output divided by electrical input; source heat plus electrical input equals output. COP 4 is an assumption, not a measured equipment rating. Monthly flat profiles cannot establish hourly delivery or reliability. No temperature/hydraulic/part-load model, storage, commissioning ramp, construction delay, replacement, degradation, inflation, financing, tax, subsidy or residual value. Additional auxiliaries need measured effective COP or explicit costs. Zero usable heat still incurs committed investment/fixed costs. The existing district network's renewable character precludes casually treating delivered heat as displaced oil; no emissions benefit is calculated.

## Reproduction and evidence

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
python -m pip install --no-deps --require-hashes -r requirements/operations.txt
energy-agents-heat --output outputs/heat_reuse
energy-agents-heat --edi --output outputs/heat_reuse_edi
python examples/business/plot_heat_reuse.py
python -m pytest
python -m ruff check .
python -m build
python -m sphinx -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Default execution is offline/key-free after installation and requires no EDI; optional EDI execution is also local/key-free. Input JSON, reports, trace, hashes, capability metadata and actual adapter execution status are exported separately. No live LLM executed; cost, tokens and latency are unknown. Scripted workflow/direct baseline numerical parity passed; no superiority or field validation claimed.

Local checks: 22 new tests pass. Full suite: 508 passed, five optional quantum-backend tests skipped (Qiskit/Torch unavailable). Ruff and package build pass. Strict full gallery/docs build and installed-wheel smoke (including executed EDI parity) pass. Charts and numerical output inspected. Hosted final-head status and independent-review status remain separate; no merge or deployment authorized by this record.

Publication: PR link and final validation evidence will be recorded after publication.
