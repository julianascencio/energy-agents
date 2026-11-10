"""Small classical, quantum-inspired and simulated quantum forecasting models."""

import numpy as np


def angles(x: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """Bound train-standardized features in (-pi/2, pi/2), without test-set fitting."""
    return np.arctan((x - mean) / scale)


def product_features(x: np.ndarray) -> np.ndarray:
    """Explicit trigonometric tensor-product map; classical, with exponential width.

    This illustrates the local feature map used in quantum-inspired tensor models.
    It is not a compressed matrix-product-state learner or quantum execution.
    """
    result = np.ones((len(x), 1))
    for column in x.T:
        local = np.column_stack((np.cos(column / 2), np.sin(column / 2)))
        result = (result[:, :, None] * local[:, None, :]).reshape(len(x), -1)
    return result


def _single(state: np.ndarray, gate: np.ndarray, wire: int, n: int) -> np.ndarray:
    tensor = np.moveaxis(state.reshape([2] * n), wire, 0)
    tensor = (gate @ tensor.reshape(2, -1)).reshape([2] * n)
    return np.moveaxis(tensor, 0, wire).reshape(-1)


def statevector(x: np.ndarray, *, entangle: bool = True) -> np.ndarray:
    """RY encoding -> CNOT chain -> data RZ -> RY re-upload (big-endian wires).

    The data-dependent operations after entanglement prevent the fixed CNOT layer
    from cancelling out of every fidelity. No shots, device noise or QPU is used.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or not 1 <= len(x) <= 8 or not np.isfinite(x).all():
        raise ValueError("Supply 1..8 finite angles")
    n = len(x)
    state = np.zeros(2**n, dtype=complex)
    state[0] = 1

    def ry(angle):
        c, s = np.cos(angle / 2), np.sin(angle / 2)
        return np.array([[c, -s], [s, c]])

    for wire, value in enumerate(x):
        state = _single(state, ry(value), wire, n)
    if entangle:
        indices = np.arange(2**n)
        for wire in range(n - 1):
            permutation = indices ^ (((indices >> (n - 1 - wire)) & 1) << (n - 2 - wire))
            state = state[permutation]
    for wire, value in enumerate(x):
        phase = value * x[(wire + 1) % n]
        state = _single(state, np.diag([np.exp(-0.5j * phase),
                                       np.exp(0.5j * phase)]), wire, n)
        state = _single(state, ry(value), wire, n)
    return state


def quantum_states(x: np.ndarray, *, entangle: bool = True) -> np.ndarray:
    return np.stack([statevector(row, entangle=entangle) for row in x])


def fidelity_kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """K(a,b)=|<psi(a)|psi(b)>|^2; exact pure-state kernel, positive semidefinite."""
    return np.clip(np.abs(left.conj() @ right.T) ** 2, 0, 1)


def fit_predict(kind: str, x: np.ndarray, y: np.ndarray, query: np.ndarray,
                *, alpha: float, gamma: float = 1.0) -> np.ndarray:
    """Fit one small regressor; all fitted transforms use only supplied training x/y."""
    if alpha <= 0 or not np.isfinite(alpha) or gamma <= 0 or not np.isfinite(gamma):
        raise ValueError("Regularization and gamma must be positive and finite")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale = np.where(scale < 1e-12, 1, scale)
    a, b = (x - mean) / scale, (query - mean) / scale
    center = float(y.mean())
    if kind in {"ridge", "product_ridge"}:
        if kind == "product_ridge":
            a, b = product_features(np.arctan(a)), product_features(np.arctan(b))
        feature_mean = a.mean(axis=0)
        a, b = a - feature_mean, b - feature_mean
        weights = np.linalg.solve(a.T @ a + alpha * np.eye(a.shape[1]), a.T @ (y - center))
        return b @ weights + center
    if kind == "rbf_kernel":
        def kernel(u, v):
            return np.exp(-gamma * ((u[:, None, :] - v[None, :, :]) ** 2).sum(axis=2))
        train, test = kernel(a, a), kernel(b, a)
    elif kind in {"quantum_kernel", "quantum_no_entanglement"}:
        states = quantum_states(np.arctan(a), entangle=kind == "quantum_kernel")
        query_states = quantum_states(np.arctan(b), entangle=kind == "quantum_kernel")
        train, test = fidelity_kernel(states, states), fidelity_kernel(query_states, states)
    else:
        raise ValueError(f"Unknown model: {kind}")
    # Kernel centering gives an unpenalized intercept consistent with primal ridge.
    column_mean, grand_mean = train.mean(axis=0), float(train.mean())
    train = train - column_mean[None, :] - column_mean[:, None] + grand_mean
    test = test - column_mean[None, :] - test.mean(axis=1)[:, None] + grand_mean
    weights = np.linalg.solve(train + alpha * np.eye(len(x)), y - center)
    return test @ weights + center


def shot_diagnostic(x: np.ndarray, *, seed: int = 31) -> dict:
    """Binomial overlap-estimation sensitivity; not noisy training or hardware emulation."""
    states = quantum_states(x[:16])
    values = fidelity_kernel(states, states)[np.triu_indices(len(states), k=1)]
    rng = np.random.default_rng(seed)
    return {"kind": "binomial_overlap_sampling_only", "seed": seed,
            "pair_count": len(values), "device_noise_modelled": False,
            "by_shots": {str(shots): float(np.mean(np.abs(
                rng.binomial(shots, values) / shots - values))) for shots in (128, 1024)}}
