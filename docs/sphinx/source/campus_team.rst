Campus design-to-delivery team
=============================

This team maps the six functions visible in the user-supplied Oracle team
screenshots to **17 generic advisory agents**. Fourteen specialists are reused;
three fill missing responsibilities. The screenshots are third-party material,
not a verified organization chart. Employee identities, headcounts and internal
company standards are not encoded. No affiliation or employee impersonation is
implied. The exact role decomposition and workflow below are this project's design.

.. list-table:: Functional coverage
   :header-rows: 1
   :widths: 28 72

   * - Screenshot function
     - Agents
   * - Design Leaders
     - Design Director; Technical Governance Lead
   * - Electrical & Mechanical
     - Electrical Power; Controls and Power Monitoring; Mechanical and Air Cooling; Liquid Cooling
   * - Data Center Design
     - **Campus Design Engineer (new)**; Civil; Structural; Architect/BIM; Design Manager
   * - Data Hall & Site Planning
     - **Data Hall and Site Planner (new)**
   * - Facilities Development
     - **Facilities Development Manager (new)**
   * - E2E Delivery
     - Commissioning and Handover; End-to-End Delivery Manager

Telecommunications and Energy/Water Performance are two supporting specialists
from the existing catalogue. They are explicit additions to the six source groups.
The original fourteen-agent workflow and default catalogue remain unchanged.

Run and inspect
---------------

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   energy-agents-campus --output outputs/campus_team
   python examples/data_centers/plot_campus_team.py
   energy-agents-campus --input outputs/campus_team/case.json --output outputs/replay

The CLI writes case.json, catalogue.json, screen.json, layout.json and team.json.
All inputs are synthetic by default. There is no network or model dependency.
``--input`` accepts the same JSON shape and either ``synthetic`` or
``user_supplied`` evidence. User-supplied does not mean independently verified.

.. code-block:: python

   from energy_agents.campus import campus_reference_case, run_campus_team
   from energy_agents.data_center import design_roles, run_design_agent

   case = campus_reference_case()
   roles = design_roles(include_campus=True)  # 17; default remains 14
   planner_review = run_design_agent("data_hall_site_planner", case)
   result = run_campus_team(case)
   assert result["success"]  # bounded protocols completed
   assert not result["readiness"]["ready_for_service"]
   print(result["readiness"]["issues"])

The new roles use the existing ``DataCenterDesignPlanner`` and tool protocol.
For an optional live run, pass a planner configured for a new role ID into
``run_design_agent`` or the team ``planners`` mapping. Unspecified roles use replay.
Role cards, curated source notes, original case, upstream reports and immutable
computed metrics are provided to the planner. Live LLM quality has not been tested.

Three new role contracts
-----------------------

**campus_design_engineer** reconciles owner demand, campus capacity, utility
requirements and discipline interfaces. Skills cover capacity reconciliation,
basis-of-design review and interface management. Required documents are the campus
basis of design, campus masterplan and phasing strategy. Its screen includes IT MW,
facility MW, grid margin, rack demand and layout margin. It hands findings to the
hall/site planner and design manager.

**data_hall_site_planner** screens equal-hall rack and area budgets, then requests
site constraints, access and layout evidence. Skills cover hall capacity, space
budgets and site-constraint triage. Required documents are the hall layout, site
constraints register and equipment access plan. Outputs include usable rack slots,
per-hall requirements, shortfalls and evidence requests. It hands work to the design
manager and facilities developer. It does not produce a spatial layout or establish
egress, structural, flood or fire safety compliance.

**facilities_development_manager** carries design issues into permit, utility,
construction and startup review. Skills cover development readiness, issue ownership
and startup dependencies. Required documents are the permit register, utility
energization plan, construction readiness plan and startup readiness register.
It hands findings to commissioning, technical governance and delivery. A supplied
reference is not an issued permit or verified acceptance test.

The versioned ``data/data_center/campus.json`` contains each role's mandate,
skills, tools, inputs, checks, deliverables, evaluation criteria, handoffs and source
IDs. Deliverables listed on cards are work to prepare. The offline replay generates
screens, checklists and evidence requests, not completed engineering documents.

Workflow and issue ownership
---------------------------

The director establishes the brief, then the campus engineer performs the concept
screen. Nine disciplines review it. The hall/site planner receives their reports,
the design manager consolidates, facilities development reviews readiness, and
commissioning reviews the handover. Governance and delivery each receive **every
preceding report**. The orchestrator executes this dependency graph sequentially.

Failed agent protocols block dependents. Engineering shortfalls remain review
findings: they do not prevent other disciplines from documenting their issues.
The final readiness register records the responsible role for each capacity
shortfall, missing document reference, unverified reference and incomplete protocol.
The same project constraint may appear under several roles; row counts are not
unique project risk counts. Service readiness and design approval remain false.

Hall-capacity method and worked example
--------------------------------------

The new tool uses homogeneous racks and equal halls. The four ``layout`` fields
are ``hall_count`` and ``rack_slots_per_hall`` (positive integers), plus
``hall_white_space_m2`` and ``planning_m2_per_rack`` (positive finite numbers).
The area allowance includes assumed aisles/service space; it is user input, not
a code requirement. Do not use the example's 6 m2/rack as an engineering standard.

* Required racks = ceiling(IT MW x 1000 / rack kW).
* Area-limited slots in each hall = floor(hall area / area allowance per rack).
* Usable slots per hall = minimum(planned slots, area-limited slots).
* Total usable slots = hall count x usable slots per hall.
* Layout margin = total usable slots minus required racks.

The existing :doc:`data_center_design` screen supplies power, cooling, annual
energy and water arithmetic. The default campus has 20 MW IT, 100 kW/rack,
two halls, 90 planned slots per hall, 600 m2 per hall and a 6 m2/rack allowance.
It therefore needs 200 racks but accommodates 180: **20 slots short**. Its 24 MW
utility assumption is **2 MW short** of the 26 MW facility peak planning estimate.

The gallery changes the assumptions to 26 MW utility supply and 100 planned slots
per hall. Both arithmetic margins become zero, but document gaps remain and no
approval is inferred. This is a scenario comparison, not an implemented upgrade,
optimization, proof of resilience, savings estimate or real company's design.
The tool does not check aisle geometry, rack placement, heterogeneous halls,
maintenance access, hydraulic paths or physical distribution topology.

Evidence and integration boundaries
-----------------------------------

The six group names come from the two user-supplied screenshots received on
11 November 2026. Exact agent titles and allocation are our functional design.
The existing primary-source reading context is reused:

* `DOE/FEMP 2024 design guide overview <https://www.energy.gov/cmei/femp/articles/best-practices-guide-energy-efficient-data-center-design>`_
  supports coordinated IT, power and cooling review; it does not prescribe the
  illustrative hall geometry or area allowance.
* `WBDG commissioning roles <https://legacy.wbdg.org/building-commissioning/roles-and-responsibilities-commissioning-process>`_
  informs owner requirements, basis of design, documented issues and handover.
* Existing TIA and buildingSMART context helps frame telecom and model-exchange
  evidence requests. Full normative standards were not retrieved for this addition.

Public DOE and WBDG overview material was checked on 11 November 2026. Sources
are reading context, not evidence that the synthetic campus satisfies a standard.
Only tool protocol, arithmetic and citation IDs are validated automatically;
the semantic truth of a live planner's narrative is not verified.

Energy Data Insights can supply climate, grid and renewable-supply inputs through
separate workflows. This example does not execute its connectors or claim a current
repository inventory. Detailed thermal, electrical, hydraulic and acoustic models
belong in ``datacenter-simulator``; this addition requests those analyses without
pretending to execute them.

Validation
----------

Tests cover all six groups, reuse of the fourteen original roles, the three new
contracts, hall-by-hall rounding, independent slot/area limits, nonfinite inputs,
immutable handoffs, blocked dependencies, premature submissions, full delivery
context, retained evidence gaps and repeatable CLI exports. The gallery executes
during the strict documentation build. These checks do not validate a real facility
or demonstrate benefit from a live language model.
