Installation
============

Install from a source checkout; this package has not been released to PyPI.
Python 3.11 or later is required. The core has no third-party runtime dependencies.
The operations integration and full documentation build require Python 3.12+
and the pinned Energy Data Insights backend.

.. code-block:: bash

   git clone https://github.com/julianascencio/energy-agents.git
   cd energy-agents
   python -m pip install -e ".[dev,docs]"
   python -m pip install -r requirements/operations.txt  # Python 3.12+
   energy-agents --output outputs/building_edits
   python examples/buildings/plot_building_edits.py

Quality and documentation
-------------------------

.. code-block:: bash

   python -m pytest
   ruff check .
   python -m build
   sphinx-build -W --keep-going -b html docs/sphinx/source docs/sphinx/build/html

GitHub Pages
------------

Set Settings → Pages → Build and deployment → Source to GitHub Actions.
The docs workflow builds on PRs and main, uploads a browsable HTML artifact on
PRs, and deploys to Pages on main. No hosted site is implied before deployment.
