from copy import deepcopy

import pytest

from energy_agents.business.nonfirm import reference_case, run_workflow, screen_nonfirm


def test_hand_calculated_reference():
    r = screen_nonfirm(reference_case())
    assert r["annual"]["curtailed_mwh"] == 4800
    assert r["annual"]["lost_contribution_usd"] == 2400000
    assert r["annual"]["avoided_energy_cost_usd"] == 1920000
    assert r["events"] == 2 and r["annual"]["restart_cost_usd"] == 40000
    assert r["annual_net_benefit_usd"] == 580000
    assert r["incremental_npv_usd"] == pytest.approx(1891847.21, abs=0.01)


def test_threshold_contiguous_events_and_negative_prices():
    c = reference_case()
    c["assumptions"].update(discount_rate=0, years=1)
    c["periods"] = [
        {"hours": 10, "price_usd_mwh": 250},
        {"hours": 10, "price_usd_mwh": 251},
        {"hours": 8740, "price_usd_mwh": -30},
    ]
    r = screen_nonfirm(c)
    assert r["events"] == 1 and r["annual"]["curtailed_mwh"] == 800
    assert r["annual"]["avoided_energy_cost_usd"] == 200400
    assert r["annual_net_benefit_usd"] == 880400
    assert r["incremental_npv_usd"] == -1119600
    c["assumptions"]["annual_avoided_firm_cost_usd"] = r["break_even_annual_avoided_firm_cost_usd"]
    assert screen_nonfirm(c)["incremental_npv_usd"] == pytest.approx(0)


def test_zero_tranche_and_all_year_event():
    c = reference_case()
    c["assumptions"]["nonfirm_mw"] = 0
    with pytest.raises(ValueError, match="No avoided"):
        screen_nonfirm(c)
    c["assumptions"]["annual_avoided_firm_cost_usd"] = 0
    r = screen_nonfirm(c)
    assert r["events"] == 0 and r["annual"]["curtailed_mwh"] == 0
    assert r["annual_net_benefit_usd"] == -100000  # committed costs not silently removed
    c = reference_case()
    for p in c["periods"]:
        p["price_usd_mwh"] = 250
    assert screen_nonfirm(c)["events"] == 1


@pytest.mark.parametrize(
    "key,value",
    [
        ("nonfirm_mw", 41),
        ("flexible_mw", 101),
        ("load_mw", True),
        ("discount_rate", float("nan")),
        ("years", 1.2),
        ("restart_usd_event", -1),
    ],
)
def test_input_bounds(key, value):
    c = reference_case()
    c["assumptions"][key] = value
    with pytest.raises(ValueError):
        screen_nonfirm(c)


def test_time_evidence_handoff_and_isolation():
    c = reference_case()
    original = deepcopy(c)
    r = run_workflow(c)
    assert r["success"] and r["results"]["finance"]["report"] == screen_nonfirm(c)
    assert c == original
    assert r["results"]["finance"]["report"]["eligible_for_service"] is None
    for source_change in [
        {"status": "effective"},
        {"url": "file:///tmp/a"},
        {"url": "https://example.org/forged"},
        {"publication_date": "2026-11-16"},
    ]:
        c = reference_case()
        c["source"].update(source_change)
        assert run_workflow(c)["states"] == {"evidence": "failed", "finance": "blocked"}
    c = reference_case()
    c["periods"][0]["hours"] += 1
    with pytest.raises(ValueError, match="8760"):
        screen_nonfirm(c)


@pytest.mark.parametrize(
    "action",
    [
        {"tool": "set_load", "arguments": {}},
        {"tool": "delegate", "arguments": {"task_id": "finance"}},
    ],
)
def test_no_controls_or_premature_handoff(action):
    class Planner:
        def next_action(self, context):
            return action

    run = run_workflow(reference_case(), Planner())
    assert not run["success"] and all(t["status"] == "rejected" for t in run["trace"])
