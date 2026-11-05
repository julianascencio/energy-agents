"""Small synthetic EnergyPlus epJSON fragment; not an annual simulation model."""

from copy import deepcopy

FIXTURE = {
    "WindowMaterial:SimpleGlazingSystem": {
        "North glazing": {"u_factor": 2.8, "solar_heat_gain_coefficient": 0.4},
        "South glazing": {"u_factor": 3.2, "solar_heat_gain_coefficient": 0.5},
    },
    "Lights": {
        "Office": {
            "zone_or_zonelist_or_space_or_spacelist_name": "Office zone",
            "schedule_name": "Occupied",
            "design_level_calculation_method": "Watts/Area",
            "watts_per_floor_area": 10.0,
        },
        "Lobby": {
            "zone_or_zonelist_or_space_or_spacelist_name": "Lobby zone",
            "schedule_name": "Occupied",
            "design_level_calculation_method": "LightingLevel",
            "lighting_level": 500.0,
        },
        "Meeting": {
            "zone_or_zonelist_or_space_or_spacelist_name": "Meeting zone",
            "schedule_name": "Occupied",
            "design_level_calculation_method": "Watts/Person",
            "watts_per_person": 12.0,
        },
    },
    "Schedule:Constant": {"Occupied": {"hourly_value": 1.0}},
}


def synthetic_model():
    """Return an independent example model with all three lighting input methods."""
    return deepcopy(FIXTURE)
