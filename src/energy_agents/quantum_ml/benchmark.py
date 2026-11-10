"""Chronological model selection, sealed holdout evaluation and resource accounting."""

from time import perf_counter

import numpy as np

from .backends import neural_predict
from .models import fit_predict, shot_diagnostic

FAMILIES = {
    "seasonal_persistence": "classical",
    "ridge": "classical",
    "rbf_kernel": "classical",
    "product_ridge": "quantum_inspired_classical",
    "quantum_kernel": "quantum_circuit_classically_simulated",
    "quantum_no_entanglement": "quantum_circuit_ablation_classically_simulated",
    "torch_mlp": "classical_neural",
    "hybrid_qnn": "hybrid_quantum_classical_simulator",
}


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Aligned hourly MW errors; summed absolute MWh is not purchased energy."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    if (actual.shape != predicted.shape or actual.ndim != 1 or not len(actual)
            or not np.isfinite(actual).all() or not np.isfinite(predicted).all()):
        raise ValueError("Metrics require finite, equally sized, nonempty 1D arrays")
    error = predicted - actual
    return {"mae_mw": float(np.mean(np.abs(error))),
            "rmse_mw": float(np.sqrt(np.mean(error**2))),
            "bias_mw": float(np.mean(error)),
            "absolute_error_mwh": float(np.sum(np.abs(error)))}


def _predict(name, config, x, y, query):
    if name in {"torch_mlp", "hybrid_qnn"}:
        # Average fixed seeds, never select a seed on the holdout.
        runs = [neural_predict(name, x, y, query, seed=seed, **config) for seed in (7, 19)]
        prediction = np.mean([r.pop("prediction") for r in runs], axis=0)
        return prediction, {"seed_runs": runs, "ensemble_seeds": [7, 19]}
    return fit_predict(name, x, y, query, **config), {}


def benchmark_forecasts(dataset: dict, *, include_hybrid: bool = False) -> dict:
    """Tune on one chronological validation block; refit once, then score holdout.

    This is a bounded screening benchmark, not rolling cross-validation, an
    exhaustive model search or statistically independent multi-site validation.
    """
    x, y = dataset["x"], dataset["y"]
    n, m = dataset["train_end"], dataset["validation_end"]
    rows = []
    names = list(FAMILIES) if include_hybrid else list(FAMILIES)[:-2]
    predictions = {}
    for name in names:
        start = perf_counter()
        trials, detail = [], {}
        if name == "seasonal_persistence":
            val = dataset["persistence"][n:m]
            prediction = dataset["persistence"][m:]
            selected = {}
            validation_mae = metrics(y[n:m], val)["mae_mw"]
        else:
            configs = [{"alpha": alpha} for alpha in (0.01, 0.1, 1.0)]
            if name == "rbf_kernel":
                configs = [{"alpha": alpha, "gamma": gamma}
                           for alpha in (0.01, 0.1, 1.0) for gamma in (0.1, 1.0)]
            if name in {"torch_mlp", "hybrid_qnn"}:
                configs = [{"learning_rate": rate, "epochs": 40} for rate in (0.01, 0.03)]
            for config in configs:
                val, _ = _predict(name, config, x[:n], y[:n], x[n:m])
                val = np.maximum(val, 0)  # physical nonnegative-demand constraint, all models
                trials.append({"config": config, "mae_mw": metrics(y[n:m], val)["mae_mw"]})
            best = min(trials, key=lambda t: t["mae_mw"])
            selected, validation_mae = best["config"], best["mae_mw"]
            prediction, detail = _predict(name, selected, x[:m], y[:m], x[m:])
            prediction = np.maximum(prediction, 0)
        predictions[name] = prediction.tolist()
        day_mae = np.abs(prediction - y[m:]).reshape(-1, 24).mean(axis=1)
        rows.append({"model": name, "family": FAMILIES[name], "selected_config": selected,
                     "validation_mae_mw": validation_mae, "validation_trials": trials,
                     "test": metrics(y[m:], prediction), "test_daily_mae_mw": day_mae.tolist(),
                     "elapsed_seconds": perf_counter() - start, "training_detail": detail})
    # The downstream decision never selects a model using holdout accuracy or cost.
    winner = min(rows, key=lambda row: row["validation_mae_mw"])["model"]
    test_stamps = dataset["timestamps"][m:]
    baseline = next(row for row in rows if row["model"] == "seasonal_persistence")
    for row in rows:
        row["paired_daily_mae_delta_vs_persistence_mw"] = (
            np.array(row["test_daily_mae_mw"]) - baseline["test_daily_mae_mw"]).tolist()
    mean, scale = x[:m].mean(axis=0), np.maximum(x[:m].std(axis=0), 1e-12)
    return {
        "split": {"train_samples": n, "validation_samples": m - n,
                  "test_samples": len(y) - m, "train_last_target": dataset["timestamps"][n - 1],
                  "validation_first_origin": dataset["forecast_origins"][n],
                  "validation_last_target": dataset["timestamps"][m - 1],
                  "test_first_origin": dataset["forecast_origins"][m]},
        "rows": rows, "selected_model": winner, "selection_metric": "validation_mae_mw",
        "predictions_mw": predictions, "actual_mw": y[m:].tolist(),
        "test_timestamps": test_stamps, "forecast_origins": dataset["forecast_origins"][m:],
        "latest_feature_timestamps": dataset["latest_feature_timestamps"][m:],
        "resources": {"qubits": 4, "amplitudes_per_state": 16,
                      "statevector_bytes_complex128": 256, "feature_map_gates": 15,
                      "train_gram_entries": m * m, "train_gram_bytes_float64": m * m * 8,
                      "test_kernel_entries": (len(y) - m) * m,
                      "circuit_backend": "numpy_exact_statevector", "qpu_executed": False,
                      "hardware_shots": 0,
                      "scaling": "statevector O(2^q); Gram memory O(n^2); dense solve O(n^3)",
                      "timing_scope": "per-model preprocessing, tuning, refit and test prediction"},
        "shot_diagnostic": shot_diagnostic(np.arctan((x[m:] - mean) / scale)),
        "quantum_advantage_demonstrated": False,
        "uncertainty": "Paired daily errors only; too few dependent days for an advantage claim.",
    }
