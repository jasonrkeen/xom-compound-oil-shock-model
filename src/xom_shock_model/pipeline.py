from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .data import collect_market_data
from .engine import evaluate_scenario, run_monte_carlo
from .models import Assumptions, MarketData
from .reporting import build_pdf_report, create_charts, write_method_log
from .scenarios import load_scenarios


@dataclass(frozen=True)
class PipelineResult:
    market_data: MarketData
    summary: pd.DataFrame
    draws: pd.DataFrame
    output_dir: Path


def _summarize_draws(
    deterministic: pd.DataFrame,
    draws: pd.DataFrame,
    baseline_price: float,
) -> pd.DataFrame:
    stats = (
        draws.groupby("scenario", sort=False)
        .agg(
            implied_price_p10=("implied_price", lambda x: x.quantile(0.10)),
            implied_price_p50=("implied_price", "median"),
            implied_price_p90=("implied_price", lambda x: x.quantile(0.90)),
            simulated_brent_p50=("brent_price", "median"),
            simulated_net_income_p50=("net_income_billion", "median"),
            probability_above_baseline=(
                "implied_price",
                lambda x: (x > baseline_price).mean(),
            ),
        )
        .reset_index()
    )
    return deterministic.merge(stats, on="scenario", how="left", validate="one_to_one")


def run_pipeline(
    output_dir: Path,
    use_live_data: bool = True,
    draws: int = 10000,
    seed: int = 20260723,
) -> PipelineResult:
    if draws < 100:
        raise ValueError("draws must be at least 100")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = output_dir / "charts"
    pdf_dir = output_dir / "pdf"

    assumptions = Assumptions()
    market = collect_market_data(use_live_data=use_live_data)
    scenarios = load_scenarios()

    deterministic_rows = [
        evaluate_scenario(scenario, market, assumptions) for scenario in scenarios
    ]
    deterministic = pd.DataFrame(deterministic_rows)

    all_draws: list[dict[str, float | str | int]] = []
    for index, scenario in enumerate(scenarios):
        all_draws.extend(
            run_monte_carlo(
                scenario,
                market,
                assumptions,
                draws=draws,
                seed=seed + index * 100_003,
            )
        )
    draws_df = pd.DataFrame(all_draws)
    summary = _summarize_draws(deterministic, draws_df, market.xom_price)

    summary.to_csv(output_dir / "scenario_summary.csv", index=False)
    draws_df.to_csv(output_dir / "simulation_draws.csv", index=False)
    pd.DataFrame([market.to_dict()]).to_json(
        output_dir / "market_baseline.json", orient="records", indent=2
    )
    charts = create_charts(
        summary,
        draws_df,
        market,
        chart_dir,
        assumptions,
        scenarios[-1],
    )
    write_method_log(
        output_dir / "source_and_method_log.json",
        market,
        assumptions,
        scenarios,
        draws,
        seed,
    )
    build_pdf_report(
        pdf_dir / "xom_compound_oil_shock_report.pdf",
        summary,
        market,
        charts,
        draws,
    )
    return PipelineResult(
        market_data=market,
        summary=summary,
        draws=draws_df,
        output_dir=output_dir,
    )
