Maintaining four-hour battery capacity
====================================================================================================

Decision and evidence
----------------------------------------------------------------------------------------------------

A renewable developer's technical/commercial team must budget storage capacity
through the supply term, rather than buy only beginning-of-life MWh. The existing
Project Finance Analyst role compares **upfront oversizing** with **scheduled
additions**. A plausible paid offering is an auditable OEM-option and lifecycle
budget review for developers or lenders; willingness to pay has not been measured.

The primary context is `SIE-155-2026-LCE
<https://sie.gob.do/wp-content/uploads/2026/11/SIE-155-2026-LCE-EDES-LP-NGR-01-2026.pdf>`_,
dated 19 November 2026. Its renewable tender ceiling is 900 MW; section 4.1 gives
180 months of supply, and section 4.3(VII) requires four-hour storage capability
throughout that term. These are contextual facts, **not an awarded 900 MW battery**.
The official index has no publication date; the PDF was accessed 22 November.
Full bases and amendments remain unreviewed. A successful capacity screen does
not establish eligibility or compliance with the other technical obligations.

All project inputs below are **synthetic**, including 20 MW, prices, degradation,
SOC assumptions and the feasibility of future additions. No field validation,
warranty, revenue, realised benefit or agent superiority is claimed.

Reproduce
----------------------------------------------------------------------------------------------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs,quantum]"
   energy-agents-augmentation --output outputs/augmentation
   python examples/business/plot_battery_augmentation.py
   python -m pytest tests/test_augmentation.py
   ruff check .
   python -m build

The default path is offline and key-free after installation. JSON exports contain
the inputs, source locators and PDF checksum, capacity audit, cash ledger, workflow,
prompt contract and EDI catalogue. Use ``--case path.json`` for another **synthetic**
scenario in the v1 scope. Source metadata cannot be silently replaced.

Optional execution of the existing Energy Data Insights method:

.. code-block:: bash

   # Python 3.12+, existing public wheel and SHA256 pin; no new credentials
   python -m pip install --no-deps --only-binary=:all: --require-hashes -r requirements/operations.txt
   energy-agents-augmentation --edi --output outputs/augmentation_edi
   MPLBACKEND=Agg sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

The method ``energy_methods.bess_service_envelope.screen_bess_service`` was
inspected at EDI commit ``e72d9d822b442f6392c80ce12dfc62f738f51ddd`` and its source
hash matches the existing 0.1.1 wheel. The bounded adapter passes each cohort-aged
DC capacity with the stated SOC window and discharge efficiency. It checks
sustainable AC MW across all 120 plan/year/scenario rows; it does not validate
costs, ageing or contract performance. Metadata alone is not execution. EDI's
noncommercial licence requires appropriate rights for any commercial offering;
no upstream source is copied into this project.

The reviewed EDI merchant-finance module models trading contribution, not additions;
its PV degradation module is not a battery ageing model. The new module adds the
missing cohort and cost ledger while reusing the service-envelope capability.

Method and timing
----------------------------------------------------------------------------------------------------

For additions :math:`q_i` DC MWh at times :math:`t_i`, constant annual retention
:math:`r`, and an interval endpoint :math:`t`, remaining capacity is

.. math::

   E_{DC}(t) = \sum_{i:t_i<t} q_i r^{t-t_i}.

Available single-event AC energy is remaining DC capacity multiplied by
``(initial_soc - reserve_soc) * discharge_efficiency``. Sustainable MW is the
minimum of inverter MW and available AC MWh divided by four hours. A cohort added
at year five cannot satisfy the year-five condition immediately before that addition.

At each allowed installation time, size the smallest whole number of packs that
covers the **next interval's endpoint**, including the remaining older cohorts.
Old cohorts stay installed. Monotone assumed fade makes this endpoint the worst
capacity in the interval; this argument does not cover outages, variable SOC,
temperature, cycling or changing inverter limits. This is a fixed-schedule screen,
not global optimisation of addition dates. Site limits apply to total installed
DC nameplate, not merely the degraded remaining capacity.

Equipment and event costs are paid at each installation time, discounted by
:math:`(1+d)^{t_i}`. Capacity-based annual O&M is paid at year end and includes
only cohorts installed before that year's endpoint. The KPI is baseline present
cost minus staged present cost, **not project NPV**. The future-price multiplier
applies only to post-zero installed equipment costs; fixed event costs and O&M
remain unchanged. Its break-even value solves equal present cost with fixed cohorts.

Baseline assumptions and results
----------------------------------------------------------------------------------------------------

.. list-table:: Synthetic inputs
   :header-rows: 1

   * - Input
     - Assumption
   * - Target / inverter / duration / horizon
     - 20 MW / 20 MW / 4 h / 15 years
   * - Initial SOC / reserve / discharge efficiency
     - 100% / 10% / 95%; DC-to-AC factor 0.855
   * - Annual retention / pack / site DC limit
     - 98% / 1 MWh / 200 MWh
   * - Installed capacity cost
     - USD 180,000 per DC MWh, constant-real; no assumed price decline
   * - O&M / event cost / real discount rate
     - USD 1,500 per installed DC MWh/year / USD 250,000 per nonzero addition / 8%
   * - Scheduled additions
     - Years 0, 5 and 10, instant installation with compatible cohorts assumed

.. list-table:: Modelled capacity-cost results
   :header-rows: 1

   * - Plan
     - DC MWh additions
     - 15-year present cost, USD
   * - Upfront
     - 127 at year 0
     - 24,490,580.69
   * - Staged
     - 104 at year 0; 10 at year 5; 10 at year 10
     - 22,496,263.37

Both pass the narrowly defined base screen. Conditional reduction is
**USD 1,994,317.32**. Future installed equipment prices at **1.96868 times** the
base price erase this difference. At twice the price, staged cost is USD 64,480.71
higher; at four times it is USD 4,182,076.78 higher.

At **97% retention**, the original upfront design first fails in year 11 and the
staged design in year 4. Minimum sustainable powers are about 17.19 and 17.49 MW,
respectively. The system keeps those original cohorts fixed and returns **null**
comparative savings, rather than presenting a cheaper inadequate design as a benefit.
The point estimates are sensitivity cases, not probability distributions or forecasts.

Prompts, handoffs and boundaries
----------------------------------------------------------------------------------------------------

``src/energy_agents/data/augmentation/skill.json`` saves the actual user prompt,
role mandates, input schema, tool allowlist, evidence requirements, handoffs,
output contract and acceptance criteria. Evidence validation and deterministic
sizing precede the existing finance role through the existing orchestrator.
Finance recomputes the input-SHA256-bound physical handoff. Altered inputs or
results, premature calls and unregistered external actions fail closed.

The scripted workflow must equal the direct deterministic baseline. Neither is
an LLM run; LLM tokens, latency and monetary usage are unknown. An optional
caller-supplied orchestrator planner can route registered tasks, but it has no
authority to change assumptions, contact suppliers, submit bids, spend or control
assets. Independent human/engineering review remains required.

Common inverter, renewable generation, land and grid costs are excluded as shared
costs; no debt, tax, FX, residual value, disposal difference, energy purchases,
service revenue or penalty is valued. Capacity-variable installation and event
costs must be replaced by compatible supplier scope before a real comparison.
Recharge and repeated dispatch, augmentation outage, warranty/cycling/temperature
curves, site engineering, grid-forming and other tender duties remain evidence gaps.
