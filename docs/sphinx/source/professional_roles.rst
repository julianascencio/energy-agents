Professional roles and agent architecture
=============================================

The initial implementation is an **advisory PV operations team**. Five executable
role contracts share a versioned case, use deterministic tools and undergo an
independent arithmetic/contract review. The wider lifecycle below is a design
catalogue, not a claim that all these agents are implemented.

Role configuration combines professional responsibility, technology expertise,
project context, approved tools and authority limits. Plant identity is separate
from professional expertise. The same role can serve many plants; persistent plant
memory and multi-tenant storage are future work.

Lifecycle catalogue
-----------------------

.. list-table:: Candidate professional roles
   :header-rows: 1
   :widths: 20 45 35

   * - Stage
     - Roles
     - Deliverables
   * - Strategy and origination
     - Market Analyst; Origination Manager; Portfolio Strategist
     - Market screening and opportunity pipeline
   * - Site and land
     - GIS/Siting Specialist; Land Acquisition Manager; Stakeholder Engagement Specialist
     - Site ranking, land-rights checklist and stakeholder register
   * - Resource and feasibility
     - Resource Assessment Engineer; Energy Yield Engineer; Feasibility Engineer
     - Production estimates, uncertainty and feasibility report
   * - Environmental and permitting
     - Environmental Specialist; Permitting Manager; Biodiversity Specialist; Social Impact Specialist
     - Constraints, dependencies and mitigation plan
   * - Grid connection
     - Grid Connection Engineer; Power Systems Engineer; Protection Engineer
     - Connection options, study specifications and evidence gaps
   * - Design
     - System Design Engineer; Electrical Engineer; Civil/Structural Engineer; Controls/SCADA Engineer
     - Layouts, sizing, specifications and monitoring architecture
   * - Commercial and financing
     - Project Finance Analyst; PPA/Offtake Specialist; Investment Analyst; Insurance/Risk Specialist
     - Scenarios, contract comparisons and investment memorandum
   * - Due diligence
     - Owner's Engineer; Lender's Technical Adviser; Technical Due Diligence Specialist
     - Independent challenge and risk register
   * - Procurement and contracting
     - Procurement Engineer; Supply Chain Manager; Contracts Specialist
     - Tenders, supplier comparison and obligations
   * - Construction
     - Construction Manager; Project Controls Engineer; QA/QC Engineer; HSE Specialist
     - Schedule, costs, inspection plans and nonconformities
   * - Commissioning
     - Commissioning Engineer; Acceptance Test Engineer; Handover Manager
     - Test plans, punch lists and handover review
   * - Operations and maintenance
     - Operations Engineer; Maintenance Planner; Reliability Engineer; Field Service Specialist
     - Triage, inspections and maintenance recommendations
   * - Performance and asset management
     - Performance Engineer; Technical Asset Manager; Commercial Asset Manager; Warranty Specialist
     - Loss accounting, evidence gaps and commercial assessment
   * - Market participation
     - Forecasting Analyst; Energy Trader; Dispatch Optimisation Engineer; Settlement Analyst
     - Forecasts, bidding scenarios and reconciliation
   * - Life extension and repowering
     - Lifetime/Reliability Specialist; Repowering Engineer; Investment Analyst
     - Remaining-life scenarios and investment cases
   * - Decommissioning
     - Decommissioning Engineer; Recycling Specialist; Environmental Restoration Specialist
     - Removal, material recovery and restoration plans

Project Manager, Document Controller, Data Engineer, Cybersecurity Specialist and
Regulatory/Legal Specialist span stages. Repeated roles retain one identity.

Technology expertise is composable: solar PV, onshore/offshore wind, BESS,
hydropower, geothermal, bioenergy and hybrid plants. Only solar PV is executable
in this workflow. BESS is enabling storage, not itself renewable generation.

Other agent families
------------------------

* **Capabilities:** research, document interpretation, geospatial analysis,
  forecasting, optimisation and simulation. Fixed calculations remain tools.
* **Assets:** portfolio, plant and equipment context. This release has a case
  snapshot, not an autonomous persistent asset agent.
* **Coordinators:** manage dependencies and handoffs. Implemented as a bounded runner.
* **Evidence review:** provenance, uncertainty and reproducibility. Implemented
  here as deterministic accounting/contract checks, not source authentication.
* **Monitoring:** initiate investigations on events. Planned, not connected to SCADA.
* **Research and engineering:** literature-to-method-to-benchmark workflows. Planned.
* **Stakeholder simulation:** developer, lender, regulator, OEM and community
  perspectives. Planned; simulated actors never represent actual authorisation.

Initial role contracts
--------------------------

The executable source of truth is :func:`energy_agents.roles.role_catalogue`.
Each contract specifies mandate, required inputs, tool, output, acceptance criteria,
technology and advisory authority.

#. **Performance Engineer:** compare baseline and meter energy; preserve missing data.
#. **Reliability Engineer:** associate deficits with supplied event evidence; keep
   unresolved energy visible and avoid causal claims.
#. **Commercial Asset Manager:** value interval deficits and a conditional recovery scenario.
#. **Maintenance Planner:** propose inspections and evidence collection with preconditions.
#. **Technical Asset Manager:** consolidate open issues and request human review.

The commercial assessment precedes maintenance planning so financial context is
available. All tools share the same original input snapshot. No tool sends a work
order, trades energy, signs a contract or controls a plant.

Design basis
----------------

The lifecycle taxonomy is a project design derived from general development
frameworks, not an official occupation classification or certification:

* `NREL, A Framework for Project Development in the Renewable Energy Sector
  <https://docs.nrel.gov/docs/fy13osti/57963.pdf>`_: site, resource, offtake,
  permits, technology, team and capital.
* `DOE, Large-Scale Renewable Energy Guide presentation
  <https://www1.eere.energy.gov/femp/pdfs/fupwg_spring13_gustafson2.pdf>`_:
  developer, owner and financier perspectives across development and operations.

Neither source validates this software or the synthetic example's assumptions.
