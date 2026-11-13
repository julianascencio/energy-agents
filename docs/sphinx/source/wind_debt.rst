Wind debt capacity and facility evidence
====================================================================================================

The 11 November 2026 `RWE announcement <https://www.rwe.com/en/press/rwe-ag/2026-11-11-rwe-and-kkr-join-forces-to-deliver-2-8-gw-of-new-offshore-wind-capacity-in-the-uk/>`_
reports financial close for 2.8 GW of offshore wind, GBP 11.1bn cash facilities
and GBP 1.7bn ancillary facilities. These are commitments, not evidence of drawn
debt. The reported 20-year CfD strike is GBP 91.20/MWh in 2024 prices.
The example uses that number only as a constant-real energy-value proxy.
It does not implement CfD settlement or estimate actual borrower leverage.

Business decision
----------------------------------------------------------------------------------------------------

A developer's finance analyst or lender can purchase a financing-readiness review:
check whether proposed borrowing survives a lower-generation scenario, and identify
the debt reduction needed before detailed diligence. No willingness-to-pay or
realised commercial revenue is measured. Baseline: proposed GBP 6.5bn borrowing.
Intervention: reduce borrowing to meet an assumed 1.3 debt-service coverage ratio
in the downside. This is a financing constraint, not a claim that less debt creates
project value. Any replacement equity, reduced project scope and financing costs
require separate review.

Model and assumptions
----------------------------------------------------------------------------------------------------

All financial results are synthetic. Net capacity factors are 50% and 40%;
annual operating expense is GBP 250m; interest is 5% real; horizon is 20 operating
years. Energy equals MW times 8,760 times net capacity factor. The net factor
already includes losses and availability. Revenue minus OPEX is a simplified
pre-tax cash-available-for-debt-service (CFADS) proxy.

Let A be the sum of annual discount factors at the real borrowing rate.
Level annual debt service equals proposed debt divided by A; DSCR equals
CFADS divided by debt service. Supported debt equals max(0, CFADS / minimum
DSCR) times A. Debt reduction equals max(0, proposed debt minus supported debt).
Zero interest is supported. Negative CFADS yields negative coverage and zero
supported debt. This model assumes level real service, not fixed nominal service.

Excludes construction timing/interest, taxes, reserves, fees, indexation mismatch,
price/volume settlement, curtailment clauses, transmission disposal, repayments
sculpted to varying cash flows and merchant revenues after the model horizon.
No probability is attached to either resource scenario. Actual finance approval
requires lender terms, an independent resource assessment and a complete model.

Workflow, permissions and evidence
----------------------------------------------------------------------------------------------------

The existing finance role and orchestrator execute evidence then finance tasks.
The evidence gate checks schema and classifications, not the truth of a source.
The finance task consumes isolated upstream input; invalid evidence blocks it.
The saved user request, mandate, schema, tool permissions, handoffs and acceptance
criteria are in ``data/debt/skill.json``. No arbitrary tools, third-party messages,
trades, contracts or physical controls are available. A human must review results.

The bounded ``edi_context`` adapter returns a two-file source-derived EDI catalogue
at commit ``72f62cf25c07ad9fab4565e8f9babfbf7af49082``, with SHA-256 hashes and
public symbols. Wind inventory validation and offshore economics were inspected.
The latter is an unlevered real-JPY LCOE method without debt modelling; relabelling
its units as GBP would be inappropriate. No EDI numerical method is executed by
this case, and the metadata adapter does not claim execution. No external package
is needed for the offline screen.

Reproduce and evaluate
----------------------------------------------------------------------------------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs,quantum]'
   energy-agents-debt --output outputs/wind_debt
   energy-agents-debt --case my_case.json --output outputs/my_debt_case
   python examples/business/plot_wind_debt.py
   python -m pytest tests/test_debt.py

The CLI saves inputs, input hash, workflow trace, results and EDI context.
The gallery shows coverage and interest/resource sensitivity. Direct deterministic
calculation equals the scripted workflow. No live LLM was run; cost, tokens and
provider latency are unknown. No superiority claim is made. This is an advisory
prototype, not field validation or actual project finance advice.
