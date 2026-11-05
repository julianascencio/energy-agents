"""
Orchestrator: successful handoff and blocked implementation
======================================================================

Synthetic runner fixtures show how customer discovery gates implementation.
These fixtures do not call LLMs or generate code; use run_delivery_team with the
specialist modules for real proposal composition. No deployment occurs.
"""

from energy_agents.orchestrator import AgentTask, run_orchestrator

TASKS = [
    AgentTask("pilot", "ai_forward_deployed_engineer", payload={"goal": "Solar alarm triage"}),
    AgentTask("code", "python_ml_engineer", ("pilot",)),
]


def pilot(context):
    return {
        "success": True,
        "python_task": "Implement a read-only evidence adapter",
        "evidence": "synthetic fixture",
    }


def code(context):
    return {
        "success": True,
        "received_task": context["upstream"]["pilot"]["python_task"],
        "evidence": "synthetic fixture; no code generated or tests run",
    }


completed = run_orchestrator(
    TASKS,
    {"ai_forward_deployed_engineer": pilot, "python_ml_engineer": code},
)
blocked = run_orchestrator(
    TASKS,
    {
        "ai_forward_deployed_engineer": lambda context: {"success": False},
        "python_ml_engineer": code,
    },
)
assert completed["success"]
assert blocked["states"]["code"] == "blocked"
print("Successful routing:", completed["states"])
print("Failed prerequisite:", blocked["states"])
print("Validation:", completed["validation"])
