"""
AI forward-deployed engineer: solar O&M copilot pilot
======================================================================

Synthetic customer discovery becomes a staged AI delivery plan and an explicit
Python engineering handoff. Scripted replay demonstrates the protocol; there is
no live LLM, connected customer system, measured saving or production deployment.
"""

from energy_agents.forward_deployed import run_forward_deployed_engineer

BRIEF = {
    "problem": "Synthetic solar operator needs faster evidence-backed alarm triage.",
    "users": "O&M analysts review alarms and prepare maintenance recommendations.",
    "evidence": "Synthetic scenario: 100 cases/week, assumed 20 minutes/case; not measured.",
    "constraints": "Read-only pilot; no SCADA control or automatic work-order creation.",
}

REPORTS = {
    "discovery": {
        "user_workflow": "Review alarm, retrieve intervals, inspect evidence, draft recommendation.",
        "business_kpi": "Median analyst minutes per correctly resolved case; analyst lead owns KPI.",
        "baseline": "Measure manual triage on the same held-out cases before claiming savings.",
        "constraints": "Read-only, tenant-scoped inputs; no credentials in prompts or source.",
        "unknowns": "Actual case distribution, API contract, tariffs and approval owner unknown.",
    },
    "solution": {
        "architecture": "Deterministic evidence retrieval plus optional grounded LLM draft.",
        "integrations": "Mock alarm CSV and time-series adapter; live CMMS/SCADA APIs unverified.",
        "data_contract": "site_id, UTC interval, alarm code, MW, quality and source ID; null != zero.",
        "build_vs_buy": "Compare rule-based report to hosted/local LLM; avoid agents if no gain.",
        "python_task": "Implement typed read-only alarm/evidence adapters and a grounded triage "
        "draft pipeline with mocked transports, tenant filters and offline example.",
        "acceptance_criteria": "Reject cross-tenant queries; retain missing values; every factual "
        "draft claim cites a supplied source; no write endpoints available.",
    },
    "evaluation": {
        "dataset_and_provenance": "Propose 100 deidentified held-out cases, split by site/time; "
        "freeze sources. Dataset not yet acquired.",
        "baseline_comparison": "Paired analyst review versus manual and rules-only baselines; "
        "measure correctness and time, report confidence intervals.",
        "quality_gates": "Proposed: >=95% supported factual claims, zero cross-tenant disclosures; "
        "reject unsupported recommendations. Owner must approve thresholds.",
        "latency_and_cost_budget": "Proposed p95 <10 s and inference <EUR 0.10/case; "
        "track integration and analyst review costs separately.",
        "failure_cases": "Missing intervals, duplicate alarms, prompt injection in documents, "
        "API outage, stale evidence and unauthorized site request.",
        "human_review": "Analyst approves every recommendation; critical cases escalate.",
    },
    "rollout": {
        "pilot_scope": "Proposed two-week shadow pilot on one consenting site after evaluation.",
        "monitoring": "Track citation failures, latency, cost/case, drift and analyst overrides.",
        "rollback": "Disable AI drafts and revert to existing manual triage; retain audit log.",
        "ownership": "Proposed: customer analyst lead owns acceptance; platform team owns support.",
        "adoption": "Train analysts; collect rejection reasons; compare completed-case time.",
        "go_no_go": "NO-GO until measured gates pass, access review completes and owner signs off.",
    },
}


class DeliveryReplay:
    """Deterministic scenario policy, not a measured autonomous engineer."""

    def next_action(self, context):
        tool = context["allowed_tools"][0]
        return {
            "tool": tool,
            "arguments": REPORTS[tool.removeprefix("submit_")] if tool != "finish" else {},
        }


result = run_forward_deployed_engineer(
    BRIEF,
    {"repository_note": "Supply current Energy Data Insights APIs before implementation."},
    DeliveryReplay(),
)
assert result["success"]
print("Completed proposal stages:", list(result["reports"]))
print("Pilot decision:", result["reports"]["rollout"]["go_no_go"])
print("Python task:", result["python_handoff"]["task"])
print("Validation:", result["validation"])
print("Deployment authorized:", result["deployment_authorized"])
