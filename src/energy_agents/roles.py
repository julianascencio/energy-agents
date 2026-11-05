"""Professional role contracts, independent of model provider and plant identity."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RoleSpec:
    """Executable role contract for the initial advisory PV workflow."""

    id: str
    title: str
    mandate: str
    inputs: tuple[str, ...]
    tool: str
    output: str
    acceptance: str
    technology: str = "solar_pv"
    authority: str = "advisory_only"

    def as_dict(self):
        return asdict(self)


PV_ROLES = (
    RoleSpec(
        "performance_engineer",
        "Performance Engineer",
        "Quantify observed energy deficits without inferring unobserved causes.",
        ("case",),
        "assess_performance",
        "performance",
        "Deficits, surplus and excluded intervals reconcile to input energy.",
    ),
    RoleSpec(
        "reliability_engineer",
        "Reliability Engineer",
        "Separate fault-associated losses from curtailment and unresolved losses.",
        ("case", "performance"),
        "assess_reliability",
        "reliability",
        "Every fault association cites evidence; association is not proven causation.",
    ),
    RoleSpec(
        "commercial_asset_manager",
        "Commercial Asset Manager",
        "Value historical deficits and an explicitly conditional recovery scenario.",
        ("case", "performance", "reliability"),
        "assess_commercial",
        "commercial",
        "Interval prices and signed revenues reconcile; no annual extrapolation.",
    ),
    RoleSpec(
        "maintenance_planner",
        "Maintenance Planner",
        "Recommend inspection and evidence collection before committing interventions.",
        ("case", "reliability", "commercial"),
        "plan_maintenance",
        "maintenance",
        "Actions are proposals with evidence, dependencies and human approval required.",
    ),
    RoleSpec(
        "technical_asset_manager",
        "Technical Asset Manager",
        "Assemble the case decision, unresolved issues and next human action.",
        ("performance", "reliability", "commercial", "maintenance"),
        "summarise_asset",
        "asset_summary",
        "Incomplete coverage and unresolved losses remain visible in the decision.",
    ),
)


PYTHON_ENGINEER = RoleSpec(
    id="python_ml_engineer",
    title="Principal Python, Data Science and ML Engineer",
    mandate="Turn energy business questions into reproducible, tested Python contributions.",
    inputs=("task", "repository_context"),
    tool="propose_files",
    output="source_bundle",
    acceptance="Source, independent tests and runnable example; external checks still required.",
    technology="cross_technology",
    authority="propose_code_only",
)

def role_catalogue(*, include_engineering=False):
    """Return PV contracts; optionally include the independent coding workflow."""
    roles = (*PV_ROLES, PYTHON_ENGINEER) if include_engineering else PV_ROLES
    return [role.as_dict() for role in roles]
