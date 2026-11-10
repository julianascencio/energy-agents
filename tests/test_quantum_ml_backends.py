"""Optional independent-framework parity and genuine differentiable training."""

import pytest

np = pytest.importorskip("numpy")

from energy_agents.quantum_ml.backends import neural_predict, qiskit_statevector  # noqa: E402
from energy_agents.quantum_ml.models import statevector  # noqa: E402


@pytest.mark.parametrize("entangle", [True, False])
def test_numpy_circuit_matches_qiskit_independent_gate_engine(entangle):
    pytest.importorskip("qiskit")
    for n in (1, 2, 4, 6):
        for seed in (3, 13, 25):
            x = np.random.default_rng(seed).uniform(-np.pi, np.pi, n)
            np.testing.assert_allclose(statevector(x, entangle=entangle),
                                       qiskit_statevector(x, entangle=entangle), atol=1e-12)


def test_qaoa_distribution_matches_independent_qiskit_simulation():
    pytest.importorskip("qiskit")
    from itertools import product

    from qiskit import QuantumCircuit
    from qiskit.circuit.library import DiagonalGate
    from qiskit.quantum_info import Statevector

    from energy_agents.quantum_ml.optimization import build_schedule_qubo, feasible, qaoa_schedule

    p = build_schedule_qubo([1.0, 1.3, 1.2, 1.4], [50, 100, 80, 60])
    run = qaoa_schedule(p)
    bits = np.array(list(product((0, 1), repeat=8)))
    energies = np.einsum("bi,ij,bj->b", bits, p["q"], bits) + p["offset"]
    circuit = QuantumCircuit(8)
    circuit.h(range(8))
    circuit.append(DiagonalGate(np.exp(-1j * run["gamma"] * energies / p["penalty"])), range(8))
    circuit.rx(2 * run["beta"], range(8))
    probabilities = Statevector.from_instruction(circuit).probabilities()
    assert float(probabilities @ energies) == pytest.approx(run["expected_penalized_cost_eur"])
    mask = [feasible(b) for b in bits]
    assert float(probabilities[mask].sum()) == pytest.approx(run["feasible_probability"])


@pytest.mark.parametrize("kind", ["torch_mlp", "hybrid_qnn"])
def test_torch_and_pennylane_train_with_fixed_seed_and_preserve_global_rng(kind):
    torch = pytest.importorskip("torch")
    if kind == "hybrid_qnn":
        pytest.importorskip("pennylane")
    rng = np.random.default_rng(2)
    x = rng.normal(size=(32, 4))
    y = 2 + 0.2 * x[:, 0] - 0.1 * x[:, 1]
    before = torch.random.get_rng_state().clone()
    run = neural_predict(kind, x, y, x[:4], epochs=20, seed=7)
    assert torch.equal(before, torch.random.get_rng_state())
    again = neural_predict(kind, x, y, x[:4], epochs=20, seed=7)
    np.testing.assert_allclose(run["prediction"], again["prediction"])
    assert np.isfinite(run["prediction"]).all()
    assert run["loss_curve"][-1] < run["loss_curve"][0]
    assert run["trainable_parameters"] > 0 and len(run["loss_curve"]) == 20
    assert run["shots"] is None
