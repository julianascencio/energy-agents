# Public EDI dependency in CI

Documentation and operations integration install the public `energy-methods`
wheel from [PyPI](https://pypi.org/project/energy-methods/), using the exact version
and SHA-256 in `requirements/operations.txt`. No GitHub credential or private
repository checkout is used.

The action installs only the wheel with `--no-deps --only-binary=:all:
--require-hashes`. The required operations modules use the Python standard
library; unrelated scientific dependencies are not installed in these jobs.
Python 3.12 or newer is required.

Before tests or gallery execution, the action checks these public APIs:

- `energy_methods.operations.DailyEnergyRecord`
- `energy_methods.operations.analyze_daily_operations`
- `energy_methods.dispatch_review.DailyScheduleRecord`
- `energy_methods.dispatch_review.review_dispatch_schedule`

## Compatible release

`energy-methods` 0.1.1 contains all four APIs. Version 0.1.0 predates them and
cannot run this integration. Keep the exact public version and wheel hash
in `requirements/operations.txt` together when upgrading.

Validate the operations integration tests, both CLI examples and the strict
documentation/gallery build against the released wheel before merging.
The API gate remains mandatory on every run.

## Reproduce

```bash
python -m pip install --no-deps --only-binary=:all: --require-hashes \
  --index-url https://pypi.org/simple -r requirements/operations.txt
python -c "from energy_methods import operations, dispatch_review"
```
