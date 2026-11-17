# Firm supply procurement: audit energy coverage and hourly gaps

Status: implemented; publication and exact-head check evidence recorded in the PR.
PR: [#29](https://github.com/julianascencio/energy-agents/pull/29) (non-draft).

## Evidence and selection

Reviewed on 17 November 2026 against energy-agents main
`c8a61091683856c890a5059d0ff6e3d4bd94a445` and EDI main
`fc63c5f97e6513e7f290340ddfdce0b80962644a`.
Both default branches were unchanged from the previous occurrence. Existing PRs
#27 (non-firm load service) and #28 (guarantee liquidity) were open at unchanged
heads; neither branch was edited. Professional roles PR #2 was merged into main,
and #3 into the former professional-role branch. Current main includes the role
catalogue and EDI awareness/execution adapters. No AGENTS.md was present.

Selection compared these substantive recent candidates:

| Candidate / primary source | Event/publication evidence | Decision |
| --- | --- | --- |
| [GWEC/Ember wind–solar–battery study](https://www.gwec.net/news/increasing-wind-in-the-clean-energy-mix-cuts-the-cost-of-electricity-by-nearly-20) | Event dateline 13 Nov; page published 16 Nov | Selected: energy coverage versus full-load hours changes backup capacity and buyer economic exposure; distinct from existing financial settlement and curtailment cases. |
| [PJM Fast Energization proposal](https://insidelines.pjm.com/pjm-proposal-would-cut-interconnection-process-time-in-half/) | 16 Nov announcement of proposed filing | Proposed study timeline is not guaranteed energization. Filing link still unavailable in the inspected announcement; avoid assuming customer savings or approved service terms. Existing non-firm/bridge cases cover adjacent decisions. |
| [BW ESS/Wattmen portfolio](https://bw-ess.com/news/bw-ess-partners-with-wattmen-to-develop-500-mw-battery-energy-storage-portfolio-in-france) | Page 16 Nov; dateline 12 Nov | Capacity and development scope, without project prices or bankable revenue; overlap with existing storage investment/bid capabilities. |
| [EnBW Forbach battery](https://www.enbw.com/press/green-light-for-enbw-battery-storage-facility-in-forbach.html) | Syndicated issuer publication 16 Nov | Shared infrastructure is promising, but indexed English/German power figures differed (41/46 MW), direct primary retrieval failed, and savings were not disclosed. Not used as model evidence. |

Solar, wind, storage, hydro and grid/data-centre leads were compared; building heat
reuse is already covered in #26. No claim that any story is trending. The selected
event lies within seven days and its publication within 72 hours.

The [atlas methodology](https://ember-labs-org.github.io/WindSolarBatteryAtlas_Labs/)
was read directly on 17 Nov. Its coverage is delivered energy divided by demand,
not the fraction of fully supplied hours. Its [landing page](https://ember-labs.org/experiments/wind-solar-battery-atlas)
was updated 16 Nov. Search snippets gave inconsistent Ember report dates;
the case uses the explicitly dated GWEC primary announcement and distinguishes
event date from publication date. No atlas dataset or hourly weather is copied.

## Customer, KPI and commercial scope

Industrial power procurement and the existing Project Finance Analyst role compare
net-delivery offers plus backup. An adviser or software vendor could charge the
buyer for profile diligence and tender screening. Baseline: choose the lower
fixed offer fee. Intervention: audit hourly residuals and include backup cash cost
plus scenario lost contribution. KPI: USD economic cost reduction over the supplied
168-hour window, with cash spending and unserved MWh reported separately.

All customer traces and prices are **synthetic**, intentionally constructed to
demonstrate equal energy coverage with different peak gaps. Both deliver 1,512
of 1,680 MWh (90%). At 2 MW backup the concentrated-gap offer leaves 84 MWh
unserved; the distributed-gap offer leaves zero. At 2,000 USD/MWh lost contribution,
economic costs are 313,600 and 169,400 USD. The conditional reduction is 144,200 USD,
while cash spending increases by 23,800 USD. Break-even lost contribution is
283.33 USD/MWh. At 4 MW backup the cheaper concentrated-gap offer wins by 7,000 USD.
These are neither realised savings nor proof of wind/battery technology superiority.
Published global cost medians are metadata, never used to set offer prices.

## Capability, prompt and provenance

- Deterministic tool: `src/energy_agents/business/firm_supply.py`; CLI `energy-agents-firm`.
- Actual reusable prompt/workflow: `src/energy_agents/data/firm_supply/skill.json`.
- Fully specified inputs: `data/firm_supply/case.json` inside the package; evidence and economic assumptions classified separately.
- Existing evidence gate, finance role, orchestrator and input SHA256 handoffs reused. No new agent, external action or credentials.
- EDI catalogue: `data/firm_supply/edi_capabilities.json`, recorded commit above; generic `simulate_hybrid` method reuses the same source blob as the heat case. Optional zero-storage matching adapter executes the existing public hash-pinned dependency; no repeated storage dispatch or copied dispatch implementation.
- Gallery: `examples/business/plot_firm_supply.py` prints the ledger and plots gaps, costs and backup/lost-contribution sensitivity.
- Guide: `docs/sphinx/source/firm_supply.rst` includes equations, boundaries, commands and input/output contract.

Run `energy-agents-firm --edi --output outputs/firm_supply_edi` after installing
the checkout and `requirements/operations.txt` on Python 3.12+. The default run
omits `--edi` and requires no upstream dependency; both are key-free and offline
after installation. Separate execution JSON proves whether EDI ran. Direct
deterministic and scripted role results must be exactly equal. No live LLM runs
or benchmarks occurred; LLM cost/latency/tokens are unknown.

## Acceptance and limitations

Focused tests cover independently calculated cash/energy ledgers, choice reversals,
energy-versus-hour coverage, surplus without fictitious storage, zero demand,
nonfinite/boolean/negative inputs, UTC alignment, evidence gates, tampered/stale
handoffs, prohibited actions and EDI source-hash checks. CI retains existing
validation and adds the CLI plus the adapter to operations integration.

The seven days are not representative-year measurements. Instant, perfectly
available backup has no fuel limit; real availability, ramping, fuel, network,
sub-hourly and restart constraints remain unresolved. Net-delivery profiles do
not establish generation or storage feasibility. No tax, discounting, escalation,
resale, emissions or contractual penalty model. Lost contribution is opportunity
cost, not a cash payment. Human procurement diligence remains required.

Publication, verified CI, merge and deployment are separate outcomes. A clean CI
run does not supply a company integration claim or independent review. No release,
deployment, energy trade, physical control, purchase or third-party contact is
part of this case.

Local validation: 20 focused tests passed; full suite 527 passed with six optional
skips. Installing the missing pandas dependency then passed all 16 tandem tests,
including the skipped replay. Five local Qiskit/Torch checks remain delegated to
the retained dedicated CI backend job. Ruff, source/wheel builds, isolated
installed-wheel CLI parity and strict Sphinx/gallery build passed. The plotted
outputs were visually inspected. The optional EDI adapter executed successfully
with parity and source hash
`e404a6724ea9f3a332fb50e307e048edde610e8569a230b5177ca1350d536a39`.
Input digest: `cf077d7df77e80dd3b8e11eeeb54fca9131ce68e6408e85e6d65fa93388bf067`.
Final-head CI and review observations are in the PR description; local results
are not a substitute for those checks.
