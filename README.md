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

Only the five PV roles are executable in this workflow; the wider renewable
lifecycle, other technologies and additional agent families are documented plans.

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
