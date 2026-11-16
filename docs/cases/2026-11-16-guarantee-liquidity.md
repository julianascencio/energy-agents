# 16 November 2026 — Bank-guarantee collateral and liquidity

PR: [#28](https://github.com/julianascencio/energy-agents/pull/28).

Selected [Enlight's issuer announcement](https://www.globenewswire.com/news-release/2026/11/16/3403923/0/en/enlight-renewable-energy-and-shemen-yielding-real-estate-sign-agreement-to-advance-development-of-a-data-center-with-planned-power-capacity-of-up-to-150-mw-in-israel.html), published 16 November 2026 at 11:30 ET; agreement announced the same day. NIS 334m estimated aggregate guarantee exposure and equal partner shares motivate a concrete treasury decision. Proposed connection is up to 150 MW; it is not approved capacity. Final regulation and approvals remain unresolved. No trending claim.

## Selection comparison

- [European Commission, 16 November](https://energy.ec.europa.eu/news/electricity-coordination-group-considers-eu-electricity-market-prepared-winter-2026-11-16_en): reports a 12 November coordination meeting and 13 November winter outlook. Regional adequacy does not establish a customer's interruption probability or value of backup; full direct retrieval failed in this review.
- [Enphase, 16 November](https://www.globenewswire.com/news-release/2026/11/16/3403444/0/en/enphase-energy-to-showcase-product-innovations-at-re-2026.html): product showcase ahead of 17–19 November RE+. Indexed issuer text distinguishes pilots and future shipments. No installed-price or comparative loss data for a defensible new economic screen; direct open failed.
- Today's NTT/Bloom republication repeats the existing bridge-power case; wind commissioning, solar/storage construction and hydropower tender leads screened earlier today overlap prior cases or lack project terms. No duplicate case/PR created.

The chosen decision is different from preferred-equity distributions, financing capacity, procurement cancellation or interrupted-load savings: separate bank-guarantee face, cash collateral, fee expense, opportunity cost and contingent loss. Commercial buyer: renewable/data-centre developer treasury team. Offering: bounded bank-offer comparison and liquidity-stress diligence, not a bank quote or financial transaction. Willingness to pay is unknown.

## Implementation and provenance

Base energy-agents main `c8a61091683856c890a5059d0ff6e3d4bd94a445`; instructions, architecture, existing finance role, orchestrator, skills, tests, gallery and case history consulted. No AGENTS.md. Earlier professional-role PR #2 is merged into main, #3 into the former professional-role branch; EDI adapters are already present. PR #27 is open at unchanged `4f2b01e3bf6351b479630fd186dbdcaaee8d701b`; this case does not edit its branch. Isolated new branch used.

EDI main `fc63c5f97e6513e7f290340ddfdce0b80962644a`: consulted source-derived equity capability catalogue and re-read `methods/src/energy_methods/offshore_wind_economics.py`, blob `88f9cd11bfd569fc3b69a0b40d7ffeac9fd3bd87`. Its unlevered real-JPY wind economics cannot supply guarantee liquidity. `data/guarantee/edi_context.json` is a bounded metadata-only adapter; no upstream execution is claimed or dependency added. No new agent: reuse existing finance RoleSpec, orchestrator and numeric validation.

Reusable request, role mandates, schema, allowed tools, handoffs and acceptance contract are in `src/energy_agents/data/guarantee/skill.json`. `business/guarantee.py` provides deterministic calculations and an evidence-to-finance workflow; gallery `plot_guarantee_liquidity.py` prints ledgers and plots fee/collateral sensitivity. Invalid evidence blocks finance; forbidden banking and premature delegation fail.

## Economic results and limitations

All terms are **synthetic assumptions**, with nominal NIS and undiscounted two-year horizon. One partner's exposure is NIS 167m. Baseline 100% collateral / 0.5% annual fee / no setup fee; alternative 25% collateral / 1.5% annual fee / NIS 0.2m setup. Both use 4% annual opportunity spread net of collateral interest, 2% horizon call probability and 40% net loss conditional on call. Initial cash budget NIS 60m; all fees paid upfront; recoveries occur after full-call cash needs.

| Metric | Baseline | Alternative |
| --- | ---: | ---: |
| Face liability (NIS m) | 167 | 167 |
| Restricted cash (NIS m) | 167 | 41.75 |
| Upfront fees (NIS m) | 1.67 | 5.21 |
| Opportunity cost (NIS m) | 13.36 | 3.34 |
| Expected net call loss (NIS m) | 1.336 | 1.336 |
| Total economic cost (NIS m) | 16.366 | 9.886 |
| Initial cash required (NIS m) | 168.67 | 46.96 |
| Additional full-call cash (NIS m) | 0 | 125.25 |

Modelled cost reduction NIS 6.48m; restricted liquidity released NIS 125.25m is NOT profit. Initial-budget feasibility is not solvency: full-call total cash plus fees reaches NIS 172.21m for the alternative. Equal liability/risk across offers is an assumption, not a real credit assessment. Sensitivity varies fee 0–5% and collateral 25/50/100%; no probability-weighted forecast or realised benefit. No compounding, tax, FX, project NPV, land/lease economics or regulatory/engineering eligibility. No live LLM run; cost/latency/tokens unknown. Scripted workflow/direct deterministic parity is tested, not agent advantage.

## Reproduce and verify

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
energy-agents-guarantee --output outputs/guarantee
python -m pytest -q -rs
python -m ruff check .
python -m build
MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Offline/key-free after installation. Custom JSON via `--case`; exports include inputs/hash, workflow/report, source/evidence gaps and EDI metadata. Tests cover independent ledger arithmetic, break-even identity, identical offers, zero exposure/collateral, full calls with recoveries, nonfinite/bool/range rejection, source metadata, isolation and permissions. Local validation: 522 passed, 5 optional quantum-backend tests skipped (Qiskit/Torch absent locally). All 14 new focused tests passed. Ruff, source/wheel builds, isolated installed-wheel CLI smoke and strict full documentation/gallery build passed. Generated plot and ledger inspected. Final exact-head CI evidence will be recorded in the PR, including the dedicated quantum job. Independent approval and current integration claim are not established; no merge, banking action, spending, third-party contact, release or deployment performed.
