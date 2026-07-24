from __future__ import annotations

from dataclasses import replace

from src.xom_shock_model.engine import evaluate_scenario, run_monte_carlo
from src.xom_shock_model.models import Assumptions, MarketData
from src.xom_shock_model.scenarios import load_scenarios


def market() -> MarketData:
    return MarketData(
        as_of_date="2026-07-23",
        xom_price=156.89,
        brent_price=100.69,
        wti_price=92.19,
        status="test",
        source_notes=(),
    )


def test_all_scenarios_are_economically_bounded() -> None:
    assumptions = Assumptions()
    for scenario in load_scenarios():
        result = evaluate_scenario(scenario, market(), assumptions)
        assert 0.0 <= result["recession_probability"] <= 0.98
        assert assumptions.minimum_brent_price <= result["brent_price"]
        assert result["brent_price"] <= assumptions.maximum_brent_price
        assert result["implied_price_deterministic"] > 0
        assert result["free_cash_flow_billion"] >= 0


def test_larger_unoffset_supply_loss_raises_brent() -> None:
    scenario = load_scenarios()[0]
    severe = replace(
        scenario,
        hormuz_disruption_share=min(1.0, scenario.hormuz_disruption_share + 0.20),
        policy_offset_mbd=max(0.0, scenario.policy_offset_mbd - 1.0),
    )
    base_result = evaluate_scenario(scenario, market(), Assumptions())
    severe_result = evaluate_scenario(severe, market(), Assumptions())
    assert severe_result["brent_price"] > base_result["brent_price"]


def test_company_volume_loss_reduces_xom_value() -> None:
    scenario = load_scenarios()[1]
    lower_loss = replace(scenario, xom_volume_loss_pct=0.0)
    higher_loss = replace(scenario, xom_volume_loss_pct=0.15)
    assumptions = Assumptions()
    low = evaluate_scenario(lower_loss, market(), assumptions)
    high = evaluate_scenario(higher_loss, market(), assumptions)
    assert high["net_income_billion"] < low["net_income_billion"]
    assert high["implied_price_deterministic"] < low["implied_price_deterministic"]


def test_demand_response_reduces_supply_gap() -> None:
    scenario = load_scenarios()[2]
    weak_response = replace(scenario, demand_destruction_pct=0.01)
    strong_response = replace(scenario, demand_destruction_pct=0.15)
    assumptions = Assumptions()
    weak = evaluate_scenario(weak_response, market(), assumptions)
    strong = evaluate_scenario(strong_response, market(), assumptions)
    assert strong["net_supply_gap_mbd"] < weak["net_supply_gap_mbd"]
    assert strong["brent_price"] < weak["brent_price"]


def test_monte_carlo_is_reproducible() -> None:
    scenario = load_scenarios()[0]
    assumptions = Assumptions()
    first = run_monte_carlo(scenario, market(), assumptions, 100, 123)
    second = run_monte_carlo(scenario, market(), assumptions, 100, 123)
    assert first == second
