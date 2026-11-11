# Private EDI dependency in CI

The documentation and operations integration jobs use this action to install
the exact Energy Data Insights commit recorded in `requirements/operations.txt`.
The standard `GITHUB_TOKEN` only has access to the current repository.

Create an Actions repository secret named `EDI_READ_TOKEN` in
[energy-agents settings](https://github.com/julianascencio/energy-agents/settings/secrets/actions).
Use a fine-grained token restricted to `julianascencio/energy-data-insights`,
with **Contents: read-only** permission. Configure and rotate it in GitHub;
never commit the credential or put its value in an issue or pull request.

Both jobs pass the secret to this action. The pinned revision is parsed from
the existing requirements file, so the action does not introduce a second pin.
Checkout does not persist the token in Git configuration, and pip installs
from that authenticated local checkout. Private source stays in the runner.

A missing token produces an explicit failure. The integration tests and
documentation gallery remain required job steps; they are not skipped or
replaced with mocks. Fork pull requests cannot use repository secrets.
