# 27 November 2026 — Battery project cost to complete

## Inspection and selection

Inspected energy-agents main `9a8a56b3be12e734183a0350600bf874bdee8ff0`:
README, finance and commissioning roles, orchestrator, business skills/tools,
tests, gallery, build configuration and quality/docs workflows. No AGENTS.md
found in the tree and no open PRs at initial refresh. PR #2 professional roles
merged into main; #3 awareness merged into the former professional-role branch.
The current source-derived catalogues and adapters are present independently.
Hourly-correlation #30 and battery-augmentation #31 are merged, not unfinished
PRs. Prior commissioning acceleration, transformer reservations and guarantee
liquidity do not perform scope-equivalent cost-to-complete reconciliation.

Searched 24–27 November (72 hours), then 20–27 November to compare a stronger,
distinct primary story. No claim that any story is trending.

| Candidate | Verified date and source | Decision |
|---|---|---|
| Yukon Energy takes over BESS completion | [Utility announcement](https://yukonenergy.ca/about-us/news-events/yukon-energy-terminates-contract-with-sungrid-solutions-and-announces-new-approach-to-complete-the-whitehorse-battery-storage-project), published 23 Nov; announcement date is used, exact legal termination date unspecified | Selected. Clearly identifies outstanding scope/prices and budget uncertainty; supports a distinct owner/finance ledger workflow. No actual remaining-cost estimate is inferred. |
| Terna second MACSE results | [Primary announcement](https://www.terna.it/en/media/press-releases/detail/completed-second-macse-auction), indexed 24 Nov; full page retrieval limited | Relevant storage auction; retrieved primary excerpt establishes award/pricing context, but generic bid/margin screening overlaps existing case. No unsupported detailed terms used. |
| Irish RESS 6 provisional results | [EirGrid report](https://www.eirgrid.ie/sites/default/files/publications/RESS-6-Provisional-Auction-Results-Report.pdf), dated/published 25 Nov; auction completed 13 Nov | Primary solar/onshore-wind evidence; provisional status retained. Nonprice scoring is potentially distinct, but results alone are insufficient for a faithful scoring implementation; not conflated with realised generation or project returns. |
| Wyoming Intertie funding | [DOE announcement](https://www.energy.gov/articles/energy-department-announces-28-billion-loan-strengthen-grid-reliability-and-help-lower), 17 Nov | Repeated in 26 Nov digest; original event/publication outside seven-day window. |
| Ice Harbor fish-friendly turbine | [USACE source](https://www.nww.usace.army.mil/Media/News-Releases/Article/2950861/22-013-corps-assembles-and-begins-installing-2nd-advanced-technology-turbine-at/), 2022 release recounting 2019 tests | Repeated in 25 Nov coverage; old underlying result, not a fresh hydro case. Full page returned 403; date/result only established from indexed primary excerpt. |
| Data-centre electricity/water and hybrid announcements | 25–26 Nov search results included secondary water-consumption research coverage and a nonbinding Tamil Nadu hybrid MoU | No selected operating/customer dataset with quantified intervention; existing building, heat-reuse, campus, bridge-power and firm-supply capabilities reviewed for overlap. Not promoted to verified primary case evidence. |

Observed context is limited to the utility's CAD35m budget, CAD25.7m original
contract value, owner-prime approach and 2027 completion target. Remaining prices
are unconfirmed. Grant figures in the announcement do not reconcile exactly;
they are recorded as a discrepancy, not silently corrected or used in the model.
No legal entitlement or damage estimate is made. No source article is vendored.

## Business decision and implemented capability

Buyer: utility capital-projects team, asset owner or lender. Plausible offering:
paid remaining-scope/invoice/quote reconciliation with financing stress review;
no measured demand, fee or revenue is asserted. Existing finance role is reused.

Baseline: replacement EPC for the remaining work. Intervention: owner-prime
packages with identical declared scope. KPI: conditional forward-cost reduction,
gross budget headroom, peak new funding and financing shortfall over 12 months.
All project, price, service, funding and timing inputs are **synthetic**. CAD35m
is used as an illustrative budget scale, not as an actual Whitehorse forecast.

`business/recovery.py` validates scope/payment contracts, calculates gross
forecast at completion and monthly cash funding, and tests physical comparability.
Sunk costs remain in the gross project budget but cancel from prospective savings.
Certified unpaid obligations are separate from new quotes. Grants affect financing,
not the gross budget; disputed recoveries never count as available cash. Within
month outflows precede receipts conservatively. Receipts beyond the horizon are
disclosed. No probability, borrowing interest, taxes, operating revenue or NPV.

Packaged `data/recovery/skill.json` saves the actual reusable request, role mandates,
input schema, bounded tools, evidence requirements, handoffs, output contract and
acceptance criteria. Source and synthetic input records are separate. An
input-SHA256-bound evidence audit must precede finance; finance recomputes and
rejects tampering. Purchasing, claims, controls and communications are unavailable.

## Reproduction and results

```sh
python -m pip install -e '.[dev,docs,quantum,mcp]'
energy-agents-recovery --output outputs/recovery
python examples/business/plot_completion_budget.py
python -m pytest tests/test_recovery.py
ruff check .
python -m build
python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
energy-agents-recovery --edi --output outputs/recovery_edi
MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Core is offline/key-free Python 3.11+; optional EDI and strict full gallery use
Python 3.12+. The CLI exports the input snapshot, report, workflow, audit, skill,
capability catalogue and actual optional-execution record. Gallery prints scenario
tables and plots gross budget, monthly funding and quote sensitivity.

Synthetic CAD24m paid + CAD2m unpaid + new quotes CAD9m (EPC) / CAD7.6m (owner)
produce gross forecasts CAD35m / CAD33.6m: **CAD1.4m conditional cost reduction**.
With CAD1m opening cash and a CAD1.5m month-ten assumed grant, peak new funding
is CAD10m / CAD8.6m, versus terminal CAD8.5m / CAD7.1m. An assumed CAD8.8m funding
limit leaves a CAD1.2m EPC shortfall. CAD2m disputed damages are excluded.

Owner quote uplift of 18.4211% removes the cost advantage; 20% makes owner
completion CAD120,000 more expensive. A grant delayed to month fourteen increases
terminal funding CAD1.5m, without changing earlier peak funding or gross budget.
The same hypothetical 10MW/60MWh DC asset is used for both plans; 100% initial SOC,
10% reserve, 95% efficiency, four-hour 10MW target. At 70% usable capacity it
supports only 8.9775MW, and conditional savings are null. The energy envelope is
not a safety, commissioning, cold-damage or winter-capacity determination.

Actual client work needs complete paid/unpaid ledgers, disjoint scope and quotes,
contingencies, financing and grant agreements, settlement evidence, OEM testing,
engineering acceptance and procurement review. None was obtained or invented.
Direct deterministic arithmetic and scripted evidence/finance workflow match;
no LLM run, field validation or agent performance benefit is claimed. LLM cost,
tokens and latency remain unknown.

## EDI reuse and provenance

Refreshed the focused capability catalogue at EDI main
`eea4916ef3cd43a5805c9584b7f4bcf5df4c3505`. Read service-envelope and margin-relief
source; consulted the existing merchant-finance catalogue entry. Reused the
existing `bess_service_envelope.screen_bess_service` with an explicit bounded
adapter; no method copied. Blob `c3d2936e718bb7f30546aa5a15910c92230f1b54`
remains unchanged from the augmentation catalogue. The installed method is guarded
by SHA256 `0653d403fe530320e2d8f517d055ba1fb3c81ad86343e16222a707fa29cec2dd`.
The existing hash-pinned energy-methods 0.1.1 wheel executed four scenario
crosschecks successfully. This verifies single-event arithmetic only, not financial
assumptions or whole-EDI compatibility. Upstream noncommercial licensing requires
appropriate rights for any commercial deployment. No new credentials or live API.

## Validation and publication

36 focused tests passed, including independent budget/cash arithmetic, adverse
quotes, late and disputed receipts, zero costs, scope/payment rejection, evidence
integrity, permissions, handoffs and actual EDI parity/hash rejection.
Full local suite: **647 passed, zero skips** on Python 3.12.14 after installing
optional test dependencies. Ruff and whitespace checks passed. Wheel and source
distribution builds passed; the installed-wheel CLI ran in an isolated environment
outside the checkout. Strict Sphinx/gallery build passed after fixing an RST
heading; generated tables and the three-panel figure were inspected. No benchmark
or usage measurement is inferred from test runtime.

Published [PR #32](https://github.com/julianascencio/energy-agents/pull/32), non-draft,
from unique branch `case/20261127-completion-budget`. Main was unchanged and no
other open PR existed immediately before publishing. Final-head CI/check evidence
is recorded in the PR description after this history-link commit; local success
is not a claim of successful GitHub CI. Independent review is not completed and no
current company integration claim was found. Default-branch protection inspection
returned HTTP403; rulesets returned an empty list. These are unresolved merge
gates. No merge or deployment performed by this run.
