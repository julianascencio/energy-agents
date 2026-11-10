"""Scientific invariants, temporal leakage, independent optima and bounded tools."""

import json
from copy import deepcopy
from itertools import product

import pytest

np = pytest.importorskip("numpy")

from energy_agents.orchestrator import AgentTask, run_orchestrator  # noqa: E402
from energy_agents.quantum_ml import (  # noqa: E402
    ROLE,
    QuantumMLReplayPlanner,
    prepare_dataset,
    quantum_context,
    quantum_ml_runners,
    run_quantum_ml_agent,
    synthetic_load_case,
)
from energy_agents.quantum_ml.__main__ import main  # noqa: E402
from energy_agents.quantum_ml.agent import research_handoff  # noqa: E402
from energy_agents.quantum_ml.benchmark import benchmark_forecasts, metrics  # noqa: E402
from energy_agents.quantum_ml.inputs import load_csv, validate_case  # noqa: E402
from energy_agents.quantum_ml.models import (  # noqa: E402
    fidelity_kernel,
    fit_predict,
    product_features,
    quantum_states,
    statevector,
)
from energy_agents.quantum_ml.optimization import (  # noqa: E402
    anneal_schedule,
    build_schedule_qubo,
    exact_schedule,
    feasible,
    qaoa_schedule,
    schedule_cost,
)


@pytest.fixture(scope="module")
def case():
    return synthetic_load_case(days=12)


@pytest.fixture(scope="module")
def result(case):
    return run_quantum_ml_agent(case)


def test_role_covers_all_responsibilities_with_unique_skills():
    context = quantum_context()
    ids = {s["id"] for s in context["skills"]}
    assert len(ids) == len(context["skills"]) == 13
    assert context["role_id"] == ROLE.id
    for row in context["responsibility_coverage"]:
        assert set(row["skills"]) <= ids
    assert all(s["instructions"] and s["acceptance"] and s["mode"] for s in context["skills"])
    assert len(context["responsibility_coverage"]) == 10


def test_seed_reproduction_and_feature_availability(case):
    assert case == synthetic_load_case(days=12)
    assert case != synthetic_load_case(days=12, seed=18)
    data = prepare_dataset(case)
    assert data["train_end"] % 24 == data["validation_end"] % 24 == 0
    for feature, origin, target in zip(data["latest_feature_timestamps"],
                                       data["forecast_origins"], data["timestamps"]):
        assert feature < origin <= target
    np.testing.assert_array_equal(data["x"][:, 0], data["persistence"])
    assert data["timestamps"][data["train_end"] - 1] < data["forecast_origins"][data["train_end"]]


@pytest.mark.parametrize("mutate", [
    lambda c: c.update(unit="kW"),
    lambda c: c.update(classification="verified"),
    lambda c: c["provenance"].update(license=""),
    lambda c: c["records"].pop(),
    lambda c: c["records"][3].update(load_mw=float("nan")),
    lambda c: c["records"][3].update(load_mw=float("inf")),
    lambda c: c["records"][3].update(load_mw=-1),
    lambda c: c["records"][3].update(load_mw=True),
    lambda c: c["records"][3].update(timestamp=c["records"][2]["timestamp"]),
    lambda c: c["records"][3].update(timestamp="2026-01-01T03:00:00"),
    lambda c: c["records"][3].update(timestamp="2026-01-01T03:00:00+01:00"),
])
def test_data_failures_are_explicit(case, mutate):
    broken = deepcopy(case)
    mutate(broken)
    with pytest.raises(ValueError):
        validate_case(broken)


def test_csv_preserves_observed_label_hash_and_zero(case, tmp_path):
    path = tmp_path / "load.csv"
    rows = deepcopy(case["records"])
    rows[2]["load_mw"] = 0
    path.write_text("timestamp,load_mw\n" + "\n".join(
        f"{r['timestamp']},{r['load_mw']}" for r in rows))
    observed = load_csv(path, source="user-owned-meter", license="authorized", description="UTC load")
    assert observed["classification"] == "observed"
    assert observed["records"][2]["load_mw"] == 0
    assert len(observed["provenance"]["source_sha256"]) == 64
    path.write_text("timestamp,load_kw\nnow,10")
    with pytest.raises(ValueError, match="header"):
        load_csv(path, source="meter", license="authorized", description="wrong units")


def test_circuit_normalization_analytic_one_qubit_and_kernel_psd():
    np.testing.assert_allclose(statevector(np.zeros(4)), np.eye(16)[0])
    angle = 0.7
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    phase = angle**2 / 2
    # Independent analytic RY(a) RZ(a^2) RY(a)|0> for one wire.
    expected = [c*c*np.exp(-1j*phase)-s*s*np.exp(1j*phase),
                s*c*(np.exp(-1j*phase)+np.exp(1j*phase))]
    np.testing.assert_allclose(statevector([angle]), expected)
    x = np.random.default_rng(11).uniform(-1, 1, (12, 4))
    states = quantum_states(x)
    np.testing.assert_allclose(np.sum(abs(states)**2, axis=1), 1, atol=1e-12)
    kernel = fidelity_kernel(states, states)
    np.testing.assert_allclose(kernel, kernel.T, atol=1e-12)
    np.testing.assert_allclose(kernel.diagonal(), 1, atol=1e-12)
    assert np.linalg.eigvalsh(kernel).min() >= -1e-10
    no_entanglement = quantum_states(x, entangle=False)
    assert not np.allclose(kernel, fidelity_kernel(no_entanglement, no_entanglement))
    np.testing.assert_allclose(np.sum(product_features(x)**2, axis=1), 1, atol=1e-12)


def test_metrics_and_constant_target_are_independent_of_heldout_scaling():
    assert metrics(np.array([0, 5, 7]), np.array([2, 5, 6]))["mae_mw"] == 1
    x = np.random.default_rng(1).normal(size=(12, 4))
    query = np.vstack([x[:2], [9999, -9999, 10, -10]])
    for name in ("ridge", "product_ridge", "rbf_kernel", "quantum_kernel"):
        np.testing.assert_allclose(fit_predict(name, x, np.ones(12)*3, query, alpha=0.1), 3)
        pred = fit_predict(name, x, x[:, 0], query, alpha=0.1)
        standalone = fit_predict(name, x, x[:, 0], query[:2], alpha=0.1)
        np.testing.assert_allclose(pred[:2], standalone)


def test_sealed_holdout_cannot_affect_hyperparameters_or_model_selection(case):
    data = prepare_dataset(case)
    original = benchmark_forecasts(data)
    modified = deepcopy(data)
    modified["y"][data["validation_end"]:] += 10000
    changed = benchmark_forecasts(modified)
    assert original["selected_model"] == changed["selected_model"]
    assert original["predictions_mw"] == changed["predictions_mw"]
    for before, after in zip(original["rows"], changed["rows"]):
        assert before["selected_config"] == after["selected_config"]
        assert before["validation_trials"] == after["validation_trials"]


@pytest.mark.parametrize("prices", [[10, 20, 30, 40], [-100, -50, 25, 80]])
def test_qubo_matches_direct_objective_for_every_feasible_state_and_excludes_invalid(prices):
    load = np.array([1, 2, 1.5, 0.5])
    p = build_schedule_qubo(load, prices)
    direct = []
    for bits in product((0, 1), repeat=8):
        b = np.array(bits)
        energy = float(b @ p["q"] @ b + p["offset"])
        if feasible(b):
            # independent cost in physical units, two distinct one-hour batches
            increment = b.reshape(2, 4).sum(axis=0) * 0.2
            euros = increment @ prices + 40 * np.sum(2 * load * increment + increment**2)
            assert energy == pytest.approx(euros, abs=1e-9)
            direct.append(euros)
    optimum = exact_schedule(p)
    assert optimum["feasible"] and optimum["feasible_states"] == 12
    assert optimum["qubo_energy"] == pytest.approx(min(direct), abs=1e-9)
    assert optimum["independent_feasible_objective"] == pytest.approx(min(direct), abs=1e-9)
    for solver in (anneal_schedule, qaoa_schedule):
        solution = solver(p)
        assert solution["feasible"]
        assert solution["qubo_energy"] >= min(direct) - 1e-9
        assert solution["qubo_energy"] == pytest.approx(schedule_cost(solution["bits"], p)["objective_eur"])
    qaoa = qaoa_schedule(p)
    assert 0 <= qaoa["feasible_probability"] <= 1
    assert 0 <= qaoa["feasible_sample_count"] <= qaoa["shots"]


def test_default_agent_runs_real_tools_and_never_claims_advantage(result):
    assert result["success"] and len(result["trace"]) == 5
    assert result["mode"] == "scripted_tool_workflow"
    assert not result["execution_authorized"]
    assert not result["reports"]["forecast"]["quantum_advantage_demonstrated"]
    assert not result["reports"]["forecast"]["resources"]["qpu_executed"]
    assert result["reports"]["optimization"]["forecast_regret_eur"] >= 0
    assert result["reports"]["handoff"]["business_result"]["realized_savings"] is False
    json.dumps(result, allow_nan=False)


def test_invalid_actions_bounded_repair_and_planner_cannot_mutate_inputs(case):
    original = deepcopy(case)

    class Repair:
        def next_action(self, context):
            if not context["history"]:
                return {"tool": "shell", "arguments": {"command": "never executed"}}
            action = QuantumMLReplayPlanner().next_action(context)
            context["input_summary"].clear()
            return action

    fixed = run_quantum_ml_agent(case, Repair())
    assert fixed["success"] and fixed["trace"][0]["status"] == "rejected"
    assert original == case
    assert not run_quantum_ml_agent(case, max_calls=1)["success"]

    class Bad:
        def next_action(self, context):
            return {"tool": "finish", "arguments": {}}

    bad = run_quantum_ml_agent(case, Bad(), max_calls=3)
    assert not bad["success"] and not bad["reports"] and len(bad["trace"]) == 3


def test_exception_keeps_failure_visible_without_exposing_provider_secrets(case, monkeypatch):
    class Broken:
        def next_action(self, context):
            raise RuntimeError("secret token")

    failed = run_quantum_ml_agent(case, Broken())
    assert not failed["success"] and "secret" not in json.dumps(failed)
    from energy_agents.quantum_ml import agent

    def broken_tool(*args, **kwargs):
        raise ImportError("missing optional backend")

    monkeypatch.setattr(agent, "benchmark_forecasts", broken_tool)
    failed = run_quantum_ml_agent(case, include_hybrid=True)
    assert not failed["success"] and failed["trace"][-1]["error_type"] == "ImportError"
    assert set(failed["reports"]) == {"data"}


def test_orchestrator_registration(case):
    routed = run_orchestrator([AgentTask("experiment", ROLE.id, payload=case)], quantum_ml_runners())
    assert routed["success"] and routed["results"]["experiment"]["success"]


def test_literature_refresh_flag_is_not_a_live_search(result):
    handoff = research_handoff(result["reports"]["forecast"], result["reports"]["optimization"],
                               as_of="2027-03-01")
    assert handoff["literature"]["refresh_due"]
    assert not handoff["literature"]["live_search_performed_by_agent"]


def test_exported_inputs_and_hash_manifest(tmp_path):
    import hashlib

    main(["--output", str(tmp_path)])
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for name, digest in manifest.items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    assert json.loads((tmp_path / "result.json").read_text())["success"]
