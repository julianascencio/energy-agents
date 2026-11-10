# Tandem-module tender premium — 10 November 2026

## Inspection and selection

Inspected energy-agents main `832f411` (roles, orchestrator, operations, quantum
studies, finance screens, gallery, tests, package and CI), seven prior case
records and current open PRs: none. No AGENTS.md found. #2 is merged into main;
#3 was merged into the old professional-role feature branch, and its full
knowledge package remains absent. #16/#17 operations/CEN and #18/#19 quantum
work are now merged. This case uses finance, not a new role or the separate
EDI news workflow. It concerns fixed-area module tenders with uncertain yield
retention, rather than battery revenues, delivery timing or VPPA settlement.

| Candidate | Publication / event | Decision |
|---|---|---|
| [Heliene/Caelux issuer release](https://www.globenewswire.com/news-release/2026/11/10/3399606/0/en/heliene-and-caelux-bring-next-generation-hybrid-tandem-solar-modules-to-u-s-commercial-manufacturing.html) | 10 Nov 2026, 09:00 ET; production announced that day, exact start not specified; deliveries planned 2027 | Selected: fresh primary source, concrete procurement premium question, reusable claim-to-scenario evidence gate and clipped-energy economics |
| [RWE Ragusa](https://www.rwe.com/en/press/rwe-renewables-europe-australia/2026-11-10-rwe-starts-construction-of-its-first-battery-in-italy/) | 10 Nov announcement of construction start; exact start day unspecified | Credible grid/BESS context, overlaps existing storage investment screens; no capacity arithmetic used to infer revenue |
| [Lydian Faraday issuer syndication](https://finance.yahoo.com/energy/articles/lydian-energy-brings-150-mw-113000948.html) | Published 10 Nov; commercial operation 18 Sep 2026 | Fresh disclosure of an older operating event; shared-interconnection and data-centre context, but no contract prices disclosed |
| [IID Pilot Knob issuer submission](https://www.acwa.com/news/iid-approves-21-million-overhaul-at-districts-largest-hydroelectric-plant/) | 4 Nov publication | Hydro restoration reviewed earlier; less distinct than the new module tender capability |

Wind, buildings and hybrid opportunities were also compared against existing
commissioning, building edits, industrial flexibility and operations workflows.
No trending claim. Source figures are manufacturer claims; scenario uplift is
not a verified annual yield, commercial guarantee or replicated efficiency test.
Only concise factual metadata are preserved; no article prose is copied.

## Business and evidence

Buyer: rooftop owner or EPC procurement team. Offering: independent bid/energy
review with a maximum all-in incremental installed premium and downside ledger.
No observed willingness-to-pay or consultancy revenue. Baseline conventional
modules on the same usable area, intervention hypothetical tandem equivalent
profile. No purchase, contract, trade, work dispatch or physical control.

Synthetic assumptions: 2,000 m² usable module area, baseline equivalent peak
0.44 MW, 20% alternative profile uplift, shared 0.30 MW AC/export ceiling,
98% uniform availability. Explicit 8,760-hour synthetic daily/seasonal profile;
20 years of repeated weather with mean retention (1-rate)^(year-1). Conventional
rate 0.5%/year; tandem rates 0.5% and 2% plus a no-uplift case. No inferred
spectral response, legal warranty or independently validated lifetime.

KPI: incremental project NPV and maximum premium, constant-real USD. Twenty-year
horizon, 7% discount rate, $100/MWh flat energy value, $500/year incremental O&M,
$50,000 all-in incremental capex at time zero. Common costs cancel. Excludes
financing, tax, subsidies, replacements, residual value, structural changes not
in the premium and time-varying prices. Annual energy after clipping: first-year
baseline 829.208 MWh versus 916.827 MWh, only 10.57% uplift despite the assumed
20% profile increase. This is a synthetic clipping result, not a product test.

Premium ceilings: $90,235 equal degradation; $31,290 faster degradation;
-$5,297 no uplift. Incremental NPVs: $40,235; -$18,710; -$55,297. No assigned
probabilities or realised savings. The gallery varies energy value $0–200/MWh;
engineers must establish profiles, clipping, compatibility, area, structure,
warranty and degradation before a real bid recommendation.

## Reuse, prompts and execution

Inspected EDI `22ec18c382643e21395726dcd6f4fad0d77f068f` and refreshed a
focused five-file AST/committed-blob catalogue. Actually executed the bounded
`pv_repowering.lifetime_intervention` adapter for all energy trajectories;
no duplicate clipping method. `case.json` records source/input hashes, commit,
dependencies and measured adapter latency. EDI 0.1.0 is separately licensed
LicenseRef-ASVA-Noncommercial-1.0. Full upstream dependency health not evaluated.

`data/tandem/skill.json` saves actual request, mandate, input schema, allowed
tools, handoffs, output and acceptance criteria. Evidence validation precedes
the existing finance role; immutable task copies and scheduler permissions are
reused. Hashes detect drift, not authenticity or scientific validity. The direct
deterministic baseline equals the scripted workflow. No live LLM run; provider
cost, token usage and latency unknown. The offline path replays EDI-generated
synthetic annual energies; optional replay executes the method again.

```bash
python -m pip install -e '.[dev,docs,quantum]'
energy-agents-tandem --output outputs/tandem
python examples/procurement/plot_tandem_premium.py
# Optional Python 3.12 EDI replay:
python -m pip install --no-deps -r requirements/tandem.txt
python -m pip install 'numpy>=2.2,<2.4' 'pandas>=2.2,<3'
energy-agents-tandem --verify-edi
python -m pytest -q
ruff check .
python -m build
# Full docs also needs the established operations backend:
python -m pip install --no-deps -r requirements/operations.txt
sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

PR: https://github.com/julianascencio/energy-agents/pull/20 — non-draft, left open.
GitHub status is verified against the final head in the PR; local results follow.

Local validation: 414 tests passed, two optional backend tests skipped. Ruff,
wheel/sdist, isolated installed-wheel offline CLI, optional EDI replay and strict
Sphinx/gallery build pass. Generated chart and numerical table inspected. The
new case adds 16 tests, including hand calculations, negative energy prices,
input validation, tamper detection, permission rejection and handoff ordering.
