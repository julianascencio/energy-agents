# Data centre bridge-power decision — 6 November 2026

## Repository status checked

Base energy-agents main: 84fddd82f7788cd55451ee82e606895fdcf7c4df. No AGENTS.md found.
GitHub PR metadata confirms #2 and #4–#9 merged; prior BESS, commissioning and
industrial-flexibility cases are on main. #3 is merged into the former professional
role branch, not main; no knowledge module is present on main. No open PRs found
at selection time. Preserve this distinction; do not assume an open stack or silently
restore the awareness feature as part of this case.

## Candidate evidence and selection

All retrieved 6 November 2026; publication and announcement dates below.

| Candidate | Primary source/date | Decision |
|---|---|---|
| NTT/Bloom 900 MW onsite power agreement | [Issuer](https://www.bloomenergy.com/news/ntt-data-announces-agreement-with-bloom-energy-for-900-mw-of-onsite-power-generation-across-multiple-data-center-projects/), published/event 5 Nov | Selected: material speed-to-power decision, reusable economic screen; deal economics unavailable |
| Ørsted commissioning/results | [Issuer](https://orsted.com/en/company-announcement-list/2026/11/orsted-delivers-strong-earnings-with-19--ebitda-gr-152708491), published 5 Nov; milestone timing only as reported | Reject: commissioning acceleration already covered in #5 |
| Eco Wave Power authenticated transactions MoU | [Issuer](https://www.ecowavepower.com/wiseqey-sealsq-sealcoin-and-eco-wave-power-sign-three-year-mou-and-demonstrate-trusted-energy-transactions-for-ai-data-centers/), published/announcement 5 Nov; demonstration date not separately established | Reject: no commercial settlement/customer economics for credible runnable revenue estimate |

No trending claim. News supplies the decision motivation, not financial calibration.
The 900 MW and planned 2027 shipments are issuer statements, not realised operations.

## Customer, role and measurable business value

Data centre developer/fund asks whether temporary onsite power is worth pursuing
versus waiting for grid connection. Existing Project Finance Analyst receives a
validated case through the existing orchestrator. Small deterministic screen and
versioned skill; no new role manufactured. Potential commercial offering: paid
project screening and customer-specific contract sensitivity diligence. No measured
willingness to pay or product revenue.

Synthetic example: 10 MW IT, 1.3 PUE, 80% utilization, 95% availability; 730-hour
months; EUR 300/IT-MWh contribution before electricity; EUR 140/facility-MWh
all-in variable power; EUR 100k/month fixed service and EUR 2m upfront. Nine months
of earlier operation (month 3 versus 12), annual discount 10%, end-month payments.
Net monthly cash EUR 554,664; incremental NPV EUR 2,685,637.47; break-even margin
EUR 242.70/IT-MWh. Baseline wait incremental NPV is zero. Same post-grid operations
cancel. No extrapolation to NTT, no realised savings, no LLM advantage.

Sensitivity plot varies margins and grid timing. Cost basis explicitly excludes tax,
financing, carbon, SLA penalties, minimum-take and stranded-contract costs. Those
need customer evidence; service feasibility, gas and permits are unvalidated.

## Source-derived EDI reuse

Inspected EDI commit 036429f93354749517d91ac62b18390ec7bccddc. Reused the catalogue
builder from awareness PR #3 commit a0ffedf911de8f6847fa603b7e55cdc45df5da34 without
merging its agent. Refreshed all 735 in-scope files / 1,481 symbols / 71 gallery
examples with zero errors; retained focused entries and full coverage metadata in
`src/energy_agents/data/bridge_power/edi_capabilities.json`. Snapshot is pinned,
not claimed current to remote HEAD. Reviewed data centre loader/validator, package
metadata and catalogue example. No suitable bridge valuation method identified.
Executed `inspect_edi_inventory` using EDI 0.1.0 source on Python 3.12: 3,330 records
validated; result/hash in `edi_execution.json`. Existing loader/validator reused;
no duplicate project connector or scientific model. Inventory is context only.

## Prompts, workflow and reproduction

Actual user prompt, role mandate, input schema, tools, handoffs, output contract and
acceptance criteria: `src/energy_agents/data/bridge_power/skill.json`.
Input scenario: adjacent `case.json`. Gate -> finance handoff uses fixed runners;
source contents cannot authorize controls or purchases. Schema validation does not
verify source truth. Human diligence required.

```
python -m pip install -e ".[dev,docs]"
energy-agents-bridge --output outputs/bridge_power
python examples/data_centers/plot_bridge_power.py
python -m pytest -q
ruff check .
python -m build
sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/_build/html
```

CLI report contains trace, hash, classifications and cash flows. Gallery executes
same baseline and workflow and asserts equality. LLM calls not executed; provider
cost/latency/tokens unknown. The optional configured OrchestratorPlanner may replace
the deterministic scheduler, but there is no claim of improved economic results.

## Publication and validation

PR: https://github.com/julianascencio/energy-agents/pull/10 (non-draft, left open).

Local validation: 173 tests pass; Ruff and diff checks pass; wheel/sdist and
installed-wheel CLI smoke pass. Strict documentation build executes the gallery
without warnings; sensitivity chart visually inspected. GitHub quality and
documentation checks must be read on the current PR head; their live status is
not frozen in this record. No live LLM/provider benchmark was run.
