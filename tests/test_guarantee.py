from copy import deepcopy

import pytest

from energy_agents.business.guarantee import reference_case, run_workflow, screen_guarantee


def test_hand_calculated_ledger():
    r = screen_guarantee(reference_case())
    b = r["offers"]["baseline"]
    a = r["offers"]["alternative"]
    assert b["guarantee_face_nis"] == 167000000
    assert b["restricted_cash_nis"] == 167000000
    assert b["upfront_fees_nis"] == 1670000
    assert b["opportunity_cost_nis"] == 13360000
    assert b["expected_net_call_loss_nis"] == 1336000
    assert b["total_economic_cost_nis"] == 16366000
    assert a["total_economic_cost_nis"] == 9886000
    assert a["initial_cash_required_nis"] == 46960000
    assert a["additional_cash_on_full_call_nis"] == 125250000
    assert a["full_call_cash_including_initial_nis"] == 172210000
    assert r["economic_cost_reduction_nis"] == 6480000
    assert r["restricted_cash_released_nis"] == 125250000
    assert a["initial_budget_feasible"] and not b["initial_budget_feasible"]


def test_break_even_and_identical_offers():
    c = reference_case()
    r = screen_guarantee(c)
    c["offers"]["alternative"]["annual_fee_rate"] = r["alternative_break_even_annual_fee_rate"]
    assert screen_guarantee(c)["economic_cost_reduction_nis"] == pytest.approx(0, abs=1e-6)
    c["offers"]["alternative"] = deepcopy(c["offers"]["baseline"])
    assert screen_guarantee(c)["economic_cost_reduction_nis"] == 0


def test_call_loss_is_not_peak_liquidity():
    c = reference_case()
    c["assumptions"].update(call_probability=1, net_loss_fraction=0)
    a = screen_guarantee(c)["offers"]["alternative"]
    assert a["expected_net_call_loss_nis"] == 0
    assert a["additional_cash_on_full_call_nis"] == 125250000
    c["assumptions"]["net_loss_fraction"] = 1
    assert screen_guarantee(c)["offers"]["alternative"]["expected_net_call_loss_nis"] == 167000000


def test_zero_share_and_zero_collateral():
    c = reference_case()
    c["offers"]["alternative"]["collateral_fraction"] = 0
    assert (
        screen_guarantee(c)["offers"]["alternative"]["additional_cash_on_full_call_nis"]
        == 167000000
    )
    c["assumptions"]["sponsor_share"] = 0
    r = screen_guarantee(c)
    assert r["alternative_break_even_annual_fee_rate"] is None
    assert r["offers"]["alternative"]["total_economic_cost_nis"] == 200000


@pytest.mark.parametrize(
    "key,value",
    [
        ("years", 0),
        ("years", float("nan")),
        ("sponsor_share", True),
        ("call_probability", 1.01),
        ("net_loss_fraction", -1),
        ("initial_liquidity_budget_nis", -1),
    ],
)
def test_bad_assumptions(key, value):
    c = reference_case()
    c["assumptions"][key] = value
    with pytest.raises(ValueError):
        screen_guarantee(c)


def test_bad_offer_and_source_block_handoff():
    for key, value in [
        ("collateral_fraction", 1.1),
        ("annual_fee_rate", float("inf")),
        ("setup_fee_nis", -1),
    ]:
        c = reference_case()
        c["offers"]["alternative"][key] = value
        assert run_workflow(c)["states"] == {"evidence": "failed", "finance": "blocked"}
    for change in [
        {"status": "approved"},
        {"publication_date": "2026-11-17"},
        {"url": "file:///secret"},
    ]:
        c = reference_case()
        c["source"].update(change)
        assert run_workflow(c)["states"] == {"evidence": "failed", "finance": "blocked"}


def test_parity_and_isolation():
    c = reference_case()
    original = deepcopy(c)
    r = run_workflow(c)
    assert c == original
    assert r["success"] and r["results"]["finance"]["report"] == screen_guarantee(c)
    assert not r["results"]["finance"]["report"]["banking_authorized"]


@pytest.mark.parametrize(
    "action",
    [
        {"tool": "issue_guarantee", "arguments": {}},
        {"tool": "delegate", "arguments": {"task_id": "finance"}},
    ],
)
def test_permissions(action):
    class Planner:
        def next_action(self, context):
            return action

    r = run_workflow(reference_case(), Planner())
    assert not r["success"] and all(t["status"] == "rejected" for t in r["trace"])
