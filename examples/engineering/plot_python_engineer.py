"""
Python engineer: forecast-error coding proposal
======================================================================

A deterministic replay proposes an interval-energy forecast error utility,
independent test and runnable example. This is an offline protocol demonstration,
not generated output from a live LLM. Proposed code is never executed by the agent.
The unit is MWh per aligned interval; business valuation needs separate prices.
"""

from energy_agents.python_engineer import run_python_engineer


class ForecastCodingReplay:
    """Scripted proposal for reproducible CI and gallery rendering."""

    def next_action(self, context):
        return {
            "tool": "propose_files",
            "arguments": {
                "files": {
                    "forecast_metric.py": '''"""Aligned interval energy MAE in MWh."""
from math import isfinite
from collections.abc import Sequence


def energy_mae(actual: Sequence[float], predicted: Sequence[float]) -> float:
    """Require aligned, finite energy observations; missing is not zero."""
    if len(actual) != len(predicted) or not len(actual):
        raise ValueError("Need equal nonempty aligned intervals")
    if not all(isfinite(v) for v in [*actual, *predicted]):
        raise ValueError("Missing/nonfinite values need explicit preprocessing")
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)
''',
                    "tests/test_forecast_metric.py": """import pytest
from forecast_metric import energy_mae


def test_independent_mae():
    # Absolute errors 2, 0, 1 MWh -> 1 MWh mean, preserving reported zero.
    assert energy_mae([0, 5, 7], [2, 5, 6]) == 1


@pytest.mark.parametrize("actual,pred", [([], []), ([1], []), ([float("nan")], [0])])
def test_invalid_intervals(actual, pred):
    with pytest.raises(ValueError):
        energy_mae(actual, pred)
""",
                    "examples/forecast_error.py": '''"""Synthetic aligned MWh observations."""
from forecast_metric import energy_mae

print("Synthetic MAE (MWh):", energy_mae([0, 5, 7], [2, 5, 6]))
''',
                    "README.md": "Synthetic utility demo. Run with the project root on PYTHONPATH.",
                },
                "explanation": (
                    "Extract a dependency-free metric before introducing ML. Caller must align "
                    "intervals and supply MWh. This is not model training or a revenue estimate. "
                    "pytest is a development dependency. No EDI import is claimed."
                ),
                "validation_commands": [
                    "python -m pytest tests/test_forecast_metric.py",
                    "PYTHONPATH=. python examples/forecast_error.py",
                ],
            },
        }


result = run_python_engineer(
    "Propose an independently tested energy forecast MAE utility in Python.",
    {"architecture": "Separate reusable methods, tests and offline examples."},
    ForecastCodingReplay(),
)
assert result["success"]
print("Agent validation:", result["validation"])
print("Tests executed by agent:", result["tests_run"])
print("Proposed files:", list(result["bundle"]["files"]))
print("Review commands:", result["bundle"]["validation_commands"])
