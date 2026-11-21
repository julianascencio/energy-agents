# Spanish data-centre hourly-correlation shaping screen

- Research/access date: 21 November 2026; no trending claim.
- Selected event: Real Decreto 1032/2026 adopted 20 November, BOE publication
  21 November, effective 22 November. Primary text:
  https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-24439
- Announcement: https://www.miteco.gob.es/es/prensa/ultimas-noticias/2026/noviembre/el-gobierno-aprueba-el-real-decreto-para-la-sostenibilidad-energ.html
- Publication index: https://www.boe.es/boe/dias/2026/11/21/
- PR: publication pending; link will be recorded after creation.

## Selection and prior work

Compared within the last 72 hours:

| Candidate | Event/publication | Evidence and decision |
|---|---|---|
| Spain data-centre decree | Adopted 20 Nov; published 21 Nov | Selected: published article 9.3 gives a reproducible new tariff calculation and a concrete procurement decision. Earlier announcement-only review is superseded by retrieved BOE text. |
| Aker Solutions Avalon turbine notice | Announced 20 Nov | Primary limited notice to proceed for 150 MW; final award/value depends on regulatory approval in 2027. Less direct new reusable decision than the published tariff. https://www.akersolutions.com/news/news-archive/2026/aker-solutions-gets-go-ahead-for-avalon-combustion-turbine-act-project-in-canada/ |
| Eskom system update | Published 20 Nov; week 13–19 Nov, year-to-date through 19 Nov | Primary operational data, but system EAF and aggregate diesel spending do not establish an asset-specific intervention benefit; existing operations and backup cases overlap. https://www.eskom.co.za/eskom-power-system-further-strengthens-as-eaf-reaches-68-13-and-reinforces-el-nino-resilience-as-load-reduction-continues-decline/ |

Inspected energy-agents main f8150df9a4272bf2b97042a61b3b785a92450057:
roles, orchestrator, existing case records, firm_supply code/prompt/tests/gallery,
packaging and quality/docs workflows. No AGENTS.md found. No open PRs at intake.
PR #2 merged into main on 5 November; PR #3 merged into its former professional-role
branch that day, not left open. Current source already contains the professional
roles and source-derived EDI catalogues. Recent #27–29 are merged; this is a new
case, not continuation or duplication. The existing firm_supply example audits
physical supply gaps; this case models correlation compensation while grid supply
is assumed to meet demand. Additionality is deliberately not inferred from monthly
physical energy coverage.

## Business decision and implementation

Customer/payer: data-centre energy procurement team, supported by the existing
project_finance_analyst role. Offering: a paid shaping-offer diligence report or
metering/contract screening module. KPI: monthly relevant cost reduction and
break-even all-in incremental shaping premium, in EUR before tax, with no annual
extrapolation. No new professional agent or upstream EDI changes.

Implemented `business/correlation.py`, CLI `energy-agents-correlation`, versioned
`data/correlation/skill.json` with actual reusable user prompt, role mandates,
input schema, evidence, tool permissions, handoff and output/acceptance contracts;
packaged BOE articles 8–9 excerpt with raw XML/excerpt hashes; case and EDI metadata;
`plot_correlation.py` in the gallery; method documentation and meaningful tests.

The evidence task validates the full mainland civil month, synthetic scope and
source provenance and produces an input-hash-bound ledger. Finance recomputes
that handoff. Exact rational hourly deviations preserve tariff boundaries.
Unsupported scope, invalid evidence, premature delegation and external actions
fail closed. Direct deterministic and scripted workflow results agree; no live
LLM was executed and LLM cost/latency/tokens are unknown. No agent superiority,
field validation, compliance certification or official invoice is claimed.

## Results and assumptions

Synthetic February 2027: 672 hours, 20 MW constant demand, 13,440 MWh. Baseline
backing is 20 MW for 18 hours and 4 MW for six hours daily: 80% monthly matched
energy, but 18.75% unweighted mean hourly deviation. Article 9.3 band rate is
8 EUR/MWh consumed, yielding EUR 107,520 modelled correlation compensation.
An assumed eligible 12 MW top-up during each gap adds 2,016 MWh and eliminates
standard-path hourly deviation. At EUR 40/MWh all-in incremental premium plus
EUR 5,000 implementation cost, relevant intervention cost is EUR 85,640 and
conditional net reduction EUR 21,880. Break-even quote is EUR 50.85/MWh. At
EUR 60/MWh, the intervention costs EUR 18,440 more. Half top-up delivery at the
base price leaves 9.375% deviation, 5 EUR/MWh exposure and EUR 5,000 net cost
increase. Sensitivities are plotted.

Published tariff rules are source evidence. Customer eligibility, traces,
allocation, additionality satisfaction and prices are assumptions. Outputs are
modelled scenarios, not realised savings. Common energy costs cancel by assumption;
the premium includes incremental replacement/settlement effects. Excludes
additionality charges, other compliance obligations, sanctions, outages, storage
attribution, SRAP/strategic transitions and the national-mix exception. Monthly
charges are provisional under article 9.4. Real work requires legal/specialist
and system-operator review, metering/contract evidence and executable quotes.
Paying a charge is not an alternative authorization to breach obligations.

## EDI reuse and reproduction

Consulted current EDI commit e72d9d822b442f6392c80ce12dfc62f738f51ddd. Refreshed the
bounded catalogue for `methods/src/energy_methods/hybrid_dispatch.py`, unchanged
blob 9a3f8bf79cce6d00d62adcf2ae3a23c9718de82e and SHA256
`e404a6724ea9f3a332fb50e307e048edde610e8569a230b5177ca1350d536a39`.
The existing hash-pinned energy-methods 0.1.1 dependency is reused. The optional
adapter executes generic one-hour supply/load matching with zero battery; it
checks both physical comparators, not legal attribution or tariff logic.
`--edi` was actually executed with parity true; discovery is separately recorded.

```bash
python -m pip install -e '.[dev,docs,quantum,mcp]'
python -m pip install --no-deps --require-hashes -r requirements/operations.txt
energy-agents-correlation --edi --output outputs/correlation_edi
python examples/business/plot_correlation.py
python -m pytest tests/test_correlation.py
ruff check .
python -m pytest
python -m build
MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

Offline/key-free after dependency installation. Inputs, audit, report, scripted
trace and separate EDI execution evidence are emitted. Optional BOE retrieval
and hashes are documented; no live LLM or live customer-data mode.

## Validation and publication evidence

- New tests: 28 passed, including calculation/band boundaries, non-weighted mean,
  no cross-hour netting, DST/leap months, invalid inputs, provenance, handoff and
  permissions, plus executed EDI parity/hash guard.
- Full local suite: 582 passed, 5 skipped. The five existing optional quantum
  backend tests lack torch/qiskit/PennyLane. Attempted CPU torch installation was
  killed (exit 137); these tests are not counted as passes.
- Repository Ruff: passed. Wheel and sdist: passed. Strict documentation/gallery:
  passed with warnings treated as errors. Generated plot and numerical table inspected.
- Expected PR CI: quality test (3.11), test (3.12), quantum-backends,
  operations-integration, and documentation build. PR-only deployment skip is
  not deployment. CI will be inspected on the final published head.
- No independent review or current integration claim established. Rulesets API
  returns []; branch-protection details unavailable to this integration (403).
  No merge or deployment performed; provider work and publication are distinct.
