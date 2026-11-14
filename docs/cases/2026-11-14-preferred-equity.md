# 14 November 2026 — Preferred equity funding and cash priority

## Selection and source chronology

Selected [Captona's company announcement](https://www.businesswire.com/news/home/20261110915054/en/Sunrun-Partners-with-Captona-on-its-Latest-Preferred-Equity-Project-Finance-Transaction), announced/published 10 November 2026; [13 November coverage](https://www.energy-storage.news/sunrun-closes-preferred-equity-investment-for-us-distributed-energy-resources-totalling-110mwh-of-batteries/) is follow-up reporting, not a new transaction date. Expanded the search to seven days. Company-reported portfolio: 9,400 projects, 74 MW solar, 110 MWh storage, more than 20 states. No investment amount, coupon or distribution terms disclosed. No trending claim.

Compared 13 November [UK BESS floor-contract coverage](https://www.energy-storage.news/toll-makes-way-for-floor-offtake-contracting-beginning-to-standardise-in-uk-bess-market/): useful commercial risk topic, but its underlying panel occurred in October and the existing VPPA/revenue screens overlap. [Statkraft's 13 November Neilston announcement](https://www.globenewswire.com/news-release/2026/11/13/3402415/0/en/statkraft-first-grid-forming-battery-is-operational.html) is current but lacks asset-level stability-service economics. NYSERDA's 12 November solicitation already has the storage-bid case. Broad solar/wind/grid/hydro searches also returned preliminary investment targets and policy headlines without bounded new decisions. Preferred-equity cash priority adds a reusable capability absent from the existing wind-debt service screen.

## Repository and capability inspection

Energy-agents base main `f465e6afb43a52f41b151c199144b53c3bbf441f`; no open PRs or AGENTS.md found. Inspected README, roles/finance helper, orchestrator, tests, gallery, workflows and prior case records. PR #2 is merged into main; awareness PR #3 merged into its former professional-role branch. Existing operations adapters provide EDI execution independently of that old PR. No assumption that #3's full knowledge module is on main.

Consulted the source-derived debt capability catalogue and fetched EDI's offshore economics module at `3d6000b9d981bbbf594eeee296a391c03f78c6e7`, blob `88f9cd11bfd569fc3b69a0b40d7ffeac9fd3bd87`. It provides real-JPY wind LCOE and tariff calculations, explicitly excluding finance/taxes; it cannot calculate preferred cash allocation. Saved bounded metadata adapter under `data/equity/edi_capabilities.json`. No EDI execution claimed. No scientific code copied. Full gallery retains the existing public hash-pinned energy-methods 0.1.1 dependency.

## Customer and decision

Customer: solar/storage development CFO or project-finance analyst comparing a common-only equity contribution with preferred financing. Plausible offering: financing term-sheet scenario audit; no willingness-to-pay or realised customer revenue evidence. Reuse Project Finance Analyst, shared evidence validation, input digest and orchestrator; no new role.

KPI: initial sponsor cash requirement, sponsor NPV, investor NPV and unpaid coupon/capital at liquidation. Baseline and intervention share identical after-debt project cash. Model is deliberately a synthetic illustrative portfolio, not the announced installations. Actual tax-credit mechanics, debt covenants, preferred participation, credit risk and legal rights require separate diligence.

## Model and reusable contract

Versioned `data/equity/skill.json` stores actual request, role mandate, input schema, bounded tools, evidence requirements, handoffs, outputs and acceptance criteria. Evidence validates classification/schema before an isolated finance handoff. Forbidden external actions and premature finance delegation are rejected. Unknown provider cost/tokens/latency stay null; no live LLM execution or superiority claimed.

Synthetic nominal USD: 10m equity need, 4m preferred contribution, 8% annual cumulative non-compounding coupon, 100k initial fee, five years, 10% discount, annual distributable cash of 0.5/0.6/0.8/1.0/1.2m and 12m terminal after-debt proceeds. Cash pays coupon/arrears, terminal preferred capital, then common. Negative cash is rejected; capital calls are unsupported. Preferred capital is not redeemed early and receives no residual participation. Unpaid terminal claims remain shortfalls, not invented future receipts.

Result: sponsor initial cash falls from 10m to 6.1m (3.9m saved). Baseline sponsor NPV is $430,639.98; preferred-funded sponsor NPV is $633,902.93; incremental sponsor NPV $203,262.94. Preferred-investor NPV is **negative $303,262.94** at the same discount rate. Their incremental values sum to minus the $100k fee. This is investor value allocation under assumed prices, not operational improvement or proof the financing is commercially obtainable. The reference preferred scenario has no coupon/capital shortfall. Gallery stresses exit proceeds and operating cash; it assigns no probabilities.

## Reproduction and checks

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
python -m pip install --no-deps --require-hashes -r requirements/operations.txt
energy-agents-equity --output outputs/preferred_equity
python examples/business/plot_preferred_equity.py
python -m pytest
ruff check .
python -m build
sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Offline CLI exports input, trace/report, input hash and EDI metadata. Gallery prints annual cash reconciliation and economics, with allocation and two-variable sensitivity plots. Tests cover independently calculated arrears, terminal impairment, no compounding, no interim redemption, zero preferred capital, conservation, fee/value identities, invalid inputs, evidence failure, permissions and handoffs. Publication and actual validation status follow below.

Local validation: 488 tests passed, two optional neural-backend tests skipped because Torch is unavailable. Ruff, wheel/sdist build, installed-wheel offline CLI and strict full documentation/gallery build passed. Generated chart and numerical output inspected. No independent review or live LLM benchmark performed. Hosted checks will be recorded on the PR at the final head.

Published non-draft PR: https://github.com/julianascencio/energy-agents/pull/24. Exact-head hosted CI results are recorded on the PR after execution. No independent review or current authorized integration claim is available; no merge or deployment performed.
