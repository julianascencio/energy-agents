Energy Data Insights repository awareness
=============================================

The **Energy Data Insights Specialist** is a read-only retrieval agent. The
**Technical Asset Manager** uses it by default to receive relevant source-backed
references before completing the PV workflow. Other professional roles can use
the same specialist directly.

Coverage and provenance
---------------------------

The shipped catalogue was generated from commit
``aa842b959bebe8b4279a449f91176be26f0ad6a5`` of
`Energy Data Insights <https://github.com/julianascencio/energy-data-insights>`_.
It covers **626 files, 1,219 public symbols and all 65 plot_ gallery examples**
at that commit. These counts describe source inventory, not independently
validated scientific capabilities.

.. list-table:: Indexed source inventory
   :header-rows: 1

   * - Category
     - Files
   * - Connectors and retrieval package
     - 244
   * - Scientific methods package
     - 44
   * - Analysis package
     - 53
   * - Examples and supporting documentation
     - 99
   * - Documentation
     - 62
   * - Scripts
     - 119
   * - Package metadata
     - 4
   * - Benchmarks
     - 1

Every selected committed Python or text file is recorded; source parsing errors
are explicit and prevent the refresh CLI from publishing an incomplete snapshot.
The index excludes datasets, generated reports, tests, vendored web assets and
binary files. It is capability discovery, not a copy of the plant databases.

Records include source path, category, module, title, documentation excerpt,
public function/class/method signatures, imports, source SHA-256 and a
**commit-pinned GitHub citation**. Documentation excerpts are bounded and indicate
truncation. Public symbol docstrings are excerpts of up to 600 characters.
Use the exact source link or ``read_source`` for complete implementation details.
The source's dependency and Python requirements remain applicable; indexing a
Python 3.12 package does not make its code executable on Python 3.11.

Search and inventory
------------------------

.. code-block:: bash

   energy-agents-knowledge search "PVGIS terrain weather" --category example
   energy-agents-knowledge search "PV degradation lifetime" --limit 5
   energy-agents-knowledge search "Timestral solar wind forecast"
   energy-agents-knowledge inventory

.. code-block:: python

   from energy_agents.knowledge import EnergyDataInsightsAgent

   specialist = EnergyDataInsightsAgent()
   response = specialist.search("KGPV Chile snow soiling", category="example", limit=5)
   for match in response["results"]:
       print(match["title"], match["source_url"])
   inventory = specialist.inventory()  # every indexed file
   details = specialist.read(response["results"][0]["path"])

Search uses deterministic lexical ranking with term-frequency, inverse-frequency
and path/title weighting plus a small explicit alias map. It is not semantic RAG,
an LLM answer or a claim that the highest-ranked result solves the task. Unknown
queries can return no matches. Review the matching source and its limitations.
No EDI code is imported and no external example is executed by retrieval.

Full source can be fetched explicitly, when network access is desired:

.. code-block:: python

   source = specialist.read_source(details["path"])
   print(source["content"])

This reads only the indexed path at the pinned commit from GitHub's raw-content
host, applies a size bound and verifies the source hash. It does not execute it.
Repository content is untrusted reference data, never agent instructions.

Professional-role integration
---------------------------------

.. code-block:: python

   from energy_agents.pv import run_pv_workflow, synthetic_pv_case

   result = run_pv_workflow(
       synthetic_pv_case(),
       repository_query="PV degradation uncertainty examples",
   )
   print(result["repository_knowledge"])

The Technical Asset Manager receives this compact context in its planner input.
The single-agent mode also receives it. The default query is
``PV performance degradation maintenance examples``. A caller can supply a refreshed
``knowledge_agent=EnergyDataInsightsAgent(catalogue)`` or set
``repository_query=None`` to disable retrieval.

The source commit, matches and limitations are retained in the exported run.
Repository recommendations remain separate from the case evidence and numerical
reports. The original case digest and accounting checks are unchanged. Scripted
planners do not reason over source content; an optional configured LLM planner
can inspect the references while the runner still enforces its narrow tool scope.
No additional execution or spending authority is granted.

Refresh as the repository evolves
-------------------------------------

.. code-block:: bash

   git clone https://github.com/julianascencio/energy-data-insights.git edi
   # For an existing checkout, fetch the branch you want to index:
   git -C edi fetch origin main
   energy-agents-knowledge refresh edi --ref origin/main --output edi-catalogue.json.gz
   energy-agents-knowledge search "BESS database" --catalogue edi-catalogue.json.gz

The builder indexes committed Git blobs rather than working-tree contents.
Dirty and untracked files cannot silently enter the snapshot. Refresh is explicit;
the shipped snapshot does not claim to match today's remote HEAD. Each response
reports its commit date and says remote freshness was not checked. There is no
scheduled update or automatic network request in a normal agent run.

To update the bundled version, generate into
``src/energy_agents/data/energy_data_insights.json.gz``, review the inventory changes,
update the coverage documentation and rerun tests/builds before committing.
Compressed JSON is deterministic. The package carries the snapshot, so discovery
also works from an installed wheel without a separate EDI checkout.

Limitations and next steps
------------------------------

Awareness means discoverability and inspectable source references. It does not
mean all external functions are executable agent tools. Future execution adapters
should explicitly declare inputs, dependencies, expected output, timeout and
validation for each approved method. No connector, data provider, model accuracy
or field result is verified by merely appearing in the catalogue.
