"""
An agent that knows Energy Data Insights
========================================

Search the complete in-scope source inventory from the shipped pinned commit.
The catalogue contains real repository metadata, not synthetic capabilities.
This offline example executes retrieval only, not Energy Data Insights methods.
"""

import matplotlib.pyplot as plt

from energy_agents.knowledge import EnergyDataInsightsAgent
from energy_agents.pv import run_pv_workflow, synthetic_pv_case

agent = EnergyDataInsightsAgent()
coverage = agent.catalogue["coverage"]
print("Source commit:", agent.catalogue["commit"])
print("Coverage:", coverage)
counts = coverage["categories"]
fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
ax.barh(list(counts), list(counts.values()), color="#247b91")
ax.set(
    xlabel="Indexed source files (not validated capabilities)",
    title="Energy Data Insights — pinned repository inventory",
)
ax.spines[["top", "right"]].set_visible(False)
plt.show()

# %%
# Results preserve exact source paths and commit-pinned links. Filter to examples
# to find runnable entry points; inspect their source and requirements before use.
queries = [
    "PVGIS terrain weather",
    "PV degradation lifetime",
    "KGPV Chile snow soiling",
    "Timestral solar wind forecast",
    "BESS database",
    "satellite module counting Rengo",
]
for query in queries:
    print("\nRequest:", query)
    result = agent.search(query, category="example", limit=2)
    for entry in result["results"]:
        print(entry["title"], entry["source_url"])
    print(result["freshness"])

# %%
# The Technical Asset Manager receives relevant references in its planner context.
# Numerical PV findings remain separate from repository recommendations.
run = run_pv_workflow(synthetic_pv_case(), repository_query="PV degradation uncertainty examples")
assert run["success"]
print("Technical Asset Manager references:")
for entry in run["repository_knowledge"]["results"]:
    print(entry["path"], entry["source_url"])
print("No Energy Data Insights package was installed or executed by this workflow.")
