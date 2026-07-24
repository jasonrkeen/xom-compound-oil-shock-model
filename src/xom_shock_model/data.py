from __future__ import annotations

import os
from datetime import date
from typing import Iterable

import requests

from .models import MarketData

FALLBACK_XOM_PRICE = 156.89
FALLBACK_BRENT_PRICE = 100.69
FALLBACK_WTI_PRICE = 92.19
FALLBACK_DATE = "2026-07-23"


def _latest_fred_value(series_id: str, api_key: str) -> tuple[str, float]:
    response = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 10,
        },
        timeout=12,
    )
    response.raise_for_status()
    for item in response.json().get("observations", []):
        value = item.get("value")
        if value not in (None, "."):
            return str(item["date"]), float(value)
    raise ValueError(f"No usable FRED observation returned for {series_id}")


def _latest_xom_close() -> tuple[str, float]:
    import yfinance as yf

    history = yf.download(
        "XOM",
        period="10d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        timeout=12,
    )
    if history.empty:
        raise ValueError("No XOM observations returned")
    close = history["Close"].dropna()
    value = float(close.iloc[-1].item() if hasattr(close.iloc[-1], "item") else close.iloc[-1])
    return history.index[-1].date().isoformat(), value


def collect_market_data(use_live_data: bool = True) -> MarketData:
    values = {
        "xom": (FALLBACK_DATE, FALLBACK_XOM_PRICE),
        "brent": (FALLBACK_DATE, FALLBACK_BRENT_PRICE),
        "wti": (FALLBACK_DATE, FALLBACK_WTI_PRICE),
    }
    notes: list[str] = [
        "Fallback XOM and crude baselines are July 23, 2026 market closes."
    ]

    if not use_live_data:
        return MarketData(
            as_of_date=FALLBACK_DATE,
            xom_price=FALLBACK_XOM_PRICE,
            brent_price=FALLBACK_BRENT_PRICE,
            wti_price=FALLBACK_WTI_PRICE,
            status="documented_fallback",
            source_notes=tuple(notes),
        )

    live_count = 0
    try:
        values["xom"] = _latest_xom_close()
        live_count += 1
        notes.append("XOM close updated through yfinance.")
    except Exception as exc:  # network and vendor failures use documented fallback
        notes.append(f"XOM live update unavailable: {type(exc).__name__}.")

    api_key = os.getenv("FRED_API_KEY", "").strip()
    if api_key:
        for key, series_id in (("brent", "DCOILBRENTEU"), ("wti", "DCOILWTICO")):
            try:
                values[key] = _latest_fred_value(series_id, api_key)
                live_count += 1
                notes.append(f"{key.title()} updated from FRED series {series_id}.")
            except Exception as exc:
                notes.append(
                    f"{key.title()} FRED update unavailable: {type(exc).__name__}."
                )
    else:
        notes.append("FRED_API_KEY not set; documented crude baselines retained.")

    if live_count == 3:
        status = "live"
    elif live_count:
        status = "partial_live"
    else:
        status = "documented_fallback"

    dates: Iterable[str] = (values[key][0] for key in ("xom", "brent", "wti"))
    as_of = max(dates, default=date.today().isoformat())
    return MarketData(
        as_of_date=as_of,
        xom_price=values["xom"][1],
        brent_price=values["brent"][1],
        wti_price=values["wti"][1],
        status=status,
        source_notes=tuple(notes),
    )
