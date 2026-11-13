# Energy Agents

<p align="center">
  <a href="https://asvaconsulting.com"><img src="https://asvaconsulting.com/wp-content/uploads/2022/05/ASVA-1-1-scaled.jpg" alt="ASVA Consulting" width="280" /></a>
</p>
<p align="center"><strong>Created by ASVA Consulting</strong><br>
<a href="https://asvaconsulting.com">asvaconsulting.com</a> ·
<a href="mailto:contacto@asvaconsulting.com">contacto@asvaconsulting.com</a></p>

Evidence-backed **LLM agents and agentic engineering for energy systems**.
Reusable inputs, connectors, domain methods, bounded agent workflows and runnable analyses.

[Documentation](https://julianascencio.github.io/energy-agents/) ·
[Example gallery](https://julianascencio.github.io/energy-agents/gallery/index.html) ·
[First paper](docs/literature/01_building_energy_agents.md)

Documentation links become live after merging and enabling GitHub Pages with the
**GitHub Actions** source. PR documentation builds are available as workflow artifacts.

## Operations and asset management

Ask **where the portfolio is losing money, which evidence is missing and what
the team should investigate first**. A shared Python/CLI/MCP service connects the
five PV operations roles to executable methods in **Energy Data Insights**.
It produces a filterable HTML portfolio report, economically ranked repair
investigations, evidence-linked work-order drafts and reproducible JSON exports.

```bash
# Python 3.12+; install from this checkout
python -m pip install -e ".[dev,docs,mcp]"
python -m pip install -r requirements/operations.txt
energy-agents-ops --output outputs/operations
energy-agents-ops-mcp  # local stdio MCP server; default synthetic portfolio
```

Open `outputs/operations/report.html`, or run with `--input portfolio.json`.
The four-site example is synthetic. Calculations execute in EDI; the default role
workflow is scripted, while an MCP host can use the tools conversationally.
Recovery values are conditional scenarios. Incomplete data blocks economic
ranking; currencies and periods stay separate. Drafts do not dispatch work.

- [Product architecture, setup, real-data contract and roadmap](docs/sphinx/source/asset_management.rst)
- [Interactive portfolio demo](https://julianascencio.github.io/energy-agents/_static/operations/report.html) (after merge and Pages deployment)
- [Runnable gallery example](examples/operations/plot_asset_management.py)

### Real CEN Chile case

Run the same operations interface with **downloaded CEN Chile observations**:

```bash
energy-agents-cen --output outputs/cen_chile
energy-agents-ops-mcp --input outputs/cen_chile/input.json
```

The preserved 2–8 November 2026 case covers 84 source PV names and 583 comparable
plant-days: 296.34 GWh actual against 322.69 GWh scheduled. It separates schedule
investigations from CEN availability notices, flags Huatacondo's reported 0%
availability despite zero scheduled generation, and holds incomplete records out
of the full-window ranking. Schedule gaps are not assumed to be recoverable losses;
financial values remain unknown. Replay needs no network or credentials.

- [Sources, live retrieval, results and MCP usage](docs/sphinx/source/cen_chile_operations.rst)
- [Runnable real-data gallery](examples/operations/plot_cen_chile_operations.py)
- [Searchable CEN report](https://julianascencio.github.io/energy-agents/_static/cen_chile/report.html) (after merge and Pages deployment)

## AI Forward-Deployed Engineer

Turn a customer energy problem into a staged **discovery, solution, evaluation
and rollout proposal**, with business KPIs, integration contracts, pilot gates,
cost/latency budgets, monitoring and rollback. The bounded workflow produces an
explicit implementation handoff for the Python/data-science/ML engineer.

```bash
python examples/delivery/plot_forward_deployed_engineer.py
```

The offline solar O&M copilot case is synthetic and scripted. Accepted plans are
structurally validated proposals, not deployed systems or verified business results.
See the [agent guide and live LLM setup](docs/sphinx/source/forward_deployed.rst).

## Professional role agents: PV operations

The first role team combines **Performance Engineer, Reliability Engineer,
Commercial Asset Manager, Maintenance Planner and Technical Asset Manager**.
A bounded coordinator shares one versioned plant case, enforces role tools and
handoffs, and checks evidence and accounting before accepting the result.

```bash
energy-agents-pv --output outputs/pv_operations
python examples/operations/plot_pv_role_team.py
```

```python
from energy_agents.pv import synthetic_pv_case, run_pv_workflow

result = run_pv_workflow(synthetic_pv_case())
assert result["success"]
print(result["reports"]["asset_summary"]["data"])
```

The offline case is **synthetic**, with deterministic/scripted planners. It compares
baseline, single-planner and five-role execution using identical tools. It reports
energy deficits, fault associations, conditional recovery value and proposed
inspections. Missing data and unresolved losses stay visible. No live LLM quality,
causal diagnosis, field validation or execution authority is claimed.

- [Lifecycle catalogue and agent architecture](docs/sphinx/source/professional_roles.rst)
- [PV workflow, evidence schema and optional LLM planner](docs/sphinx/source/pv_operations.rst)
- [Runnable gallery source](examples/operations/plot_pv_role_team.py)

This PV workflow executes these five roles. Public-career and data center
specialists have separate advisory runners; the wider renewable lifecycle
catalogue also includes roles still at the design stage.

## Public-career role agents

**53 generic agents cover 57 public role descriptions** reviewed through 10 November
2026. They span AI engineering and delivery, data and IoT platforms,
energy operations, sales, finance, IT, governance, marketing, strategy, HR and legal
support. Repeated procurement, FDE and translated support listings share agents.

Each role has its own mandate, responsibilities, required inputs, deliverables,
review checks, KPIs and handoffs. A neutral source index records coverage without
employer names, links, original posting IDs, or other identifying source metadata.

```bash
energy-agents-roles --list
energy-agents-roles --output outputs/career_roles
python examples/enterprise/plot_career_role_agents.py
```

The default run produces **scripted work plans**. An optional LLM adapter can
propose deliverables through the same bounded evidence-linked protocol. Structural
acceptance is not factual validation or completion of professional work.

- [Role guide, neutral source index and contracts](docs/sphinx/source/career_roles.rst)
- [Runnable gallery example](examples/enterprise/plot_career_role_agents.py)
- [Packaged role catalogue](src/energy_agents/data/career_roles/catalogue.json)

## Quantum Machine Learning Engineer

The generic **Quantum Machine Learning Engineer** has 13 versioned skills covering
classical, quantum-inspired and hybrid models, real/synthetic data, time-series
validation, training, hyperparameter search, quantum optimization, literature review
and technology-transfer handoffs.

```bash
python -m pip install -e ".[dev,quantum,docs]"
energy-agents-qml --output outputs/quantum_ml
python examples/quantum_ml/plot_quantum_ml_engineer.py

# Optional PennyLane/PyTorch training and Qiskit circuit checks
python -m pip install -e ".[quantum-hybrid]"
energy-agents-qml --hybrid --output outputs/quantum_ml_hybrid
```

The agent executes a **demand-forecasting → production-scheduling** research case:
six default forecasting models, two optional neural models, chronological model
selection, an eight-variable QUBO, exact optimization, classical annealing and
simulated QAOA. It exports input data, metrics, traces, research handoffs and hashes.
The default data and business assumptions are synthetic; observed CSV input is
supported. Quantum computation is simulated. No quantum advantage is claimed.

- [Full coverage, methods, real-data contract and live planner](docs/sphinx/source/quantum_ml.rst)
- [Runnable gallery source](examples/quantum_ml/plot_quantum_ml_engineer.py)
- [Versioned skills and primary research context](src/energy_agents/data/quantum_ml/skills.json)

## Python, data science and ML engineering agent

The **Principal Python, Data Science and ML Engineer** proposes reusable code,
independent tests and runnable examples for energy applications. Its engineering
contract follows Energy Data Insights conventions: typed scientific APIs, explicit
units and provenance, leakage-free ML evaluation, baseline comparisons and
reproducible analysis. A bounded loop validates proposal paths and Python syntax
and returns errors to the planner for repair.

```bash
python examples/engineering/plot_python_engineer.py
```

Use `PythonEngineeringPlanner` for an explicitly configured LLM provider or supply
your own `next_action` planner. The offline demo is scripted. The runner returns
unexecuted code proposals; tests, scientific validity and live LLM quality remain
separate checks. See the [agent guide](docs/sphinx/source/python_engineer.rst).

## First research example: building energy model edits

Shirzadi, Lopez & Stylianou (2026), *Tool-augmented vs. autonomous LLM agents for
building energy model modifications: A comparative study using NECB compliance
models*, Energy and AI 26, 100896. [DOI](https://doi.org/10.1016/j.egyai.2026.100896).

This first contribution implements the paper's **1.5 W/(m² K) window U-factor**
and **30% active lighting-design reduction** tasks on EnergyPlus epJSON objects.
It compares high-level domain tools with field-level edits, records each action,
checks exact postconditions, and rolls failed attempts back to the original model.

The offline example uses a **synthetic model fragment and scripted policies**.
It is runnable without API keys, EnergyPlus or network access. It is not a rerun
of the authors' experiment or evidence of LLM superiority. Published Table 8A
observations are shown separately, including documented inconsistencies with the
paper's narrative. No energy-savings or NECB-compliance claims are inferred.

## Orchestrator agent

Coordinate registered specialists through dependency-aware tasks, isolated handoffs,
bounded scheduling and explicit completed/failed/blocked/pending states. Use the
deterministic scheduler or an optional LLM prioritizer. The delivery-team adapter
connects the forward-deployed and Python/ML engineers when their modules are present.

```bash
python examples/orchestration/plot_orchestrator.py
```

See the [orchestrator guide](docs/sphinx/source/orchestrator.rst). Successful routing
is not independent validation, code execution or deployment authorization.

## Install and run

From this source checkout (not yet published to PyPI):

```bash
python -m pip install -e ".[dev,docs]"
python -m pip install -r requirements/operations.txt  # Python 3.12+ for operations/docs
energy-agents --output outputs/building_edits
python examples/buildings/plot_building_edits.py
```

The analysis writes the synthetic input, four edited-model/action-trace results,
published observations and a checksum manifest. Gallery scripts execute during docs builds.

```python
from energy_agents import run_agent
from energy_agents.inputs import synthetic_model

result = run_agent(synthetic_model(), task="lighting", surface="domain")
assert result["success"]
print(result["trace"])
```

An optional `ChatCompletionsPlanner` accepts an explicitly configured HTTPS endpoint,
model and environment-variable key for a real LLM run. See the user guide. HTTP
transport is covered by mocked tests; live provider behavior has not been validated.

## Repository map

| Location | Responsibility |
| --- | --- |
| `src/energy_agents/inputs.py` | Explicitly synthetic example inputs |
| `src/energy_agents/connectors.py` | Optional live LLM adapter |
| `src/energy_agents/methods.py` | Pure, transactional domain edits |
| `src/energy_agents/agents.py` | Tool surfaces, bounded orchestration and audit traces |
| `src/energy_agents/analysis.py` | Reproducible comparison and evidence exports |
| `analysis/building_edits/` | Command-line research runner |
| `examples/buildings/` | Executable Sphinx-Gallery example |
| `docs/literature/` | Paper, attribution and implementation scope |
| `tests/` | Preservation, rollback, input-validation and orchestration tests |

## Documentation and quality

Like OrbitalPV: **Sphinx + PyData Sphinx Theme + Sphinx-Gallery**, with installation,
user guide, public API, literature and a two-level gallery.

```bash
python -m pytest
ruff check .
python -m build
sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html
```

CI checks Python 3.11 and 3.12, builds the wheel, runs the offline analysis and builds
the gallery. The Pages workflow deploys on main after GitHub Pages is configured.

## Scope and next steps

Implemented: simple glazing and all three active Lights calculation methods,
domain/primitive action separation, exact edit validation, three-attempt cap,
per-attempt call budgets, deterministic exports, optional LLM planner.

Not implemented: the paper's full IDF/MCP/RAG stack, code-compliance validation,
annual EnergyPlus simulation, PTAC/DX-to-VRF conversion, or a seven-building live
LLM replication. epJSON input should be converted and validated with a matching
EnergyPlus version before use in a real simulation. The supplied fragment lacks
building geometry and is deliberately not simulation-ready.

Next: versioned EnergyPlus schema validation, real reference models and weather,
EnergyPlus execution, cited standards retrieval, MCP transport, repeated live-model
benchmarks, then topology-aware HVAC tools. Add solar, wind, BESS and grid domains
through the same input → tool → validation → analysis interfaces.

## AI-assisted development and literature basis

Created by **ASVA Consulting** with AI assistance. Developers select the literature;
implementation and documentation remain research work in progress. Tests establish
the specific software properties they check, not independent scientific validation.
Source observations, synthetic examples and measured live runs must remain separate.

Code: MIT. The included paper has its own CC BY attribution and is not relicensed.
See [literature notes](docs/literature/01_building_energy_agents.md).

## Industrial demand flexibility

Run `energy-agents-flex --output outputs/industrial_flexibility` for an advisory industrial energy manager example. It shifts fixed production batches around on-site solar, import limits and customer prices, accounting for lost export credits and rescheduling fees. Inputs are synthetic. See the [business case](docs/sphinx/source/industrial_flexibility.rst) and runnable demand-flexibility gallery.

## Wind commissioning business case

The Project Controls Engineer compares dependency-aware acceleration packages
against no action. The runnable synthetic example brings completion forward five
days and calculates expected contribution minus acceleration cost. Minimum test
durations and budget limits remain enforced; no realised revenue is claimed.

```bash
energy-agents-commissioning --output outputs/wind_commissioning
python examples/project_delivery/plot_wind_commissioning.py
```

See [method, evidence and prompts](docs/sphinx/source/commissioning_business.rst).

## News-driven BESS investment screening

The Project Finance Analyst now has a reusable revenue-concentration screening
skill inspired by Clean Horizon's 4 November 2026 analysis. Run:

```bash
energy-agents-bess --output outputs/bess_saturation
python examples/business/plot_bess_saturation.py
```

It compares flat and stressed revenue paths, NPV, upfront budget and discount-rate
sensitivity. Inputs distinguish published model outputs from illustrative scenarios.
Prompts, bounded tools and an optional read-only Energy Data Insights catalogue
adapter are included. No realised returns or live LLM advantage are claimed.
See [business case and reproduction](docs/sphinx/source/bess_business.rst).

### Data centre bridge-power business case

Run `energy-agents-bridge --output outputs/bridge_power` for the synthetic NTT/Bloom-news-inspired incremental investment screen. Reuses the finance role and orchestrator; compares against waiting and direct deterministic execution. See [methodology](docs/sphinx/source/bridge_power.rst) and [case history](docs/cases/2026-11-06-data-center-bridge-power.md).

### Residential battery reserve screen

Run `energy-agents-reserve --output outputs/reserve` to compare a reserve-limited grid-service offer against nameplate overcommitment. Uses recorded EDI physics, synthetic USD/event economics and the existing finance role. See [methodology](docs/sphinx/source/reserve_screen.rst) and [case history](docs/cases/2026-11-07-residential-battery-reserve.md).

## Data center design agents

The new **six-function campus team** covers design leadership, electrical/mechanical,
campus design, hall/site planning, facilities development and end-to-end delivery.
It reuses the fourteen specialists below and adds **Campus Design Engineer, Data
Hall and Site Planner, and Facilities Development Manager**. Generic roles are
inspired by the supplied team diagram; they do not impersonate employees.

```bash
energy-agents-campus --output outputs/campus_team
python examples/data_centers/plot_campus_team.py
```

The runnable synthetic case exposes a **2 MW grid gap and 20 missing rack slots**.
All seventeen roles have bounded advisory execution; delivery retains role-owned
evidence and capacity issues. See [role mapping, tools and workflow](docs/sphinx/source/campus_team.rst).
Default execution is scripted, with no live LLM or engineering approval claimed.

Fourteen specialists cover all six design-team groups in Brian Bakerman's
LinkedIn post, with telecoms and sustainability explicitly added. Each includes
a role contract, research context, evidence checklist and bounded advisory runner.
The existing orchestrator coordinates discipline reviews and handover.

```bash
energy-agents-design --output outputs/data_center_design
python examples/data_centers/plot_design_team.py
```

The synthetic 20 MW IT example identifies a 2 MW utility shortfall and missing
design evidence. Includes optional live LLM planners, without claiming live LLM
validation or automated engineering approval. See the
[role catalogue, literature and usage](docs/sphinx/source/data_center_design.rst).

### VPPA buyer basis risk

Run `energy-agents-vppa --output outputs/vppa` for an offline synthetic buyer settlement screen with equal-energy solar/wind alternatives, an unhedged baseline and basis sensitivities. See [methodology](docs/sphinx/source/vppa_basis.rst) and [case history](docs/cases/2026-11-07-vppa-basis-risk.md).

### Transformer manufacturing-slot reservation

Run `energy-agents-procurement --output outputs/procurement` to compare reservation
against waiting for project approval under joint delivery, site-readiness and
cancellation scenarios. Reuses Project Controls Engineer, Project Finance Analyst
and the orchestrator. Includes synthetic NPV, downside and fee-ceiling results,
versioned prompts and a runnable procurement gallery. See
[method and reproduction](docs/sphinx/source/transformer_procurement.rst) and
[case history](docs/cases/2026-11-08-transformer-procurement.md).

### Wind debt capacity

Run `energy-agents-debt` for a synthetic, evidence-gated debt-service coverage screen. It separates announced facilities from drawn debt and compares proposed borrowing with downside cash flow. See `docs/cases/2026-11-11-wind-debt.md` and the business gallery.
