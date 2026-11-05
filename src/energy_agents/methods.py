"""Transactional edits of EnergyPlus epJSON fields, without a simulation claim."""

import math
from copy import deepcopy

GLAZING = "WindowMaterial:SimpleGlazingSystem"
LIGHT_FIELDS = {
    "lightinglevel": "lighting_level",
    "watts/area": "watts_per_floor_area",
    "watts/person": "watts_per_person",
}


def number(value, *, positive=False):
    """Validate finite physical scalar inputs (booleans are not numbers here)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a finite numeric value")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError("Expected a finite, physically admissible value")
    return float(value)


def active_field(obj):
    """Resolve only the active Lights design-power field."""
    method = obj.get("design_level_calculation_method", "LightingLevel").lower()
    if method not in LIGHT_FIELDS:
        raise ValueError(f"Unsupported lighting calculation method: {method}")
    field = LIGHT_FIELDS[method]
    number(obj.get(field))
    if not obj.get("schedule_name"):
        raise ValueError("Lights object lacks a schedule reference")
    return field


def targets(model, kind):
    objects = model.get(kind, {})
    if not isinstance(objects, dict) or not objects:
        raise ValueError(f"No {kind} objects found")
    return objects


def edit_windows(model, u_factor=1.5):
    """Set every simple glazing U-factor in W/(m² K); return a new model."""
    value = number(u_factor, positive=True)
    result = deepcopy(model)
    for obj in targets(result, GLAZING).values():
        obj["u_factor"] = value
    return result


def edit_lighting(model, reduction=0.30):
    """Reduce active design input; preserve schedules, inactive fields and other objects."""
    reduction = number(reduction)
    if reduction > 1:
        raise ValueError("Reduction must lie in [0, 1]")
    result = deepcopy(model)
    for obj in targets(result, "Lights").values():
        field = active_field(obj)
        obj[field] = number(obj[field]) * (1 - reduction)
    return result


def verify_task(before, after, task):
    """Check exact task effects and preservation, not NECB or EnergyPlus validity."""
    if task not in {"windows", "lighting"}:
        raise ValueError("Unknown task")
    expected = edit_windows(before) if task == "windows" else edit_lighting(before)
    if after != expected:
        raise ValueError("Task postcondition failed: missing edits or unrelated changes")
