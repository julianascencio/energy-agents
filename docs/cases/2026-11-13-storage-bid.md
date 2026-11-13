# 13 November 2026 — Storage solicitation development spending

## Selection

Selected [NYSERDA's 12 November 2026 release](https://www.nyserda.ny.gov/About/Newsroom/2026-Announcements/2026-11-12-NYSERDA-Announces-2026-Bulk-Energy-Storage-Solicitation): publication and announced launch both 12 November. Two-step qualification enables a distinct development-spend decision. Procurement quantity is not revenue. No trending claim. Deadline wording has a weekday/calendar conflict; the tool preserves this as unresolved, not a validated deadline.

Compared [FlexGen's 11 November announcement](https://www.businesswire.com/news/home/20261111558600/en/FlexGen-to-Integrate-Long-Duration-Storage-at-MN8-Energys-Mammoth-Solar-Campus): hybrid solar/mixed-duration storage is substantive, but claimed commissioning improvements lack quantified cost/delay evidence and overlap existing commissioning and data-centre cases. [New Jersey's 12 November coverage](https://newjerseymonitor.com/2026/11/12/nj-virtual-power-plant-battery-storage/) describes new VPP/storage programs; overlaps residential reserve work and requires primary tariff/order review before financial use. The 12 November China–Turkey preliminary agreement lacks project financing/timing and is weaker for a runnable decision. Existing solar, wind, markets, buildings, hydro-context and grid cases were reviewed; no reason to force a new example in every technology.

## Repository inspection and reuse

Base energy-agents main e077b5f240852c7fe28c4de2ed530a52f65e8347. No AGENTS.md found. Inspected professional roles, finance workflows/tools, orchestrator, tests, case history, gallery and CI. No open PRs. #2, #21 and #22 are merged into main; #3 merged into feat/professional-role-pv-operations, not main. Existing operations adapters now provide explicit EDI execution capabilities. Private dependency problem in the prior run was resolved through pinned public energy-methods 0.1.1.

Consulted existing procurement/debt EDI catalogues; fetched BESS catalogue source at 53f47b87fe9a6213e85a7fe60d4cf2599ec26658 and saved symbols/hash in data/bid/edi_capabilities.json. This is metadata inspection, not execution. Asset catalogue validation does not answer bid eligibility or probability questions. Reuse existing project_finance_analyst and orchestrator; no new agent or duplicated scientific method. New repository skill is data/bid/skill.json, not a personal ChatGPT skill.

## Customer, economics and acceptance

Buyer: storage developer/development director seeking a tender-readiness and budget review. KPI: expected development-stage net value, preparation spend at risk and break-even conditional project value. No willingness-to-pay evidence. Baseline pays full preparation upfront; intervention stages spending behind qualification, incurring overhead and a competitiveness haircut. No bid is an explicit alternative. Advisory only: no application, communication, spending, trading or physical actions.

All economics synthetic: USD decision-date PV; p(qualify)=0.6; p(award|qualify)=0.25; staging relative award haircut=0.1; qualification $40k; bid preparation $200k; overhead $10k; three-month delay; 8% discount; $2m award-conditional project NPV net of project costs and excluding application costs. No subsidy estimate. Sensitivity varies qualification probability and haircut; model includes losing money and declining to bid. Source facts and assumptions occupy separate objects. No live LLM or field validation; LLM cost/tokens/latency unknown. Deterministic versus workflow parity is tested, not claimed as agent improvement.

Saved prompt/workflow defines units, schema, authority, evidence gate, isolated handoff and output contract. Invalid evidence blocks finance; unknown deadline/eligibility remain explicit. Tests cover independent arithmetic, zero probability, guaranteed award, lost competitiveness, monetary break-even, nonfinite/bool/out-of-range inputs and forbidden actions.

## Reproduction

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
python -m pip install --no-deps --require-hashes -r requirements/operations.txt
energy-agents-bid --output outputs/storage_bid
python examples/business/plot_storage_bid.py
python -m pytest
ruff check .
python -m build
sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

CLI exports inputs, input SHA-256, trace/report and EDI metadata; no key/network needed. Source commentary is not a legal interpretation or a complete solicitation review. Actual contract, manual, project facts, budget and calibrated odds remain human diligence requirements. Validation and PR recorded below after execution.

## Executed results and validation

Expected net value: no bid $0; upfront $60,000; staged $102,286.76. Staging incremental expected value $42,286.76; expected preparation spend falls from $240,000 to $167,713.24. Worst-case loss increases from $240,000 to $246,188.73. Staged break-even conditional project NPV is $1,242,320.28. These are synthetic decision-tree results, not realised customer benefit.

464 local tests passed; five optional quantum backend tests skipped. Ruff, package wheel/source builds and installed-wheel offline CLI passed. Strict full documentation/gallery build passed after fixing a title underline; generated sensitivity chart and numerical table inspected. The full gallery used the public hash-pinned energy-methods 0.1.1 package. Hosted checks and PR link follow publication.

Published non-draft PR: https://github.com/julianascencio/energy-agents/pull/23 — left open for review. Final-commit hosted check status is recorded on the PR after execution.
