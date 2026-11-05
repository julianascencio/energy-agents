User guide
==========

Inputs → methods → agent → analysis
------------------------------------------------------------

The synthetic input has two simple glazing materials and three Lights objects,
one for each design-level calculation method. It is an epJSON fragment, not a
complete EnergyPlus building. Existing objects and inactive fields are preserved.

.. code-block:: python

   from energy_agents.inputs import synthetic_model
   from energy_agents import edit_lighting, run_agent

   original = synthetic_model()
   changed = edit_lighting(original, reduction=0.30)
   result = run_agent(original, "windows", "primitive")
   assert result["success"]

A planner proposes one action at a time. Domain tools encapsulate the supported
edit; the primitive surface exposes an allowlisted field assignment. The runner
validates exact postconditions before accepting completion. It retries at most
three times, starting each attempt from the original to prevent compounding a
30% reduction. The default budget is 20 calls per attempt, including completion.
This is in-process orchestration, not MCP or a multi-agent RAG implementation.

Live LLM adapter
----------------

Choose a Chat Completions compatible HTTPS endpoint and a model that returns JSON
text. Set ENERGY_AGENTS_API_KEY in your environment. Inputs are sent to that provider.

.. code-block:: python

   import os
   from energy_agents.connectors import ChatCompletionsPlanner
   from energy_agents.inputs import synthetic_model
   from energy_agents import run_agent

   planner = ChatCompletionsPlanner(
       endpoint=os.environ["ENERGY_AGENTS_ENDPOINT"],
       model=os.environ["ENERGY_AGENTS_MODEL"],
   )
   result = run_agent(synthetic_model(), "lighting", "domain", planner)
   print(result["success"], planner.usage)

The adapter does not execute model-generated Python or shell commands. Invalid
JSON/actions fail the attempt; provider/network errors propagate to the caller.
It is tested with mocked HTTP, not a live provider. Temperature zero does not
guarantee identical outputs across model/service versions. Record the endpoint,
model version, provider usage and traces for any reported live experiment.

Reproducibility and limits
--------------------------

``energy-agents --output outputs/building_edits`` writes synthetic input,
replay results, a separate published-results file and SHA-256 manifest.
The gallery uses the same public API. Local edit counts exclude finish calls.
Published counts retain the paper's scope. Neither local output nor the optional
LLM interface establishes NECB compliance, EnergyPlus validity or energy savings.

Before a real simulation, validate a complete model against the matching
EnergyPlus schema and execute EnergyPlus with documented weather and version.
Do not feed this minimal fragment into annual simulation. Conversion of full
HVAC topology and standards retrieval remain future work.
