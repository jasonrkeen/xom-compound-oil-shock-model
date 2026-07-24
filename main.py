from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from src.xom_shock_model.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the XOM compound oil-supply shock stress model."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the documented fallback market baseline without attempting live data.",
    )
    parser.add_argument(
        "--draws",
        type=int,
        default=None,
        help="Monte Carlo draws per scenario (overrides MONTE_CARLO_DRAWS).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (overrides MONTE_CARLO_SEED).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for CSV, chart, JSON, and PDF outputs.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    draws = args.draws or int(os.getenv("MONTE_CARLO_DRAWS", "10000"))
    seed = args.seed or int(os.getenv("MONTE_CARLO_SEED", "20260723"))

    result = run_pipeline(
        output_dir=args.output_dir,
        use_live_data=not args.offline,
        draws=draws,
        seed=seed,
    )

    print("=" * 72)
    print("XOM Compound Oil Shock Equity Stress Model")
    print("=" * 72)
    print(f"Market data status: {result.market_data.status}")
    print(f"Baseline XOM price: ${result.market_data.xom_price:,.2f}")
    print(f"Baseline Brent: ${result.market_data.brent_price:,.2f}/bbl")
    print(f"Scenarios evaluated: {len(result.summary)}")
    print(f"Monte Carlo draws per scenario: {draws:,}")
    print(f"Outputs written to: {args.output_dir.resolve()}")
    print()
    print(
        result.summary[
            [
                "scenario",
                "brent_price",
                "net_income_billion",
                "implied_price_p10",
                "implied_price_p50",
                "implied_price_p90",
                "probability_above_baseline",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
