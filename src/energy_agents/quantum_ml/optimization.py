"""Forecast-informed production scheduling: exact verification of a small QUBO."""

from itertools import product

import numpy as np

from .models import _single


def build_schedule_qubo(load_mw, prices_eur_mwh, *, power_mw: float = 0.2,
                        stress_eur_per_mw2: float = 40.0) -> dict:
    """Two one-hour batches, four slots, one batch per slot, eight binary variables.

    The operational objective is incremental energy cost plus a declared squared
    import-load stress proxy. The latter is NOT a regulated demand tariff. Positive
    penalties enforce one slot per job and no overlap; all states are independently
    checked for feasibility. Negative electricity prices are supported.
    """
    load, price = np.asarray(load_mw, dtype=float), np.asarray(prices_eur_mwh, dtype=float)
    if load.shape != (4,) or price.shape != (4,) or not np.isfinite([load, price]).all():
        raise ValueError("Supply four finite load and price values")
    if np.any(load < 0) or not np.isfinite(power_mw) or not 0 < power_mw <= 1e3:
        raise ValueError("Loads must be nonnegative and power in (0, 1000] MW")
    if not np.isfinite(stress_eur_per_mw2) or not 0 <= stress_eur_per_mw2 <= 1e6:
        raise ValueError("Stress weight must be in 0..1e6")
    q = np.zeros((8, 8))
    # Increment in stress: (L+P*n)^2-L^2, with n=x_job0+x_job1.
    linear = power_mw * price + stress_eur_per_mw2 * (2 * load * power_mw + power_mw**2)
    for job in range(2):
        for slot in range(4):
            q[job * 4 + slot, job * 4 + slot] = linear[slot]
    for slot in range(4):
        q[slot, 4 + slot] = 2 * stress_eur_per_mw2 * power_mw**2
    # More than the total absolute objective range: an infeasible state cannot win.
    penalty = 2 * float(np.abs(q).sum()) + 1.0
    for job in range(2):
        for slot in range(4):
            q[job * 4 + slot, job * 4 + slot] -= penalty
            for other in range(slot + 1, 4):
                q[job * 4 + slot, job * 4 + other] += 2 * penalty
    for slot in range(4):
        q[slot, 4 + slot] += penalty
    return {"q": q, "offset": 2 * penalty, "penalty": penalty, "load_mw": load,
            "prices_eur_mwh": price, "power_mw": power_mw,
            "stress_eur_per_mw2": stress_eur_per_mw2}


def feasible(bits) -> bool:
    bits = np.asarray(bits)
    if bits.shape != (8,) or not np.isin(bits, [0, 1]).all():
        return False
    matrix = bits.reshape(2, 4)
    return bool(np.all(matrix.sum(axis=1) == 1) and np.all(matrix.sum(axis=0) <= 1))


def schedule_cost(bits, problem: dict, *, load_mw=None) -> dict:
    """Evaluate a feasible schedule independently of its QUBO penalty algebra."""
    if not feasible(bits):
        raise ValueError("A schedule needs exactly one slot per job and no overlap")
    load = problem["load_mw"] if load_mw is None else np.asarray(load_mw, dtype=float)
    if load.shape != (4,) or not np.isfinite(load).all() or np.any(load < 0):
        raise ValueError("Evaluation loads must be four finite nonnegative values")
    energy = np.asarray(bits).reshape(2, 4).sum(axis=0) * problem["power_mw"]
    euros = float(energy @ problem["prices_eur_mwh"])
    stress = float(problem["stress_eur_per_mw2"] * np.sum((load + energy)**2 - load**2))
    return {"incremental_energy_eur": euros, "load_stress_proxy_eur": stress,
            "objective_eur": euros + stress, "flexible_energy_mwh": float(energy.sum())}


def exact_schedule(problem: dict) -> dict:
    """Enumerate all 256 bitstrings; return both penalized and constrained optima."""
    candidates = [np.array(bits) for bits in product((0, 1), repeat=8)]
    best = min(candidates, key=lambda b: float(b @ problem["q"] @ b + problem["offset"]))
    valid = [b for b in candidates if feasible(b)]
    reference = min(valid, key=lambda b: schedule_cost(b, problem)["objective_eur"])
    return {"bits": best.tolist(), "feasible": feasible(best),
            "qubo_energy": float(best @ problem["q"] @ best + problem["offset"]),
            "independent_feasible_objective": schedule_cost(reference, problem)["objective_eur"],
            "states_evaluated": len(candidates), "feasible_states": len(valid)}


def anneal_schedule(problem: dict, *, seed: int = 7, sweeps: int = 300) -> dict:
    """Bounded classical simulated annealing on a quantum-compatible QUBO.

    This Metropolis heuristic is classical; it is not quantum annealing or QAOA.
    Return best feasible visited state, explicitly reporting failure if none exists.
    """
    if type(sweeps) is not int or not 1 <= sweeps <= 10000:
        raise ValueError("sweeps must be in 1..10000")
    rng = np.random.default_rng(seed)
    q, offset = problem["q"], problem["offset"]
    bits = rng.integers(0, 2, 8)
    current = float(bits @ q @ bits + offset)
    best, best_cost = None, float("inf")
    if feasible(bits):
        best, best_cost = bits.copy(), current
    for temperature in np.geomspace(problem["penalty"], 0.01, sweeps):
        for _ in range(8):
            candidate = bits.copy()
            candidate[rng.integers(8)] ^= 1
            value = float(candidate @ q @ candidate + offset)
            if value < current or rng.random() < np.exp(min(0.0, (current - value) / temperature)):
                bits, current = candidate, value
            if feasible(bits) and current < best_cost:
                best, best_cost = bits.copy(), current
    return {"seed": seed, "bits": None if best is None else best.tolist(),
            "feasible": best is not None, "qubo_energy": best_cost if best is not None else None,
            "proposals": sweeps * 8, "method": "classical_simulated_annealing"}


def qaoa_schedule(problem: dict, *, seed: int = 23, shots: int = 2048) -> dict:
    """p=1 QAOA, classically grid-trained and sampled from an exact 8-qubit simulator.

    Exp(-i gamma H/penalty) followed by exp(-i beta sum X), starting at the uniform eight-qubit superposition.
    Parameters minimize expected penalized cost over a predeclared 12x12 grid.
    The reported schedule is the best feasible sampled bitstring, not the exact
    optimum substituted into the result. No hardware or noise model is implied.
    """
    if type(shots) is not int or not 1 <= shots <= 100000:
        raise ValueError("shots must be in 1..100000")
    states = np.array(list(product((0, 1), repeat=8)))
    energies = np.einsum("bi,ij,bj->b", states, problem["q"], states) + problem["offset"]
    normalized = energies / problem["penalty"]
    best = None
    for gamma in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        for beta in np.linspace(0, np.pi, 12, endpoint=False):
            vector = np.exp(-1j * gamma * normalized) / 16
            mixer = np.array([[np.cos(beta), -1j * np.sin(beta)],
                              [-1j * np.sin(beta), np.cos(beta)]])
            for wire in range(8):
                vector = _single(vector, mixer, wire, 8)
            probabilities = np.abs(vector)**2
            probabilities /= probabilities.sum()
            expectation = float(probabilities @ energies)
            if best is None or expectation < best[0]:
                best = (expectation, float(gamma), float(beta), probabilities)
    expectation, gamma, beta, probabilities = best
    valid_mask = np.array([feasible(bits) for bits in states])
    sampled = np.random.default_rng(seed).choice(256, size=shots, p=probabilities)
    feasible_samples = [index for index in sampled if valid_mask[index]]
    winner = min(feasible_samples, key=lambda index: energies[index]) if feasible_samples else None
    return {"method": "qaoa_p1_numpy_statevector", "qubits": 8, "layers": 1,
            "training_grid_evaluations": 144, "gamma": gamma, "beta": beta,
            "expected_penalized_cost_eur": expectation,
            "feasible_probability": float(probabilities[valid_mask].sum()),
            "feasible_sample_count": len(feasible_samples), "shots": shots, "seed": seed,
            "bits": None if winner is None else states[winner].tolist(),
            "feasible": winner is not None,
            "qubo_energy": None if winner is None else float(energies[winner]),
            "quantum_hardware_executed": False}


def benchmark_schedule(forecasts: dict) -> dict:
    """Use a validation-selected forecast for hours 08..11 of the first holdout day.

    Perfect foresight is an ex-post lower bound, never an available decision input.
    The synthetic prices and production assumptions are declared even for real load.
    """
    window = slice(8, 12)
    model = forecasts["selected_model"]
    prediction = np.array(forecasts["predictions_mw"][model])[window]
    actual = np.array(forecasts["actual_mw"])[window]
    price = [100.0, 75.0, 85.0, 110.0]
    problem = build_schedule_qubo(prediction, price)
    exact = exact_schedule(problem)
    baseline = [1, 0, 0, 0, 0, 0, 0, 1]  # jobs at 08:00 and 11:00, fixed in advance
    oracle_problem = build_schedule_qubo(actual, price)
    oracle = exact_schedule(oracle_problem)
    heuristic = [anneal_schedule(problem, seed=seed) for seed in (7, 19, 31)]
    qaoa = qaoa_schedule(problem)
    qaoa["optimality_gap_eur"] = (max(0.0, qaoa["qubo_energy"] - exact["qubo_energy"])
                                  if qaoa["feasible"] else None)
    for run in heuristic:
        run["optimality_gap_eur"] = (max(0.0, run["qubo_energy"] - exact["qubo_energy"])
                                     if run["feasible"] else None)
    costs = {"fixed_baseline": schedule_cost(baseline, problem, load_mw=actual),
             "forecast_schedule": schedule_cost(exact["bits"], problem, load_mw=actual),
             "perfect_foresight": schedule_cost(oracle["bits"], oracle_problem)}
    return {"classification": "scenario_economics_even_when_load_is_observed",
            "selected_forecast_model": model, "forecast_origin": forecasts["forecast_origins"][8],
            "timestamps": forecasts["test_timestamps"][window],
            "forecast_mw": prediction.tolist(), "actual_mw": actual.tolist(),
            "prices_eur_mwh": price, "batch_power_mw": problem["power_mw"],
            "batch_duration_hours": 1, "stress_eur_per_mw2": problem["stress_eur_per_mw2"],
            "qubo": {"matrix": problem["q"].tolist(), "offset": problem["offset"],
                     "penalty": problem["penalty"], "convention": "upper_triangular x.T @ Q @ x"},
            "exact": exact, "annealing_runs": heuristic, "qaoa": qaoa, "baseline_bits": baseline,
            "oracle_bits": oracle["bits"], "ex_post_costs": costs,
            "scenario_objective_reduction_eur": costs["fixed_baseline"]["objective_eur"]
            - costs["forecast_schedule"]["objective_eur"],
            "forecast_regret_eur": max(0.0, costs["forecast_schedule"]["objective_eur"]
                                       - costs["perfect_foresight"]["objective_eur"]),
            "limitations": ["Stress is a quadratic scenario proxy, not a utility demand charge.",
                            "No grid connection limit, battery physics or production dynamics.",
                            "No dispatch, market order or realized savings.",
                            "Eight-bit enumeration is an audit reference, not a scalable solver."]}
