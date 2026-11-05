# Industrial load shifting — 2026-11-05

Selected the [IEA Spain press release](https://www.iea.org/news/accelerating-electrification-can-unlock-the-full-benefits-of-spains-renewables-leadership), dated 5 November 2026, from the current 72-hour window. Primary indexed release retrieved; direct report page unavailable. Its demand-flexibility theme motivates an industrial energy manager; all case inputs are synthetic.

Other candidates: REE's 3 November adjustment-services revenue announcement requires eligibility and settlement inputs not available here. BESS saturation and wind commissioning duplicate open PRs #4/#5. This case instead addresses a consumer electricity bill with unchanged production.

Deliverables: professional role, packaged task contract, prompt, optional provider adapter, deterministic optimisation tool, permission-enforced runner, runnable gallery, CLI, economic sensitivity, tests and documentation. EDI source 600db672269079ab8a92224ad5de3cf80e8206bf inspected for REE generation and hybrid dispatch; discovery only, no false site-level or tariff substitution.

Buyer: industrial operator or ESCO. Commercial offering: site-specific production/energy feasibility study. KPI: avoided net electricity expense less rescheduling costs, for a single synthetic day. No revenue guarantee, annualisation or claim of live LLM superiority.

PR: [#6](https://github.com/julianascencio/energy-agents/pull/6). Leave open for review.

Reference outcome: EUR 3,320 baseline cost versus EUR 2,240 including EUR 160 rescheduling fees; EUR 1,080 net saving on the synthetic day. Both schedules deliver 8 MWh of batch production. Export credits decrease by EUR 280. No annual extrapolation.

Validation: 69 tests passed, Ruff passed, strict Sphinx/gallery build passed, rendered chart inspected, wheel/sdist built and installed-wheel CLI reproduced EUR 1,080. Live LLM not run.
