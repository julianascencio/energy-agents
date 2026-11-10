Quantum Machine Learning Engineer
======================================================================

The generic ``career_quantum_ml_engineer`` covers quantum and quantum-inspired
time-series analysis, optimization, data preparation, classical and hybrid model
implementation, hyperparameter tuning, research review, technology transfer and
multidisciplinary handoffs. No employer identity or job-description text is
redistributed. Human degrees and experience are not agent credentials.

There are two entry points: the existing career-role runner creates advisory work
plans, while ``run_quantum_ml_agent`` executes the numerical experiment described
here. Its default planner is scripted. An optional live LLM may request stages,
but cannot invent scores or replace the tools' outputs.

Install and reproduce
----------------------------------------------------------------------

.. code-block:: bash

   python -m pip install -e ".[dev,quantum,docs]"
   energy-agents-qml --output outputs/quantum_ml
   python examples/quantum_ml/plot_quantum_ml_engineer.py
   python -m pytest tests/test_quantum_ml.py

To execute the additional classical MLP and hybrid quantum neural training:

.. code-block:: bash

   # CPU-only Torch avoids downloading CUDA libraries for this small experiment.
   python -m pip install 'torch>=2.6,<3' --index-url https://download.pytorch.org/whl/cpu
   python -m pip install -e ".[dev,quantum-hybrid]"
   energy-agents-qml --hybrid --output outputs/quantum_ml_hybrid
   python -m pytest tests/test_quantum_ml_backends.py

Optionally retrieve recent research metadata with one bounded arXiv query:

.. code-block:: bash

   energy-agents-qml --refresh-literature --output outputs/quantum_ml_recent

This explicitly enables network access, a 20-second timeout and at most ten
results sorted by submission date. The connector records title, authors, article
dates, retrieval timestamp and response hash. It does not copy abstracts or papers,
verify peer review, or turn source metadata into validated findings. Avoid repeated
requests within three seconds. Failed retrieval leaves the run unsuccessful with
the completed numerical reports preserved; default runs remain fully offline.

The optional backend CI job executes both Qiskit parity tests and the full hybrid
example. The default gallery uses NumPy only, plus Matplotlib for figures. Missing
optional dependencies fail a requested hybrid run, with a preserved failure trace.

Exports include ``input.json``, ``result.json``, ``research_context.json``,
``environment.json`` and a SHA256 ``manifest.json``. Numerical outputs are seeded;
wall-clock timings and environment versions naturally vary between machines.

.. code-block:: python

   from energy_agents.quantum_ml import run_quantum_ml_agent, synthetic_load_case

   result = run_quantum_ml_agent(synthetic_load_case())
   assert result["success"]
   print(result["reports"]["forecast"]["rows"])
   print(result["reports"]["optimization"]["ex_post_costs"])
   print(result["reports"]["handoff"])

Responsibility and skill coverage
----------------------------------------------------------------------

The versioned machine-readable contract is
``src/energy_agents/data/quantum_ml/skills.json``. Each skill records its
instructions, execution mode, tools and acceptance checks.

.. list-table:: Coverage and implementation boundaries
   :header-rows: 1
   :widths: 30 45 25

   * - Responsibility
     - Skills and tools
     - Status
   * - Quantum and quantum-inspired forecasting
     - Fidelity-kernel ridge, product-feature ridge, entanglement ablation
     - Executable local simulation
   * - Classical and hybrid AI
     - Persistence, ridge, RBF; PyTorch MLP and PennyLane QNode/readout
     - Executable; neural models optional
   * - Quantum/hybrid optimization
     - QUBO derivation, exact reference, annealing, p=1 QAOA
     - Executable local simulation
   * - Real and synthetic data
     - Seeded generation, observed CSV, provenance, units, UTC, missing-data checks
     - Executable; real-data source supplied by caller
   * - Training and hyperparameters
     - Fixed grids, Adam, fixed seed ensemble, chronological model selection
     - Executable bounded experiment
   * - New methodology and current research
     - Problem framing, primary-reference ledger, review age and ablation protocol
     - Curated context, optional arXiv metadata retrieval and review proposal
   * - Applied research and transfer
     - Scheduling economics, regret, prospective pilot gates
     - Computed scenario and review handoff
   * - Multidisciplinary collaboration
     - Orchestrator registration; code, commercial and plant review assignments
     - Explicit handoffs, no external messages
   * - Additional scientific safeguards
     - Leakage checks, independent circuit/solver tests, resource accounting, shot diagnostic
     - Executable with documented limits

Forecasting protocol
----------------------------------------------------------------------

The default dataset has 432 hourly synthetic demand values in MW. Remove the
first 48 hours to construct lag-24, lag-48, sine-hour and cosine-hour features.
Split the remaining 384 targets into 192 training, 96 validation and 96 test
samples, all on midnight UTC boundaries. Each day's 24 predictions use only
measurements available at that day's midnight; later test days may use earlier
test observations as lag features. This is rolling daily issuance with a frozen
model, not a forecast of the entire holdout from its first midnight. Zero
telemetry delay is assumed and must be replaced for a real deployment.

Fit standardization on training samples, choose configurations by validation MAE,
then refit on training plus validation. Freeze the downstream model choice before
scoring test targets. The test winner can differ from the validation winner.
All models report MAE, RMSE and signed bias in MW, absolute hourly energy-error
sum in MWh, and paired daily errors. Error energy is not energy actually purchased.
Demand predictions are clipped at zero for every learned model.

* Ridge and product-feature ridge use three regularization values.
* RBF kernel ridge uses three regularizers and two bandwidths (six trials).
* Quantum kernels use three regularizers and four qubits. The feature map is RY
  encoding, a CNOT chain, data-dependent RZ rotations and RY re-upload. The
  no-entanglement ablation removes only the CNOT chain.
* The product-feature model uses explicit sine/cosine tensor products and a
  classical ridge readout. It is quantum-inspired but is neither a quantum circuit
  execution nor a compressed tensor-train optimizer.
* Optional neural models use two learning rates, 40 full-batch Adam epochs and
  an ensemble of seeds 7 and 19. The hybrid has two layers of trainable RY gates
  and CNOTs, Pauli-Z measurements and a linear PyTorch readout. The classical MLP
  uses one eight-unit hidden layer. Their capacities are not matched; report the
  parameter counts instead of claiming a controlled scaling comparison.

The kernel is :math:`K_{ij}=|\langle\psi(x_i)|\psi(x_j)\rangle|^2`.
Training kernels are centered, as are out-of-sample rows using training column
means. A positive regularizer permits a stable dense solve even if a kernel is
rank deficient. All computation is classical simulation. Statevector memory grows
as :math:`2^q`; Gram memory grows as :math:`n^2`; dense fitting as :math:`n^3`.
The 12..32-day input limit bounds this research runner's cost.

The fidelity diagnostic samples independent binomial overlaps at 128 and 1,024
shots. It does not train a noisy kernel model, ensure a sampled Gram matrix is
positive semidefinite, emulate decoherence or measure quantum-device performance.
Daily error differences are descriptive; four test days are not sufficient for a
generalizable or statistically persuasive quantum advantage claim.

Forecast-informed scheduling
----------------------------------------------------------------------

For hours 08:00..11:00 of the first holdout day, two one-hour batches each consume
0.2 MW and choose distinct slots. The eight bits encode job-by-slot decisions.
Prices of 100, 75, 85 and 110 EUR/MWh and a stress weight of 40 EUR/MW² are
**synthetic assumptions**, even when the load CSV contains observations.

For slot load :math:`L_t`, batch power :math:`P`, slot occupation :math:`n_t`
and one-hour intervals, the incremental objective is:

.. math::

   C(x)=\sum_t p_t P n_t + w\left[(L_t+P n_t)^2-L_t^2\right].

The squared-load term is a scenario stress proxy, not a utility demand tariff.
The QUBO adds one-hot penalties for each job and overlap penalties for each slot.
Its penalty exceeds the objective's absolute range. The exported upper-triangular
matrix uses :math:`x^TQx+\mathrm{offset}`; do not symmetrize it by doubling entries.
All 256 bitstrings are checked against an independent constrained objective.

Three seeded classical annealing runs and a p=1 QAOA simulation compare with the
exact optimum. QAOA starts at :math:`|+\rangle^8`, applies the diagonal cost phase
scaled by the penalty, then single-qubit X mixers. A predeclared 12-by-12
gamma/beta grid minimizes expected penalized energy. It samples 2,048 outcomes
and reports the best feasible sampled solution, feasibility probability and gap.
This best-sample statistic differs from expected circuit cost; both are exported.
An optimal sampled result on eight bits demonstrates no computational advantage.

The executable decision uses the exact forecast-based schedule; heuristic and
QAOA results are research comparisons. Ex-post scoring uses the same actual load
for the fixed baseline, forecast schedule and perfect-foresight lower bound.
Reported objective reduction includes the assumed stress proxy. No realized
savings, grid constraints, battery behavior or plant dispatch are represented.

Observed data and integration
----------------------------------------------------------------------

Provide 12..32 complete days, starting at midnight, with an explicit UTC offset:

.. code-block:: text

   timestamp,load_mw
   2026-01-01T00:00:00+00:00,1.25
   2026-01-01T01:00:00+00:00,1.18

.. code-block:: bash

   energy-agents-qml --input-csv load.csv \
     --source 'authorized-meter-export' --license 'internal-use-authorized' \
     --description 'Hourly average demand, MW, UTC' --output outputs/observed_qml

Reject duplicates, gaps, NaNs, negatives and wrong units. Zero is a valid measured
value. Signed net-power/export data require a different contract. Provenance is
caller-declared and hashed, not independently verified. No production data is
bundled or downloaded. To use an Energy Data Insights connector, first inspect its
current capability manifest, then explicitly adapt the timestamp, unit and license
contract into this CSV. This contribution does not claim a direct EDI connector.

Orchestrator and optional live planner
----------------------------------------------------------------------

.. code-block:: python

   from energy_agents.orchestrator import AgentTask, run_orchestrator
   from energy_agents.quantum_ml import ROLE, quantum_ml_runners, synthetic_load_case

   tasks = [AgentTask("qml_study", ROLE.id, payload=synthetic_load_case())]
   result = run_orchestrator(tasks, quantum_ml_runners())
   assert result["success"]

Register ``quantum_ml_runners`` explicitly to execute the research workflow. The
generic ``career_runners`` registry continues to produce a work plan for this role.
This distinction prevents a generic advisory request from unexpectedly training
models. Failed runs remain failed and block dependent orchestrator tasks.

.. code-block:: python

   from energy_agents.quantum_ml import QuantumMLPlanner, run_quantum_ml_agent

   planner = QuantumMLPlanner(
       endpoint="https://your-provider.example/v1/chat/completions",
       model="your-model", api_key_env="ENERGY_AGENTS_API_KEY",
   )
   # Explicitly opt in to sending role metadata and workflow summaries:
   # result = run_quantum_ml_agent(synthetic_load_case(), planner)

The planner receives skills, sample count, classification and stage history, not
raw hourly loads. Only the next permitted tool with empty arguments is accepted.
The caller selects the backend and budget. Tools cannot execute arbitrary code,
fetch arbitrary URLs, submit quantum hardware jobs, dispatch equipment or publish.
Only the caller can enable the fixed arXiv metadata refresh stage.
Successful replay establishes execution and contracts, not live LLM quality.

Research context and transfer
----------------------------------------------------------------------

The handoff records a primary-reference ledger reviewed on 10 November 2026 and
flags review older than 90 days relative to ``as_of`` (today UTC by default).
Supply ``--as-of 2026-11-10`` to replay the original review date. There is no
scheduled literature watcher. New
methodology proposals require source retrieval, falsifiable hypotheses, classical
baselines and ablations before implementation or novelty claims.
The optional metadata refresh does not reset the curated references' full-review
age: discovering an article and scientifically reviewing it are separate steps.

* `Bowles, Ahmed and Schuld: QML benchmarking <https://arxiv.org/abs/2403.07059>`_
  motivates careful baselines and entanglement ablations; its results are not replicated here.
* `Stoudenmire and Schwab: quantum-inspired tensor networks <https://arxiv.org/abs/1605.05775>`_
  motivates local tensor-product features; no compressed MPS training is claimed.
* `Farhi, Goldstone and Gutmann: QAOA <https://arxiv.org/abs/1411.4028>`_
  supplies the alternating cost/mixer framework used in the small optimization illustration.
* `PennyLane's PyTorch interface <https://docs.pennylane.ai/en/stable/introduction/interfaces/torch.html>`_
  and `Qiskit Statevector <https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.Statevector>`_
  describe the implemented optional framework adapters.

Before technology transfer: collect licensed multi-season measurements, account
for telemetry delays, use rolling-origin/site-separated validation, improve
classical baselines, test hardware/noise budgets, calibrate production constraints
and measure value prospectively. The agent assigns these reviews to engineering,
commercial and plant roles; it neither performs human collaboration nor confers
academic qualifications.

API
----------------------------------------------------------------------

.. automodule:: energy_agents.quantum_ml.agent
   :members:

.. automodule:: energy_agents.quantum_ml.inputs
   :members:

.. automodule:: energy_agents.quantum_ml.benchmark
   :members:

.. automodule:: energy_agents.quantum_ml.models
   :members:

.. automodule:: energy_agents.quantum_ml.backends
   :members:

.. automodule:: energy_agents.quantum_ml.optimization
   :members:

.. automodule:: energy_agents.quantum_ml.literature
   :members:
