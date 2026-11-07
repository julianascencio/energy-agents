# VPPA buyer basis and profile risk — 7 November 2026

## Inspection and status

Energy-agents main c5e6650247da89a85870ef275d9e8aefaa112334. No AGENTS.md found.
Inspected roles, skills, finance tools, coordinator, new data-centre specialists,
tests, gallery and all prior business cases. #2 and #11 are confirmed merged into
main; #3 was merged into its old feature branch and knowledge module remains absent
from main. #12 data-centre design work is now on main. No open PRs found at start.
This case concerns buyer-side VPPA cash settlement, not previous battery finance,
commissioning, load shifting, bridge power or household reserve calculations.

## News comparison, retrieved 7 November 2026

| Candidate | Primary publication / event | Decision |
|---|---|---|
| [Ahold Delhaize wind/solar VPPA](https://newsroom.aholddelhaize.com/ahold-delhaize-signs-new-power-purchase-agreement-further-supporting-renewable-energy-development-in-romania/) | 5 Nov 2026; agreement announced that day, signing date not separately established | Selected: corporate procurement exposure with distinct reusable settlement accounting |
| [Haleon/Lightsource VPPAs](https://lightsourcebp.com/news/lightsource-bp-signs-two-virtual-ppas-with-haleon-to-support-supply-chain-decarbonisation/) | 4 Nov 2026 announcement; signing date not separately specified | Similar buyer question, but fewer disclosed profile details; supporting context, no duplicate case |
| [Dunarea East financing](https://rezolvenergy.azurewebsites.net/news/rezolv-energy-secures-up-to-e367-million-financing-for-the-dunarea-east-wind-farm-in-romania/) | 6 Nov 2026 financing announcement | Material value, but detailed debt/coverage assumptions unavailable; prior finance cases cover generic valuation |

No trending claim. Selected announcement describes planned wind/solar projects
and expected 2029 operation. Neither production nor buyer savings are observed.
Do not resolve differing project capacity descriptions across announcements by
inventing facts; no project MW is used in the numerical example.

## Customer, role and economics

Corporate energy procurement/treasury could buy an auditable term-sheet and
basis-risk screen. Reuses Project Finance Analyst and fixed orchestrator handoff;
new deterministic reconciliation tool and versioned repository skill. No new role.
No measured willingness-to-pay, actual offering revenue or live LLM benefit.

One synthetic day, four six-hour UTC intervals: 400 MWh load and 400 MWh contracted
solar, wind or 50/50 blended output. Fixed strike EUR 65/MWh, fee EUR 2/MWh.
Buyer pays retail consumption and receives generation*(reference-strike), which
can be negative. No double-counted physical supply. Retail bill EUR 32,000;
net costs solar EUR 52,800, blend EUR 45,300, wind EUR 37,800. All exceed unhedged
cost in the base scenario. Assumed EUR 40,000 daily budget is exceeded by EUR
12,800 in solar case. Equal MWh does not fix cost or establish renewable matching.

Reference-price and retail-basis stresses remain explicit scenarios. A +25 EUR/MWh
retail-only shock adds EUR 10,000 without changing settlements. No annualization,
probabilities, actual contract terms, realized savings or investment advice.
Excludes negative-price clauses, collateral, credit, FX, imbalance, tax and
certificate value. Human procurement/treasury review required.

## EDI awareness and bounded reuse

Consulted existing source-derived capability snapshots, then inspected EDI
15da19b4a0631dd3ef4e9523fb655388f4c98107, contribution guide, current source paths,
wind catalogue, Elexon settlement client and offshore-wind economics method.
Focused five-file AST catalogue refresh reuses the existing snapshot-builder
script; no claim of full inventory. No suitable buyer VPPA reconciliation method
found in inspected scope. Elexon GB generation is not Romanian price data.

Optional wind loader/validator adapter executed on Romanian catalogue records;
count and input hash are in `data/vppa/edi_execution.json`. This is inventory
context only, not calibration or execution of a price/scientific model. EDI's
package/version/dependencies and separate noncommercial license are documented.

## Saved prompts and reproduction

`src/energy_agents/data/vppa/skill.json` contains actual request, mandate, schema,
allowed tools, evidence requirements, handoffs, output and acceptance criteria.
`case.json` labels all numerical assumptions synthetic and records news provenance.
Evidence gate validates before finance, retaining source and case hash; no trading,
contracting, controls or third-party communication.

```
python -m pip install -e ".[dev,docs]"
energy-agents-vppa --output outputs/vppa
python examples/procurement/plot_vppa_basis.py
python -m pytest -q
ruff check .
python -m build
sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Default path offline/key-free; optional EDI commands in `vppa_basis.rst`.
Direct deterministic baseline equals scripted handoff output. LLM cost, latency
and tokens unknown; no provider run or superiority asserted.

PR: https://github.com/julianascencio/energy-agents/pull/13 — non-draft, left open.

Local validation: 224 tests pass, Ruff/diff checks pass, wheel/sdist and installed-
wheel smoke pass, strict Sphinx/gallery build passes; generated charts inspected.
Two pre-existing optional EDI integration tests run locally and skip in default CI.
See current PR head checks for live GitHub status rather than a frozen result.
