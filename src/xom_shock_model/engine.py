from __future__ import annotations

from dataclasses import replace

import numpy as np

from .models import Assumptions, MarketData, Scenario


def _clip_probability(value: float) -> float:
    return float(np.clip(value, 0.0, 0.98))


def evaluate_scenario(
    scenario: Scenario,
    market: MarketData,
    assumptions: Assumptions,
) -> dict[str, float | str]:
    gross_hormuz_loss = (
        assumptions.hormuz_transit_mbd * scenario.hormuz_disruption_share
    )
    bypass = min(gross_hormuz_loss, assumptions.available_bypass_mbd)
    bypass *= scenario.bypass_utilization
    demand_response = (
        assumptions.global_liquids_demand_mbd * scenario.demand_destruction_pct
    )
    total_physical_loss = (
        gross_hormuz_loss
        - bypass
        + scenario.russian_crude_loss_mbd
        + scenario.russian_product_loss_mbd
        + scenario.cpc_loss_mbd
        + scenario.other_supply_loss_mbd
    )
    net_supply_gap = max(
        0.0, total_physical_loss - scenario.policy_offset_mbd - demand_response
    )
    gap_pct = net_supply_gap / assumptions.global_liquids_demand_mbd

    brent_change_pct = (
        assumptions.short_run_price_linear * gap_pct
        + assumptions.short_run_price_convexity * gap_pct**2
    )
    brent_price = float(
        np.clip(
            market.brent_price * (1.0 + brent_change_pct),
            assumptions.minimum_brent_price,
            assumptions.maximum_brent_price,
        )
    )
    realized_brent_change = brent_price - market.brent_price
    wti_discount = max(4.0, market.brent_price - market.wti_price)
    wti_price = max(40.0, brent_price - wti_discount * (1.0 + 1.5 * gap_pct))

    product_tightness = (
        scenario.russian_product_loss_mbd
        + 0.25 * scenario.cpc_loss_mbd
        + 0.15 * gross_hormuz_loss
    )
    crack_change = 2.0 + 3.6 * product_tightness - 20.0 * scenario.demand_destruction_pct
    composite_crack = max(
        8.0, assumptions.baseline_composite_crack_usd + crack_change
    )

    horizon_factor = min(1.0, scenario.horizon_days / 365.0)
    oil_spike_pct = max(0.0, brent_price / market.brent_price - 1.0)
    recession_probability = _clip_probability(
        scenario.base_recession_probability
        + 0.30 * oil_spike_pct
        + 0.10 * scenario.geopolitical_volatility
        + 0.0010 * max(0, scenario.horizon_days - 90)
    )

    upstream_delta = (
        assumptions.annual_upstream_sensitivity_billion_per_brent_dollar
        * realized_brent_change
        * horizon_factor
    )
    volume_penalty = (
        assumptions.upstream_earnings_billion
        * scenario.xom_volume_loss_pct
        * (1.0 + 0.8 * scenario.geopolitical_volatility)
    )
    upstream_earnings = max(
        -5.0, assumptions.upstream_earnings_billion + upstream_delta - volume_penalty
    )

    refining_delta = (
        assumptions.annual_refining_sensitivity_billion_per_crack_dollar
        * crack_change
        * horizon_factor
    )
    throughput_penalty = (
        assumptions.energy_products_earnings_billion
        * 0.55
        * scenario.xom_volume_loss_pct
    )
    energy_products_earnings = max(
        -4.0,
        assumptions.energy_products_earnings_billion
        + refining_delta
        - throughput_penalty,
    )

    chemical_earnings = max(
        -2.5,
        assumptions.chemical_earnings_billion
        - horizon_factor
        * (1.3 * recession_probability + 0.8 * oil_spike_pct),
    )
    specialty_earnings = max(
        0.5,
        assumptions.specialty_earnings_billion
        + horizon_factor
        * (0.10 * crack_change - 0.75 * recession_probability),
    )
    corporate_earnings = (
        assumptions.corporate_earnings_billion
        - horizon_factor
        * (0.9 * scenario.geopolitical_volatility + 0.7 * recession_probability)
    )

    net_income = (
        upstream_earnings
        + energy_products_earnings
        + chemical_earnings
        + specialty_earnings
        + corporate_earnings
    )
    net_income_delta = net_income - assumptions.net_income_billion
    working_capital_penalty = (
        5.0 * oil_spike_pct * horizon_factor
        + 1.5 * scenario.geopolitical_volatility * horizon_factor
    )
    security_capex_penalty = (
        1.2 * scenario.geopolitical_volatility * horizon_factor
    )
    free_cash_flow = max(
        0.0,
        assumptions.free_cash_flow_billion
        + assumptions.earnings_to_fcf_conversion * net_income_delta
        - working_capital_penalty
        - security_capex_penalty,
    )
    eps = net_income / assumptions.shares_outstanding_billion

    baseline_eps = assumptions.net_income_billion / assumptions.shares_outstanding_billion
    baseline_pe = market.xom_price / baseline_eps
    multiple_compression = (
        0.30 * recession_probability
        + 0.13 * scenario.geopolitical_volatility
        + 0.08 * min(1.0, oil_spike_pct)
    )
    adjusted_pe = max(7.0, baseline_pe * (1.0 - multiple_compression))
    pe_value = max(0.0, eps * adjusted_pe)

    baseline_market_cap = (
        market.xom_price * assumptions.shares_outstanding_billion
    )
    baseline_fcf_yield = assumptions.free_cash_flow_billion / baseline_market_cap
    adjusted_fcf_yield = (
        baseline_fcf_yield
        + 0.017 * recession_probability
        + 0.010 * scenario.geopolitical_volatility
    )
    fcf_value = (
        free_cash_flow
        / adjusted_fcf_yield
        / assumptions.shares_outstanding_billion
    )

    factor_return = (
        0.42 * oil_spike_pct * horizon_factor
        + 0.12 * (crack_change / assumptions.baseline_composite_crack_usd)
        - 0.38 * recession_probability
        - 0.22 * scenario.xom_volume_loss_pct
        - 0.08 * scenario.geopolitical_volatility
    )
    factor_value = market.xom_price * max(0.35, 1.0 + factor_return)
    implied_price = 0.45 * pe_value + 0.35 * fcf_value + 0.20 * factor_value

    return {
        "scenario": scenario.name,
        "description": scenario.description,
        "horizon_days": scenario.horizon_days,
        "gross_hormuz_loss_mbd": gross_hormuz_loss,
        "bypass_mbd": bypass,
        "total_physical_loss_mbd": total_physical_loss,
        "demand_response_mbd": demand_response,
        "policy_offset_mbd": scenario.policy_offset_mbd,
        "net_supply_gap_mbd": net_supply_gap,
        "net_supply_gap_pct": gap_pct,
        "brent_price": brent_price,
        "wti_price": wti_price,
        "composite_crack": composite_crack,
        "recession_probability": recession_probability,
        "upstream_earnings_billion": upstream_earnings,
        "energy_products_earnings_billion": energy_products_earnings,
        "chemical_earnings_billion": chemical_earnings,
        "specialty_earnings_billion": specialty_earnings,
        "corporate_earnings_billion": corporate_earnings,
        "net_income_billion": net_income,
        "free_cash_flow_billion": free_cash_flow,
        "eps": eps,
        "adjusted_pe": adjusted_pe,
        "pe_value": pe_value,
        "fcf_value": fcf_value,
        "factor_value": factor_value,
        "implied_price_deterministic": implied_price,
        "deterministic_return_pct": implied_price / market.xom_price - 1.0,
    }


def draw_scenario(
    scenario: Scenario,
    rng: np.random.Generator,
) -> Scenario:
    def bounded(value: float, rel_sd: float, low: float, high: float) -> float:
        scale = max(abs(value) * rel_sd, rel_sd * 0.05)
        return float(np.clip(rng.normal(value, scale), low, high))

    return replace(
        scenario,
        hormuz_disruption_share=bounded(
            scenario.hormuz_disruption_share, 0.10, 0.05, 1.0
        ),
        bypass_utilization=bounded(scenario.bypass_utilization, 0.10, 0.0, 1.0),
        russian_crude_loss_mbd=bounded(
            scenario.russian_crude_loss_mbd, 0.25, 0.0, 2.5
        ),
        russian_product_loss_mbd=bounded(
            scenario.russian_product_loss_mbd, 0.25, 0.0, 2.5
        ),
        cpc_loss_mbd=bounded(scenario.cpc_loss_mbd, 0.25, 0.0, 2.2),
        other_supply_loss_mbd=bounded(
            scenario.other_supply_loss_mbd, 0.30, 0.0, 3.0
        ),
        policy_offset_mbd=bounded(scenario.policy_offset_mbd, 0.20, 0.0, 8.0),
        demand_destruction_pct=bounded(
            scenario.demand_destruction_pct, 0.20, 0.0, 0.20
        ),
        xom_volume_loss_pct=bounded(
            scenario.xom_volume_loss_pct, 0.30, 0.0, 0.20
        ),
        base_recession_probability=bounded(
            scenario.base_recession_probability, 0.20, 0.0, 0.95
        ),
        geopolitical_volatility=bounded(
            scenario.geopolitical_volatility, 0.15, 0.0, 1.0
        ),
    )


def run_monte_carlo(
    scenario: Scenario,
    market: MarketData,
    assumptions: Assumptions,
    draws: int,
    seed: int,
) -> list[dict[str, float | str | int]]:
    rng = np.random.default_rng(seed)
    results: list[dict[str, float | str | int]] = []
    for draw in range(draws):
        sampled_market = MarketData(
            as_of_date=market.as_of_date,
            xom_price=market.xom_price,
            brent_price=float(
                np.clip(rng.normal(market.brent_price, 3.0), 45.0, 180.0)
            ),
            wti_price=float(np.clip(rng.normal(market.wti_price, 3.0), 40.0, 175.0)),
            status=market.status,
            source_notes=market.source_notes,
        )
        sampled_assumptions = replace(
            assumptions,
            annual_upstream_sensitivity_billion_per_brent_dollar=float(
                np.clip(
                    rng.normal(
                        assumptions.annual_upstream_sensitivity_billion_per_brent_dollar,
                        0.08,
                    ),
                    0.25,
                    0.85,
                )
            ),
            annual_refining_sensitivity_billion_per_crack_dollar=float(
                np.clip(
                    rng.normal(
                        assumptions.annual_refining_sensitivity_billion_per_crack_dollar,
                        0.16,
                    ),
                    0.50,
                    1.70,
                )
            ),
        )
        row = evaluate_scenario(
            draw_scenario(scenario, rng), sampled_market, sampled_assumptions
        )
        results.append(
            {
                "scenario": scenario.name,
                "draw": draw + 1,
                "brent_price": float(row["brent_price"]),
                "net_supply_gap_mbd": float(row["net_supply_gap_mbd"]),
                "recession_probability": float(row["recession_probability"]),
                "net_income_billion": float(row["net_income_billion"]),
                "free_cash_flow_billion": float(row["free_cash_flow_billion"]),
                "implied_price": float(row["implied_price_deterministic"]),
            }
        )
    return results
