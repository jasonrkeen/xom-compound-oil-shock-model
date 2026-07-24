from __future__ import annotations

import csv
from pathlib import Path

from .models import Scenario


def load_scenarios(path: Path | None = None) -> list[Scenario]:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "scenarios.csv"

    scenarios: list[Scenario] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            scenarios.append(
                Scenario(
                    name=row["name"],
                    description=row["description"],
                    horizon_days=int(row["horizon_days"]),
                    hormuz_disruption_share=float(row["hormuz_disruption_share"]),
                    bypass_utilization=float(row["bypass_utilization"]),
                    russian_crude_loss_mbd=float(row["russian_crude_loss_mbd"]),
                    russian_product_loss_mbd=float(row["russian_product_loss_mbd"]),
                    cpc_loss_mbd=float(row["cpc_loss_mbd"]),
                    other_supply_loss_mbd=float(row["other_supply_loss_mbd"]),
                    policy_offset_mbd=float(row["policy_offset_mbd"]),
                    demand_destruction_pct=float(row["demand_destruction_pct"]),
                    xom_volume_loss_pct=float(row["xom_volume_loss_pct"]),
                    base_recession_probability=float(
                        row["base_recession_probability"]
                    ),
                    geopolitical_volatility=float(row["geopolitical_volatility"]),
                )
            )
    return scenarios
