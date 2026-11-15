# ISO-NE proposed non-firm service: interruption economics

Date: 2026-11-15. PR: [#27](https://github.com/julianascencio/energy-agents/pull/27). Status: implemented, advisory scenario; not an effective tariff or a service-eligibility opinion.

## News selection and evidence

The selected [ISO-NE primary announcement](https://isonewswire.com/2026/11/13/iso-ne-files-proposal-with-ferc-to-address-large-loads/) was published 13 November 2026, within 72 hours of this review. It describes a filing that week; the exact filing timestamp was not independently established here. Its proposed non-firm/interim service includes redispatch when local prices reach USD 250/MWh. The [linked information summary](https://www.iso-ne.com/static-assets/documents/100040/large_loads_integration_proposal_information_summary_10.09.26.pdf) says last updated 9 November despite its filename. The proposal is not represented as effective regulation. No trending claim is made.

Other candidates reviewed:

| Candidate and date | Business potential | Why not selected |
| --- | --- | --- |
| [Jordan official Petra update](https://org.petra.gov.jo/Include/InnerPage.jsp?ID=365494&lang=ar&name=news), 14 November; project promotion ahead of 19 November conference | Solar 200 MW and storage 100 MW / 4 hours; broader programme includes wind and pumped hydro | Contract prices, investment cost and revenue terms absent; generic bid screen already exists |
| [SOLRITE/sonnen/ADAPT announcement](https://www.globenewswire.com/news-release/2026/11/12/3401686/0/en/solrite-unveils-next-gen-virtual-power-plant-node-with-sonnen-and-adapt-energy-integrating-vpp-breakers-to-turn-home-loads-into-flexible-grid-assets.html), 12 November | Residential breakers make household demand a VPP resource | Publication predates 15 November republication; missing measured deployment economics; overlaps reserve/flexibility cases |
| [Waaree NSE filing](https://nsearchives.nseindia.com/corporate/WAAREE_14112026195402_BESSPacklineannouncementsigned.pdf), 14 November | Battery pack manufacturing expansion | Indexed filing describes commissioned annual capacity, not output or realised sales; full PDF retrieval failed, so not selected on incomplete evidence |

ISO-NE was selected for a concrete reusable decision: mandatory price-triggered interruptions versus assumed fixed service-cost savings. Existing bridge-power work values connection delay, existing industrial flexibility shifts work, and residential reserve protects storage. This case fixes the same connection date, permanently loses curtailed business output, counts interruption starts and calculates the required annual cost saving. It is distinct from the EDI news workflow.

## Customer, decision and economics

A data-centre developer or industrial energy buyer, supported by the existing Project Finance Analyst, compares all-firm service against a fully curtailable non-firm tranche. A plausible paid offering is a service-contract and workload-economics diligence report; buyer demand, pricing and realised revenue are not evidenced.

All customer, price chronology and economic inputs are **synthetic assumptions**, not field data. USD constant-real before-tax cash, 10 years, 8% discount; 100 MW constant load with a 40 MW curtailable tranche. Two 60-hour high-price blocks cost USD 300 and 500/MWh. Lost contribution excludes electricity and is USD 500/MWh. Restart costs USD 20,000/event, annual assumed avoided firm-service costs USD 1.2 million, flexibility O&M USD 100,000/year, and upfront flexibility CAPEX USD 2 million. The proposed price threshold is the observed source fact; the assumed firm-service saving is NOT a tariff quote, capacity payment or guaranteed exemption.

| Modelled reference result | Value |
| --- | ---: |
| Curtailment | 4,800 MWh/year |
| Interruption starts | 2/year |
| Lost contribution excluding electricity | USD 2,400,000/year |
| Avoided electricity purchases | USD 1,920,000/year |
| Restart costs | USD 40,000/year |
| Net annual incremental benefit | USD 580,000/year |
| Incremental NPV vs all-firm baseline | USD 1,891,847.21 |
| Break-even annual avoided firm-service cost | USD 918,058.98/year |

The gallery plots the annual cash components and a separate sensitivity of 0–480 interruption hours at USD 400/MWh and lost contribution of USD 300/500/800 per MWh. This stress is one contiguous event, unlike the two-event reference; it is not a probability forecast. Zero non-firm tranche cannot claim avoided firm-service cost. Below-threshold and negative prices are accepted, threshold equality triggers, contiguous high-price blocks share one restart. Each annual accounting window starts uncurtailed and repeats independently. No recovered work, onsite generation, storage, ramping, SLA distribution, tax, finance, inflation, residual value or non-price reliability events are modelled. Historical regional high-price frequency is not used as a nodal forecast. Positive NPV cannot establish tariff eligibility, actual curtailability or permission to operate.

## Capability and repository provenance

Base energy-agents main: `c8a61091683856c890a5059d0ff6e3d4bd94a445`. Repository instructions, role/orchestrator architecture, versioned skills, tests, gallery, case history and workflows inspected; no AGENTS.md found. No open PRs at initial inspection. Earlier professional-role PR #2 is merged into main and #3 was merged into the former professional-role branch. Previous heat-reuse PR #26 is merged (14 November 23:08:46Z); this occurrence did not perform that merge or deployment.

EDI main inspected at `fc63c5f97e6513e7f290340ddfdce0b80962644a`. The existing source-derived catalogue was consulted and relevant `methods/src/energy_methods/hybrid_dispatch.py` re-read at blob `9a3f8bf79cce6d00d62adcf2ae3a23c9718de82e`. This supply/storage energy-balance method does not calculate mandatory price-triggered lost output or contractual opportunity costs. `data/nonfirm/edi_context.json` records a bounded metadata-only capability adapter: no EDI code is executed by this new screen, no EDI dependency is added, and discovery is not execution. The repository's existing operations integration uses its separately hash-pinned public wheel.

Reusable prompt, mandates, schemas, tools, handoffs and acceptance criteria: `src/energy_agents/data/nonfirm/skill.json`. Implementation: `business/nonfirm.py`; CLI `energy-agents-nonfirm`; gallery `examples/business/plot_nonfirm_service.py`; guide `docs/sphinx/source/nonfirm_service.rst`. Evidence contract validates the synthetic schema and announced-source origin, then hands isolated inputs to existing finance role through the bounded orchestrator. It does not perform legal/source-content verification. Unknown tools and premature finance calls are rejected. Eligibility remains unknown; dispatch authority is false. No new agent or connector is created.

## Reproduction and validation

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
energy-agents-nonfirm --output outputs/nonfirm
python -m pytest -q -rs
python -m ruff check .
python -m build
MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Default/custom `--case` examples are offline and key-free after installation. Exports retain inputs, input hash, evidence gaps, workflow report and upstream capability metadata. The direct deterministic screen and scripted orchestrator produce identical results; this is a correctness baseline, not an agent-performance gain. No LLM run occurred; cost, latency and tokens are unknown. Optional live planning uses the existing OrchestratorPlanner; only registered ready tasks are available and no external control is connected.

Focused tests cover hand calculations, break-even identity, zero discount, threshold equality, event adjacency, negative prices, quantity bounds, NaN/bool/horizon rejection, bad source origin/status/date, annual coverage, isolated handoffs, premature calls and forbidden controls. Local validation: 12 focused tests passed; full suite 520 passed / 5 optional quantum-backend skips (Qiskit/Torch absent locally), with existing EDI operations integration executed after installing the pinned public wheel. Ruff, sdist/wheel build, isolated installed-wheel CLI smoke and strict Sphinx/gallery build passed. Generated table and plot were inspected. CI runs dedicated quantum backends and both Python versions; final head-specific results are recorded in the PR. Independent review and current integration claim are not established; leave open unless all required gates subsequently pass. No release, trade, physical control, contract, third-party contact or deployment is performed.
