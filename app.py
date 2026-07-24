from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.xom_shock_model.data import collect_market_data
from src.xom_shock_model.engine import evaluate_scenario, run_monte_carlo
from src.xom_shock_model.models import Assumptions
from src.xom_shock_model.scenarios import load_scenarios

st.set_page_config(
    page_title="XOM Oil Shock Stress Model",
    page_icon="🛢️",
    layout="wide",
)

st.title("XOM Compound Oil Shock Equity Stress Model")
st.caption(
    "Conditional scenario analysis - not a geopolitical forecast or investment recommendation."
)

assumptions = Assumptions()
market = collect_market_data(use_live_data=False)
scenarios = load_scenarios()
scenario_names = [scenario.name for scenario in scenarios]
selected_name = st.sidebar.selectbox("Starting scenario", scenario_names)
selected = next(item for item in scenarios if item.name == selected_name)

st.sidebar.header("Shock controls")
horizon = st.sidebar.slider("Duration (days)", 30, 365, selected.horizon_days, 15)
hormuz = st.sidebar.slider(
    "Hormuz disruption", 0.0, 1.0, selected.hormuz_disruption_share, 0.05
)
russian_crude = st.sidebar.slider(
    "Russian crude loss (mb/d)", 0.0, 2.5, selected.russian_crude_loss_mbd, 0.05
)
russian_products = st.sidebar.slider(
    "Russian product loss (mb/d)", 0.0, 2.5, selected.russian_product_loss_mbd, 0.05
)
cpc = st.sidebar.slider("CPC loss (mb/d)", 0.0, 2.2, selected.cpc_loss_mbd, 0.05)
policy = st.sidebar.slider(
    "Policy offset (mb/d)", 0.0, 8.0, selected.policy_offset_mbd, 0.10
)
demand = st.sidebar.slider(
    "Demand destruction", 0.0, 0.20, selected.demand_destruction_pct, 0.005
)
xom_loss = st.sidebar.slider(
    "XOM volume loss", 0.0, 0.20, selected.xom_volume_loss_pct, 0.005
)

custom = selected.__class__(
    **{
        **selected.to_dict(),
        "name": f"Custom - {selected.name}",
        "horizon_days": horizon,
        "hormuz_disruption_share": hormuz,
        "russian_crude_loss_mbd": russian_crude,
        "russian_product_loss_mbd": russian_products,
        "cpc_loss_mbd": cpc,
        "policy_offset_mbd": policy,
        "demand_destruction_pct": demand,
        "xom_volume_loss_pct": xom_loss,
    }
)
result = evaluate_scenario(custom, market, assumptions)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Modeled Brent", f"${result['brent_price']:,.2f}")
col2.metric("Net supply gap", f"{result['net_supply_gap_mbd']:.2f} mb/d")
col3.metric("Net income", f"${result['net_income_billion']:.1f}B")
col4.metric(
    "Deterministic XOM value",
    f"${result['implied_price_deterministic']:,.2f}",
    f"{result['deterministic_return_pct']:.1%}",
)

st.subheader("Segment earnings bridge")
segment_df = pd.DataFrame(
    {
        "Segment": [
            "Upstream",
            "Energy Products",
            "Chemical",
            "Specialty",
            "Corporate",
        ],
        "Baseline": [
            assumptions.upstream_earnings_billion,
            assumptions.energy_products_earnings_billion,
            assumptions.chemical_earnings_billion,
            assumptions.specialty_earnings_billion,
            assumptions.corporate_earnings_billion,
        ],
        "Scenario": [
            result["upstream_earnings_billion"],
            result["energy_products_earnings_billion"],
            result["chemical_earnings_billion"],
            result["specialty_earnings_billion"],
            result["corporate_earnings_billion"],
        ],
    }
).set_index("Segment")
st.bar_chart(segment_df)

if st.button("Run 2,000-draw Monte Carlo"):
    with st.spinner("Simulating conditional valuation range..."):
        draws = pd.DataFrame(
            run_monte_carlo(custom, market, assumptions, draws=2000, seed=20260723)
        )
    q10, q50, q90 = draws["implied_price"].quantile([0.10, 0.50, 0.90])
    st.success(
        f"Conditional XOM range: P10 ${q10:,.2f} | "
        f"Median ${q50:,.2f} | P90 ${q90:,.2f}"
    )
    st.line_chart(
        draws["implied_price"].sort_values(ignore_index=True),
        y_label="Implied price",
    )

st.divider()
st.caption(
    "The model separates crude-supply losses, refined-product losses, company "
    "volume exposure, and macroeconomic feedback. See docs/methodology.md for "
    "definitions and limitations."
)
