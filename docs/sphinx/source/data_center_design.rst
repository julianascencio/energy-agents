Data center design agents
=========================

Fourteen advisory specialists combine discipline-specific context, screening tools,
structured evidence gaps and the existing dependency-aware orchestrator. They are
functional agents inspired by public roles, not Microsoft employees or internal
Microsoft engineering standards.

Source extraction and boundaries
--------------------------------

`Brian Bakerman's LinkedIn post <https://lnkd.in/p/e4cNpEE5>`_ was read through
its public page on 7 November 2026. The visible text groups designers into the
following six categories. Counts are the author's approximate estimates, not
verified headcount. The embedded graphic could not be inspected, so individual
job titles or names inside that graphic have not been exhaustively extracted.

.. list-table:: Post groups and implemented agents
   :header-rows: 1
   :widths: 30 10 60

   * - Post group
     - Approximate people
     - Our functional agents
   * - Design Leaders
     - 40
     - Design Director; Technical Governance Lead
   * - Electrical & Controls
     - 35
     - Electrical Power; Controls and Power Monitoring
   * - Mechanical & Cooling
     - 30
     - Mechanical and Air Cooling; Liquid Cooling
   * - Structure, Civil & Architecture
     - 15
     - Civil; Structural; Architect and BIM Coordinator
   * - Design Management
     - 15
     - Design Manager
   * - E2E Delivery
     - 25
     - Delivery Manager; Commissioning and Handover

Telecommunications is an addition motivated by a visible comment identifying its
omission. Energy and Water Performance is our additional specialization. Exact
agent titles are our decomposition of the groups, not claims that the post lists
those exact job titles. The post explicitly mentions regional engineering
leadership, technical governance and power monitoring design management.

Run the example
---------------

.. code-block:: bash

   pip install -e ".[dev,docs]"
   energy-agents-design --output outputs/data_center_design
   python examples/data_centers/plot_design_team.py

The CLI exports the synthetic case, full source/role catalogue, numerical screen
and fourteen-agent trace. The gallery executes offline without API keys.

.. code-block:: python

   from energy_agents.data_center import reference_case, run_design_team

   result = run_design_team(reference_case())
   assert result["success"]  # completed protocols, not approved engineering
   assert not result["design_approved"]
   print(result["results"]["electrical_engineer"]["review"])

Workflow and authority
----------------------

The director runs first. Ten discipline specialists then receive its report.
The design manager consolidates those reports, technical governance reviews the
coordination output, and delivery receives governance's review. The scheduler is
sequential and dependency-aware; a failed upstream protocol blocks dependents.
Engineering gaps do not stop the review process: they remain in nested upstream
reports and every downstream result retains a human-review requirement.

Each specialist calls ``review_design`` once, then ``submit_review``. The runner
computes its metrics, evidence gaps and checklist independently of model output.
It only validates the narrative's shape and cited source IDs, not factual quality
or whether each citation supports the narrative. Completion never grants design
approval. Document references are recorded but their contents are not fetched or
verified. The listed deliverables are work to prepare, not automatically generated
construction drawings, reports or certifications.

Optional LLM usage
------------------

.. code-block:: python

   from energy_agents.data_center import DataCenterDesignPlanner, run_design_agent

   planner = DataCenterDesignPlanner(
       "liquid_cooling_engineer",
       endpoint="https://YOUR-PROVIDER/chat/completions",
       model="YOUR-MODEL",
   )
   review = run_design_agent("liquid_cooling_engineer", reference_case(), planner)

Set ``ENERGY_AGENTS_API_KEY`` for the chosen endpoint. A team accepts a ``planners``
mapping keyed by role ID; unspecified roles use deterministic replay. Only supply
case and upstream information suitable for disclosure to that provider. The
planner receives the role card, original curated literature notes, required inputs,
review checks and upstream outputs. No live model call or quality evaluation was
performed for this example.

Numerical methods and assumptions
---------------------------------

* Peak facility MW = IT MW multiplied by a user-supplied peak facility multiplier.
  This is explicitly separate from annual PUE; neither is an equipment model.
* Rack count = ceiling(IT MW times 1000 / rack kW), assuming homogeneous racks.
* Firm equipment MW = (installed units minus unavailable units) times unit MW.
  UPS demand is IT-only in this example. Distribution paths, derating, bypass,
  battery autonomy, transient loads and common-cause failure are not modeled.
* Liquid heat = IT MW times liquid fraction. Residual IT heat goes to air.
  Cooling auxiliary and other facility heat must be added in a detailed study.
* Liquid mass flow kg/s = liquid MW times 1000 / (fluid heat capacity in kJ/kg/K
  times temperature difference in K). The illustrative fluid heat capacity is
  4.186; replace with the selected fluid's actual properties. Pressure drop and
  pump sizing are outside this screen.
* Annual IT MWh = IT MW times annual load factor times annual hours. Facility
  MWh = IT MWh times annual PUE. Cost uses a flat EUR/MWh scenario; no demand
  charges, tax, time-varying tariff or financing is included.
* Site water m3 = IT MWh times site WUE in L/IT-kWh (conversion factors cancel).
  This is an assumed site metric, not Microsoft data and not cooling-only water.

The fixture has 200 racks, 26 MW peak facility demand and 24 MW grid supply,
therefore a -2 MW grid margin. It has 140,160 IT MWh and 175,200 facility MWh/year,
EUR 17.52 million/year electricity and 28,032 m3/year assumed site water. The
liquid/air IT heat split is 16/4 MW. Equal firm capacity and demand means zero
arithmetic margin, not demonstrated resilience. No Tier or code certification is
inferred from these calculations.

Role cards
----------

Data Center Design Director
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``design_director`` — Design Leaders. Translate capacity demand into a staged owner brief and explicit trade-offs across resilience, cost, schedule and energy.

Required evidence: owner_requirements, capacity_roadmap.

Expected deliverables: owner brief, decision register, discipline assignments.

Review questions:

* Define usable IT capacity separately from utility capacity.
* Record availability objectives and expansion phases.
* Assign unresolved decisions to accountable specialists.

Reading context: ``msroles``, ``uptime``, ``doe2024``.

Electrical Power Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~

``electrical_engineer`` — Electrical & Controls. Develop the grid-to-rack power concept and quantify capacity margins before detailed electrical studies.

Required evidence: single_line_diagram, utility_offer, protection_study.

Expected deliverables: load schedule, capacity gap report, electrical study scope.

Review questions:

* Separate peak planning multiplier from annual PUE.
* Review UPS bypass and maintenance paths.
* Request load-flow, fault-level, selectivity and arc-flash studies from qualified engineers.

Reading context: ``doe2024``, ``uptime``.

Controls and Power Monitoring Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``controls_engineer`` — Electrical & Controls. Define observable BMS/EPMS interfaces and failure-aware control review requirements.

Required evidence: points_list, sequence_of_operations, ot_network_diagram.

Expected deliverables: metering and alarm matrix, sequence review, OT interface register.

Review questions:

* Map meters, alarms and timestamps to equipment IDs.
* Specify sensor failure and communications-loss responses.
* Review OT segmentation and change ownership.

Reading context: ``nist``, ``doe2024``.

Mechanical and Air Cooling Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``mechanical_engineer`` — Mechanical & Cooling. Assess residual air-side heat removal and coordinate environmental limits with IT equipment.

Required evidence: thermal_envelope, airflow_model, cooling_topology.

Expected deliverables: air heat balance, thermal study brief, cooling interface review.

Review questions:

* Check inlet rather than room-average conditions.
* Review containment and recirculation assumptions.
* Request design-weather and maintenance-mode thermal studies.

Reading context: ``ashrae2023``, ``doe2024``.

Liquid Cooling Engineer
~~~~~~~~~~~~~~~~~~~~~~~

``liquid_cooling_engineer`` — Mechanical & Cooling. Scope direct-to-chip loops, CDU capacity and fluid interfaces for high-density racks.

Required evidence: cdu_datasheet, fluid_specification, leak_response_plan.

Expected deliverables: liquid heat balance, flow estimate, CDU interface register.

Review questions:

* Verify TCS/FWS temperatures and pressure interfaces.
* Check fluid material compatibility and water quality.
* Request leak isolation, flushing and serviceability evidence.

Reading context: ``ocp``, ``ashrae2023``, ``mscooling``.

Civil and Site Infrastructure Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``civil_engineer`` — Structure, Civil & Architecture. Identify site constraints and due-diligence gaps affecting utility corridors, grading and access.

Required evidence: topographic_survey, geotechnical_report, flood_assessment.

Expected deliverables: site constraints register, due-diligence requests, utility corridor brief.

Review questions:

* Coordinate drainage, access and underground services.
* Identify local permitting and environmental constraints.
* Request survey and hazard evidence before site suitability conclusions.

Reading context: ``asce``, ``tia``.

Structural Engineer
~~~~~~~~~~~~~~~~~~~

``structural_engineer`` — Structure, Civil & Architecture. Frame structural verification for heavy racks, plant loads, anchors and equipment replacement routes.

Required evidence: structural_load_schedule, structural_calculations, equipment_weights.

Expected deliverables: load interface schedule, structural verification requests.

Review questions:

* Check concentrated, dynamic and distributed loads separately.
* Include anchorage and site hazards under applicable codes.
* Request signed calculations; never infer slab adequacy from rack count.

Reading context: ``asce``, ``ifc``.

Data Center Architect and BIM Coordinator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``architect`` — Structure, Civil & Architecture. Coordinate space, maintainability, life safety and model exchange requirements.

Required evidence: site_layout, life_safety_strategy, bim_execution_plan.

Expected deliverables: space and adjacency brief, BIM coordination register, life-safety review requests.

Review questions:

* Review equipment replacement routes and service clearances.
* Coordinate fire compartments and egress with local specialists.
* Set IFC versions, units and model ownership before exchanging geometry.

Reading context: ``ifc``, ``tia``, ``cx``.

Telecommunications Infrastructure Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``telecom_engineer`` — Added: comment-identified omission. Define physical network pathways independently of electrical and controls design.

Required evidence: fiber_route_survey, network_topology, cabling_schedule.

Expected deliverables: telecom pathway brief, network diversity review.

Review questions:

* Check carrier entrances for shared physical failure points.
* Coordinate meet-me rooms, pathways and rack interfaces.
* Request optical budgets and cabling acceptance tests.

Reading context: ``tia``, ``ashrae2023``.

Energy and Water Performance Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``sustainability_engineer`` — Added: supporting specialization. Compare energy and water scenarios with explicit boundaries and site-specific evidence.

Required evidence: weather_series, water_balance, energy_model.

Expected deliverables: annual energy screen, water boundary review, scenario requirements.

Review questions:

* Keep annual PUE separate from peak sizing.
* Declare WUE denominator and cooling-versus-site water boundary.
* Request hourly tariffs, emissions, climate and source provenance before optimization.

Reading context: ``doe2024``, ``mscooling``.

Commissioning and Handover Engineer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``commissioning_engineer`` — E2E Delivery. Plan verifiable acceptance from owner requirements through integrated systems testing.

Required evidence: commissioning_plan, integrated_test_scripts, operations_manual.

Expected deliverables: commissioning matrix, test evidence requests, handover checklist.

Review questions:

* Trace test acceptance criteria to owner requirements.
* Plan loss-of-utility, failed-component and recovery scenarios with authorized teams.
* Track defects, retests, training and handover evidence.

Reading context: ``cx``, ``msroles``, ``uptime``.

Data Center Design Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~

``design_manager`` — Design Management. Coordinate design packages, dependencies, review gates and unresolved interfaces.

Required evidence: design_schedule, interface_register, cost_plan.

Expected deliverables: design coordination report, review gate register.

Review questions:

* Reconcile specialist scope and assumptions.
* Assign owners and dates to unresolved interfaces.
* Preserve missing evidence and design changes in gate reports.

Reading context: ``cx``, ``ifc``, ``msroles``.

Technical Governance Lead
~~~~~~~~~~~~~~~~~~~~~~~~~

``technical_governance`` — Design Leaders. Independently review evidence completeness, exceptions and resilience claims before escalation.

Required evidence: standards_register, deviation_register.

Expected deliverables: assurance review, exception register.

Review questions:

* Identify adopted standards and editions by jurisdiction.
* Distinguish calculations from verified compliance.
* Reject certification claims based only on redundancy arithmetic.

Reading context: ``uptime``, ``tia``, ``cx``.

End-to-End Delivery Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``delivery_manager`` — E2E Delivery. Turn coordinated design into a staged procurement, construction and handover proposal.

Required evidence: procurement_schedule, construction_plan, handover_acceptance.

Expected deliverables: delivery roadmap, readiness gaps, owner handoff.

Review questions:

* Track long-lead equipment and energization dependencies.
* Carry design gaps into procurement and construction risks.
* Keep ready-for-service acceptance separate from completed agent execution.

Reading context: ``msroles``, ``cx``.

Literature and context register
-------------------------------

These are concise original reading notes, not copies of full standards. Public
publisher summaries identify relevant standards; obtain applicable editions and
local adoption requirements before clause-level engineering review. US structural
references do not establish requirements for Spain or other jurisdictions.

* **doe2024** — `DOE/FEMP: Best Practices Guide for Energy-Efficient Data Center Design (July 2024) <https://www.energy.gov/sites/default/files/2024-07/best-practice-guide-data-center-design.pdf>`_.
  Coordinate IT demand, environmental conditions, airflow, cooling, electrical distribution and heat recovery. Evaluate efficiency at consistent measurement boundaries; a single design is not optimal for every site.
  Access scope: Public guide; chapters 2–7.

* **ashrae2023** — `ASHRAE Handbook 2023, Chapter 20: Data Centers and Telecommunication Facilities <https://handbook.ashrae.org/Handbooks/A23/IP/A23_Ch20/a23_ch20_ip.aspx>`_.
  Power, space, cooling and networking depend on each other. Use equipment environmental envelopes and measured inlet conditions; coordinate heat loads and serviceability across disciplines.
  Access scope: Public chapter; equipment-specific limits still required.

* **ocp** — `Open Compute Project: Cold Plate project and contribution catalogue <https://www.opencompute.org/projects/cooling-environments/cold-plate/>`_.
  Use cold-plate, manifold, fluid and CDU requirements as separate interfaces. Request selected equipment qualification, fluid compatibility, leak response and service procedures before accepting a liquid-cooling concept.
  Access scope: Public project overview; individual specification revisions must be checked.

* **uptime** — `Uptime Institute: Tier Classification System <https://uptimeinstitute.com/tiers>`_.
  Review maintainability and distribution paths as well as component redundancy. An N+1 capacity calculation alone cannot establish a Tier classification or certification.
  Access scope: Public overview; topology standard and certification are separate.

* **tia** — `TIA-942: Telecommunications Infrastructure Standard for Data Centers <https://tiaonline.org/standard/tia-942/>`_.
  Use a dedicated telecommunications design package and coordinate it with the physical facility. Obtain the applicable standard and project edition before making clause-level compliance claims.
  Access scope: Public overview only; full normative standard not reproduced.

* **nist** — `NIST SP 800-82 Rev. 3: Guide to Operational Technology Security (2023) <https://csrc.nist.gov/pubs/sp/800/82/r3/final>`_.
  Treat building automation and physical environment monitoring as OT. Review asset inventories, network boundaries, access, monitoring and recovery with operational reliability constraints.
  Access scope: Public final publication; Rev. 4 initial public draft exists, not substituted.

* **cx** — `WBDG: Roles and Responsibilities in the Commissioning Process <https://legacy.wbdg.org/building-commissioning/roles-and-responsibilities-commissioning-process>`_.
  Link owner requirements, basis of design, design reviews, commissioning plans, issues and operations manuals. Assign acceptance ownership and retain evidence of unresolved issues.
  Access scope: Public process guidance.

* **asce** — `ASCE/SEI 7-22: Minimum Design Loads and Associated Criteria <https://www.asce.org/publications-and-news/codes-and-standards/asce-sei-7-22>`_.
  Identify applicable structural loads and local code adoption. Request site-specific hazards and load combinations; this catalogue does not contain normative design values.
  Access scope: Public publisher overview; US reference, not a global code.

* **ifc** — `buildingSMART: Industry Foundation Classes (IFC) <https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/?lang=en>`_.
  Use explicit IFC exchange versions and validate model exchanges. Preserve object identity, units and discipline ownership when coordinating information across design tools.
  Access scope: Public overview.

* **mscooling** — `Microsoft: Sustainable by design, next-generation datacenters (9 December 2024) <https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling/>`_.
  Microsoft describes cooling without evaporative water consumption. Keep cooling water, total site water and supply-chain water separate; do not infer that every facility has zero water demand.
  Access scope: Public vendor announcement, not independent performance evidence.

* **msroles** — `Microsoft Careers: Datacenters <https://careers.microsoft.com/v2/global/en/datacenters.html>`_.
  Public examples include electrical and mechanical engineers, construction managers and commissioning managers, complementing the six groups described in the LinkedIn post.
  Access scope: Public role descriptions, not an organization chart.

Integration with other energy workflows
---------------------------------------

Use the existing bridge-power workflow for a separate investment screen. Do not
convert its financial result into electrical design acceptance. For site climate,
grid, renewable supply or storage scenarios, the sustainability role requests
provenance-bearing inputs that can be prepared with Energy Data Insights. This
module does not invoke EDI connectors, a simulator, Revit, AutoCAD, IFC parsers or
CFD. Those integrations require explicit adapters and independent validation.

Validation
----------

Tests cover independent energy and capacity balances, heat partition boundaries,
invalid/nonfinite values, water units, role coverage, input isolation, unsupported
tools, invalid citations and blocked downstream tasks. A documentation build runs
the example. These checks verify software contracts and arithmetic, not engineering
accuracy on a real facility or live model performance.
