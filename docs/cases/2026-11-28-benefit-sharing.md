# CIS Tender 12: equity versus revenue-sharing cash flows

Research date: 28 November 2026. Status: implemented and locally validated;
publication/check/review outcome is recorded in the linked PR. No merge or deployment
is asserted here. PR: [PR #33](https://github.com/julianascencio/energy-agents/pull/33).

## Source checkpoint and selection

The prior run's unresolved CIS guidelines partition is now processed:
[ASL tender page](https://asl.org.au/tenders/cis-tender-12-nem-generation) and its
[26 November guidelines](https://asl.org.au/-/media/services/files/cis/cis-12-nem/cis-tender-12-nem-tender-guidelines.pdf?rev=5931635e776449b485adc597c0dff92a&sc_lang=en),
section 4.3, were read on 28 November. Tender opening was 27 November.
The financial-evidence requirement creates a practical need for comparing proposed
sharing cash flows. The model does not decide qualification, consent or award.
Source facts and dates are separately packaged in `data/sharing/source.json`.
No claim that the story is trending is made.

Candidates compared against the existing gallery:

| Candidate | Primary publication/event | Decision |
|---|---|---|
| CIS Tender 12 | Guidelines 26 Nov; tender opened 27 Nov | Selected: reusable comparison of recipient value, sponsor costs and funding risk; source gap now resolved |
| [Greenvolt Alamogordo solar+BESS](https://power.greenvolt.com/media/news/greenvolt-power-beginning-of-construction-bess-project-in-new-mexico/) | Primary announcement 25 Nov; describes commencement, no separate construction-day date established; secondary republication 27 Nov is not a new event | Existing firm-supply/service-envelope cases cover the principal modelling need; no new dispatch or commercial terms |
| [Ember Italy storage economics](https://ember-energy.org/latest-insights/energy-storage-can-help-cut-italys-power-prices/) | Analysis released 26 Nov; underlying comparisons use earlier market inputs | Strong primary analysis, but existing BESS saturation and hourly firm-supply examples overlap; no realised saving inferred |

The targeted follow-up reuses the previous cross-sector scan and unchanged
hydro, grid, wind, building and data-centre checkpoints; it is not an assertion
that every source was re-reviewed. Greenvolt's primary date corrects the discovery
feed's 27 November date. No additional implementation is opened for those candidates.

## Repository and reuse checkpoint

Base `energy-agents` revision: `142e941b879f746a3187fadb040640e1cd5f5726`.
No open PR existed at intake. Completion-budget PR #32 was already merged at that
revision; it is not duplicated. Earlier roles PR #2 is merged; awareness PR #3
was merged to its earlier feature branch, not directly to main. Reused current
roles, adapter catalogue, tests and gallery rather than assuming those PRs open.
No `AGENTS.md` was present in the inspected checkout.

Focused EDI revision: `0f3c90cbb13b8ecc72f5d6c6b44beb319a7d4aaf`.
The merchant-finance source was read; the unchanged physical service-envelope
checkpoint was reused. `data/sharing/edi_capabilities.json` records symbols,
blob revisions, scope and fit. Neither method evaluates community rights;
the bounded adapter exposes metadata only. No EDI execution is claimed and no
upstream dependency, source or scientific method is duplicated.

## Business opportunity and specification

Buyer: renewable developer, community investment adviser or project-finance team.
Offering: auditable proposal comparison and funding-risk review alongside human
community and legal advisers. Willingness-to-pay and fees are unmeasured.
Existing role: `project_finance_analyst`. Tools: schema validator, SHA256-bound
cash-flow audit, deterministic sharing screen and dependency-enforced orchestrator.
No new professional agent is introduced.

Baseline: supplied common-equity sharing. Intervention: supplied gross-revenue
sharing. KPIs: recipient NPV, sponsor incremental cost PV and annual operating
funding gaps. The algebraic revenue fraction at equal recipient NPV is explicitly
not a regulatory equivalence test. Existing preferred-equity work models coupon
priority and funding; this case models benefit-sharing timing and affordability.

Actual reusable prompts, role mandates, schema, tools, evidence requirements,
handoffs and output/acceptance contracts are in `data/sharing/skill.json`.
Evidence precedes finance; changed handoffs are rejected. No bid submission,
agreement, contact, spending, trade or physical control can be dispatched.

## Synthetic results and uncertainty

All financial values are assumed, not actual tender/project economics. Horizon
20 years, nominal AUD with 8% year-end discount. Initial equity AUD50m; revenue
AUD30m/year; after-debt/tax distributable cash AUD8m/year; terminal proceeds AUD40m.
Gifted 5% equity: AUD100k setup and AUD20k/year administration. Revenue sharing:
1.5% for all 20 years, AUD200k setup and AUD50k/year administration. Neither
recipient contributes upfront in the reference case.

| Metric (AUD, present value) | Equity | Revenue sharing |
|---|---:|---:|
| Recipient NPV | 4,356,355 | 4,418,166 |
| Sponsor incremental cost PV | 4,652,718 | 5,109,074 |

Revenue sharing increases recipient NPV by AUD61,811 but sponsor cost by AUD456,355.
Equal-recipient-NPV revenue fraction is 1.4790147%, holding other assumptions fixed.
These are value transfers and costs, not realised revenue or an improvement in
overall project returns. The example sweeps 4%, 8% and 12% discount rates and
5..20-year revenue-sharing durations. A stress with revenue 30% lower and only
AUD0.1m annual distributable cash produces AUD5.3m cumulative operating funding
gaps for revenue sharing; this is not peak borrowing. Terminal proceeds cannot
hide earlier operating cash shortages. Contributions, zero denominators and
infeasible parity fractions have dedicated tests.

Limitations: common discount rate does not price unequal risks/rights; no actual
community evidence, terms, recipient tax, borrowing interest, capital calls,
covenant or tax-shield recalculation. Support, eligibility and contractual
arrangements remain unverified. No LLM execution, field validation, scientific
superiority or agent performance uplift. LLM cost, tokens and latency are unknown.
The scripted workflow matches the direct deterministic baseline exactly.

## Reproduction and validation

```sh
python -m pip install -e '.[dev,docs,quantum,mcp]'
energy-agents-sharing --output outputs/sharing
MPLBACKEND=Agg python examples/business/plot_benefit_sharing.py
python -m pytest tests/test_sharing.py
ruff check .
python -m build
python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Core CLI: offline/key-free, Python 3.11+. Entire existing gallery uses the pinned
operations wheel on Python 3.12+. Optional existing quantum tests require the
`quantum-hybrid` extra (CPU torch is sufficient). JSON outputs preserve inputs,
workflow, audit, prompts, catalogue and results. Plots show annual receipts,
recipient versus sponsor PV and duration/rate sensitivity; generated tables and
figure were inspected. New tests cover hand-calculated conservation, discounting,
terminal timing, contributions, funding gaps, source/schema validation,
permissions and handoff integrity.

Validation on 28 November: 679 tests passed, zero skips (32 new tests); Ruff
passed; wheel and sdist built; installed-wheel offline CLI passed; strict
Sphinx/gallery passed with zero warnings after correcting two title underlines.
A third-party pytest plugin emitted one deprecation warning; no tests failed.

Independent review and any company integration claim are separate outstanding
gates; local self-review is not independent review. GitHub check results must be
read on the published head. Provider completion, publication, check success,
merge and deployment remain separate outcomes. No schedules or company intake
records were created. Only the completed source/model partition advances; review
and integration remain pending until separately verified.
