# 2026-11-05 — BESS revenue concentration screening

## Selection

Selected [Clean Horizon's 4 November article](https://www.cleanhorizon.com/news/where-are-battery-storage-revenues-heading-in-europe/) because it supports a concrete investment-review decision and provides an attributable revenue decomposition. Event: 1 October presentation; article: 4 November; accessed: 5 November. No audience-trend claim is made.

Also considered [Eos's 5 November earnings announcement](https://investors.eose.com/news-releases/news-release-details/eos-energy-enterprises-reports-third-quarter-2026-revenue-827), which discusses a data-centre storage project, but project-specific economics are not public in the inspected announcement. A [CBRE market update](https://www.cbre.com/insights/reports/european-power-markets-and-battery-storage-update-oct) is useful context but dated 29 September, outside the preferred news window. Neither supplies inputs to the implemented screen.

## Buyer and value

Developer, fund or lender buying investment diligence or repeatable portfolio screening. Business KPI: change in NPV and zero-NPV upfront budget under declining revenue assumptions. Deliverable: auditable evidence/assumption pack and sensitivity report. Avoided overvaluation is a risk metric, not realised cash savings. No sales conversion or fee is assumed.

## Implementation

- New Project Finance Analyst role instance and reusable `bess_revenue_concentration_screen` skill contract.
- Packaged user/system prompts, handoffs, explicit tool permissions and acceptance criteria.
- Validated annual revenue-path and cash-flow tools; bounded planner and deterministic review.
- CLI, gallery plot, reproducible exports and discount-rate sensitivity.
- Optional adapter actually calls EDI's existing BESS loader and row validator. Its inventory does not set financial assumptions.

Input classifications: two imported published-model outputs; illustrative asset/cost assumptions and future paths; calculated financial results. No real plant performance, realised investment return or live LLM benchmark.

## Reproduction and evidence

`energy-agents-bess --output outputs/bess_saturation`

`python examples/business/plot_bess_saturation.py`

Expected illustrative NPV: flat EUR 23.815m; saturation EUR 1.555m; severe EUR -3.884m. Saturation reduction vs flat: EUR 22.260m. Full limitations and assumptions: `docs/sphinx/source/bess_business.rst`; machine-readable inputs/prompts: `src/energy_agents/data/business/`.

EDI knowledge catalogue consulted at aa842b959bebe8b4279a449f91176be26f0ad6a5. Current source inspected at 600db672269079ab8a92224ad5de3cf80e8206bf. Repository state: #2 merged to main; #3 merged to old feature branch, awareness absent from main. No existing open PR for this case.

## Publication

Branch: `feat/bess-revenue-saturation-case`. PR: https://github.com/julianascencio/energy-agents/pull/4. Final check status is available on the PR's Checks tab. Leave open for review.

## Local validation completed

67 tests passed; Ruff, wheel/sdist build, installed-wheel CLI, strict Sphinx build and gallery execution passed. Plot visually inspected. Optional EDI loader and validator executed on 71 Polish records: 67 announced, 2 operational, 2 under construction. Input hash: `819e99ab0a0ede2f41b678a3e67dff3f9a218ff66d77952a8a505336d46c5fb0`. Counts describe the retrieved catalogue, not the national market. No live LLM run.
