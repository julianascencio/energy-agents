# 2026-11-05 — Wind commissioning acceleration

Selected [Orsted's 5 November issuer update](https://orsted.com/en/company-announcement-list/2026/11/orsted-delivers-strong-earnings-with-19--ebitda-gr-152708491). It provides a current commissioning milestone story with a concrete project-delivery decision. Search indexed the issuer release and EQS syndication; direct full-page retrieval returned an error. Only the reported milestone context is used; event dates are not inferred and all example inputs are synthetic.

Alternatives considered: Clean Horizon's 4 November storage-revenue article duplicates the prior BESS case (#4); Eos's 5 November storage announcement was considered but lacks the project economics needed for a data-centre case; UK curtailment dashboards surfaced provisional derived data and were less suitable than the primary issuer event for this iteration. No trending-audience claim.

Buyer: asset owner, EPC manager or project financier. Commercial deliverable: schedule/value review showing which conditional resource purchases affect commercial-operation timing. KPI: expected contribution brought forward less acceleration costs, with an explicit no-action baseline. No realised benefit or customer fee is asserted.

Implementation: Project Controls Engineer RoleSpec; packaged prompts and skill contract; DAG schedule evaluator; bounded exhaustive package ranking; permission-enforced runner; price sensitivity; gallery and reproducible outputs. No controls, orders, approval waivers or live LLM benchmark.

Reference hypothetical outcome: day 25 to day 20, 4,800 MWh brought forward, EUR 336,000 expected contribution, EUR 140,000 cost, EUR 196,000 net benefit. The turbine-only option has zero completion benefit and costs EUR 40,000. Missing real inputs include commissioning acceptance, weather/resources, capture price and contract terms.

Reproduce: `energy-agents-commissioning --output outputs/wind_commissioning` and `python examples/project_delivery/plot_wind_commissioning.py`.

EDI catalogue aa842b959bebe8b4279a449f91176be26f0ad6a5 and source 600db672269079ab8a92224ad5de3cf80e8206bf consulted. No suitable critical-path method found; wind metadata and forecast capability discovered but not executed. No artificial claim of integration.

Branch: `feat/wind-commissioning-revenue`. PR link will be recorded after publication. Leave open for review.

Local validation: 69 tests passed; Ruff and diff whitespace checks passed; strict Sphinx/gallery build passed and rendered chart inspected; source and wheel distributions built; installed-wheel CLI smoke completed. Reference outputs reproduced. Live LLM not run.
