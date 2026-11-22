# Battery augmentation for maintained storage duration — 22 November 2026

## Selection and repository checkpoint

Selected [SIE-155-2026-LCE](https://sie.gob.do/wp-content/uploads/2026/11/SIE-155-2026-LCE-EDES-LP-NGR-01-2026.pdf), adopted 19 November; official publication date unknown (blank index), accessed 22 November. [Secondary coverage](https://portal-energiaestrategica.vercel.app/es/notes/republica-dominicana-redobla-la-apuesta-y-lanza-nueva-licitacion-de-900-mw-renovables-con-baterias) is dated 22 November. The search began with 72 hours and allowed seven days for verified event dates. No trending claim. The public resolution provides the duration/lifetime context; absence of full annexes prevents tender pricing/compliance conclusions but does not prevent a clearly bounded synthetic capacity-cost comparison.

Compared candidates:

| Candidate | Verified dates and selection rationale |
| --- | --- |
| SIE renewable/storage tender | 19 November resolution; new maintained-duration question, strong primary evidence, distinct cohort/cost capability. Selected. |
| [EU buildings compact](https://energy.ec.europa.eu/news/eu-backs-global-compact-cut-energy-bills-and-emissions-buildings-2026-11-20_en) | Announcement and endorsement 20 November; collective nonbinding intensity target, not evidence for a specific building's retrofit cash flow. |
| [Nordex C1 acquisition](https://www.nordex-online.com/en/2026/11/nordex-group-to-acquire-c1-connections-adding-specialist-onshore-tower-engineering-expertise/) | Primary announcement 11 November despite later coverage; outside seven days and financial terms undisclosed. |
| [ACME BESS commissioning coverage](https://solarquarter.com/2026/11/21/acme-solar-commissions-51-87-mw-bess-capacity-in-rajasthan/) | 21 November article describes 20 November disclosures and 22 November planned COD; filing not independently retrieved, no new contract economics; existing firm-supply case is closer. |
| Spain hourly correlation | Already the subject of open PR #30; no duplicate implementation. |

Solar/wind/hybrid plants and grids are addressed by the selected storage case; energy-market, buildings/data-centre and hydro leads were also considered in the preceding checkpoint. No requirement to force a case per technology. The novelty is maintained-duration cohort sizing and augmentation timing, not generic tender preparation (already covered by storage-bid).

Inspected energy-agents main `f8150df9a4272bf2b97042a61b3b785a92450057`: README, architecture, finance role, orchestrator, existing skills, tests, gallery, workflows and prior cases. No AGENTS.md found. Earlier professional-role PR #2 merged into main; awareness PR #3 merged into its former professional-role branch. Current role catalogues and EDI operations adapters exist independently. PRs #27–29 are merged. Sole open PR #30 remained at `4b1d33b319e465aa9d30ba757ef90b758c2e0fb7`; its branch was not edited. This case uses a new isolated branch.

Inspected EDI main `e72d9d822b442f6392c80ce12dfc62f738f51ddd` and refreshed a source-derived, case-specific catalogue. Reuse `bess_service_envelope.py` blob `c3d2936e718bb7f30546aa5a15910c92230f1b54`, SHA256 `0653d403fe530320e2d8f517d055ba1fb3c81ad86343e16222a707fa29cec2dd`. Existing pinned public energy-methods 0.1.1 contains matching source. Merchant-finance, PV-degradation and hybrid-dispatch methods were considered and their scope limitations recorded. No new repository-wide catalogue freshness claim.

## Business and implementation

Customer/payer: renewable developer or lender commissioning an auditable storage lifecycle budget/OEM-option review. Role: existing Project Finance Analyst, supplied by deterministic evidence/capacity tools and the existing orchestrator; no new professional agent. Willingness to pay unknown. Appropriate EDI commercial rights would be needed for a commercial product.

Baseline: all required oversizing at service start. Intervention: compatible additions at years 5 and 10, with initially installed capacity sufficient until the first addition. KPI: 15-year battery capacity-cost present value reduction, constant-real USD at service start. This is not revenue, project NPV, an award or realised savings. Full annexes, augmentation permissions, supplier warranties and installation outages remain unresolved.

New `business/augmentation.py` validates evidence and units, sizes whole-MWh cohorts, checks interval endpoints before additions, enforces site/inverter limits and discounts cost timing. Stress scenarios keep designs fixed. A failed comparator suppresses savings and break-even claims. A hash-bound handoff feeds the existing finance role; the saved `data/augmentation/skill.json` contains actual reusable prompts, mandates, schemas, tool permissions, evidence requirements, handoffs and acceptance criteria.

The optional EDI adapter executes the existing service envelope for all 120 plan/year/scenario rows, passing degraded DC capacity and one SOC/efficiency conversion. It does not validate ageing, warranties, costs or tender compliance. The no-key default path is standard-library-only; no LLM run or measured agent advantage. Direct/scripted results must match; LLM costs, tokens and latency remain unknown.

## Results and limitations

All engineering/economic inputs are synthetic: 20 MW/four-hour event, 15 years, 98% annual retention per cohort, 1 MWh DC packs, 90% SOC window, 95% discharge efficiency, USD 180,000/MWh installed capacity, USD 1,500/MWh-year O&M, USD 250,000 per later addition and 8% real discount. Common plant/inverter/grid costs cancel; no terminal value, FX, tax, financing, revenue, penalties or dispatch is valued.

Upfront 127 MWh costs USD 24,490,580.69 PV; staged 104 + 10 + 10 MWh costs USD 22,496,263.37 PV. Conditional difference **USD 1,994,317.32**. Future equipment-price break-even **1.96868 times** base. At twice base, staging increases cost by USD 64,480.71. At 97% retention the fixed upfront and staged designs first fail in years 11 and 4, respectively, so savings are null. This is a scenario envelope, not a probability forecast. Instant additions, compatible cohorts, monotone fade and full initial SOC must be tested before any actual decision.

## Reproduction and publication

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
energy-agents-augmentation --output outputs/augmentation
# Optional existing EDI backend; Python 3.12+
python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
energy-agents-augmentation --edi --output outputs/augmentation_edi
python -m pytest
ruff check .
python -m build
MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Source metadata preserves URL, page/section locators, unknown publication date and retrieved PDF SHA256 `ec451c1dae78fcb2785befcd2e43ab3b0680e36a2bfd2cc2474caa164316b96a`. The source file is not redistributed. `curl -fL` on that URL followed by `sha256sum` can check whether the remote file has changed; retrieval is optional and does not overwrite the reviewed snapshot. Observed source facts, synthetic assumptions and modelled outputs are separate.

Local validation: 24 new tests passed; full suite **581 passed, 2 skipped** (Torch-dependent quantum tests unavailable locally). Ruff, wheel/sdist, isolated installed-wheel offline CLI and strict full Sphinx/gallery build passed. The initial heading-length warnings were fixed and the strict build rerun successfully. Generated chart and HTML numerical tables inspected. Optional EDI execution passed all 120 rows; direct/scripted report parity passed. CI retains the dedicated quantum-backend job and both Python versions, and now executes the new CLI plus EDI integration.

No independent review or current authorized integration claim is established. GitHub rulesets returned an empty list; the main branch-protection endpoint returned 403, so protection requirements are not fully inspectable with this connection. A prior green PR is not evidence for this branch. Exact-head hosted checks and the focused PR link are recorded after publication. No merge, release, third-party contact, control, purchase or deployment performed.

Published non-draft PR: https://github.com/julianascencio/energy-agents/pull/31. Final-head hosted check and review evidence is recorded in the PR description. Publication is distinct from verification, merge and deployment.
