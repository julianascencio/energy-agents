"""Optional local Qiskit parity and PennyLane/PyTorch hybrid training adapters."""

import numpy as np


def qiskit_statevector(x: np.ndarray, *, entangle: bool = True) -> np.ndarray:
    """Same circuit as models.statevector, with explicit Qiskit endianness mapping."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    from .models import statevector

    statevector(x, entangle=entangle)  # validate dimensions and finite angles
    n = len(x)
    circuit = QuantumCircuit(n)
    for wire, value in enumerate(x):
        circuit.ry(float(value), n - 1 - wire)
    if entangle:
        for wire in range(n - 1):
            circuit.cx(n - 1 - wire, n - 2 - wire)
    for wire, value in enumerate(x):
        circuit.rz(float(value * x[(wire + 1) % n]), n - 1 - wire)
        circuit.ry(float(value), n - 1 - wire)
    return np.asarray(Statevector.from_instruction(circuit).data)


def neural_predict(kind: str, x: np.ndarray, y: np.ndarray, query: np.ndarray,
                   *, learning_rate: float = 0.03, epochs: int = 40, seed: int = 7) -> dict:
    """Train a classical MLP or hybrid four-qubit QNode with a PyTorch readout.

    Full-batch Adam, fixed epoch budgets, train-only transforms and local analytic
    simulation. Seeds are controlled without resetting the caller's Torch RNG.
    """
    import torch

    if kind not in {"torch_mlp", "hybrid_qnn"}:
        raise ValueError("kind must be torch_mlp or hybrid_qnn")
    if type(epochs) is not int or not 1 <= epochs <= 200:
        raise ValueError("epochs must be in 1..200")
    if not np.isfinite(learning_rate) or not 0 < learning_rate <= 0.1:
        raise ValueError("learning_rate must be in (0, 0.1]")
    if x.shape[1] != 4:
        raise ValueError("This bounded neural experiment requires exactly four features")
    mean, scale = x.mean(axis=0), np.maximum(x.std(axis=0), 1e-12)
    center, yscale = float(y.mean()), max(float(y.std()), 1e-12)
    train = torch.tensor(np.arctan((x - mean) / scale), dtype=torch.float64)
    target = torch.tensor((y - center) / yscale, dtype=torch.float64)
    test = torch.tensor(np.arctan((query - mean) / scale), dtype=torch.float64)

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        if kind == "torch_mlp":
            model = torch.nn.Sequential(torch.nn.Linear(4, 8), torch.nn.Tanh(),
                                        torch.nn.Linear(8, 1)).double()
        else:
            import pennylane as qml

            device = qml.device("default.qubit", wires=4, shots=None)

            @qml.qnode(device, interface="torch", diff_method="backprop")
            def circuit(inputs, weights):
                qml.AngleEmbedding(inputs, wires=range(4), rotation="Y")
                for layer in range(2):
                    for wire in range(4):
                        qml.RY(weights[layer, wire], wires=wire)
                    for wire in range(3):
                        qml.CNOT(wires=[wire, wire + 1])
                return [qml.expval(qml.PauliZ(wire)) for wire in range(4)]

            quantum = qml.qnn.TorchLayer(circuit, {"weights": (2, 4)})
            model = torch.nn.Sequential(quantum, torch.nn.Linear(4, 1)).double()
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        losses = []
        for _ in range(epochs):
            optimizer.zero_grad()
            loss = torch.mean((model(train).reshape(-1) - target) ** 2)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        with torch.no_grad():
            prediction = model(test).reshape(-1).numpy() * yscale + center
        return {"prediction": prediction, "loss_curve": losses, "seed": seed,
                "trainable_parameters": sum(p.numel() for p in model.parameters()),
                "epochs": epochs, "backend": "pennylane.default.qubit+torch"
                if kind == "hybrid_qnn" else "torch.cpu", "shots": None}
