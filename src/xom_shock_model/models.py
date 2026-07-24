from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MarketData:
    as_of_date: str
    xom_price: float
    brent_price: float
    wti_price: float
    status: str
    source_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_notes"] = list(self.source_notes)
        return data


@dataclass(frozen=True)
class Assumptions:
    # Physical-market baseline
    global_liquids_demand_mbd: float = 103.0
    hormuz_transit_mbd: float = 20.0
    available_bypass_mbd: float = 2.6

    # ExxonMobil 2025 financial baseline, USD billions unless stated
    upstream_earnings_billion: float = 21.4
    energy_products_earnings_billion: float = 7.423
    chemical_earnings_billion: float = 0.800
    specialty_earnings_billion: float = 2.857
    corporate_earnings_billion: float = -3.590
    net_income_billion: float = 28.844
    free_cash_flow_billion: float = 26.131
    production_mboed: float = 4.736
    shares_outstanding_billion: float = 4.486

    # Calibrated sensitivities
    annual_upstream_sensitivity_billion_per_brent_dollar: float = 0.52
    annual_refining_sensitivity_billion_per_crack_dollar: float = 1.10
    earnings_to_fcf_conversion: float = 0.78
    baseline_composite_crack_usd: float = 24.0
    short_run_price_linear: float = 5.0
    short_run_price_convexity: float = 35.0
    maximum_brent_price: float = 240.0
    minimum_brent_price: float = 45.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    horizon_days: int
    hormuz_disruption_share: float
    bypass_utilization: float
    russian_crude_loss_mbd: float
    russian_product_loss_mbd: float
    cpc_loss_mbd: float
    other_supply_loss_mbd: float
    policy_offset_mbd: float
    demand_destruction_pct: float
    xom_volume_loss_pct: float
    base_recession_probability: float
    geopolitical_volatility: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
