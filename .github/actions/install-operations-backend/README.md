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

## Current release blocker

As checked on 2026-11-13, the only published release is 0.1.0, uploaded on
2026-11-03. Its wheel does not contain `operations` or `dispatch_review`.
Installation succeeds, but the API check correctly fails. This version must
not be described as a working operations backend.

Publish an upstream release containing those APIs, then update the exact
version and public wheel hash together in `requirements/operations.txt`.
Run the operations integration tests, both CLI examples and the strict
documentation/gallery build against that released wheel before merging.
Do not skip tests, substitute local calculations or silently fall back to Git.

## Reproduce

```bash
python -m pip install --no-deps --only-binary=:all: --require-hashes \
  --index-url https://pypi.org/simple -r requirements/operations.txt
python -c "from energy_methods import operations, dispatch_review"
```
