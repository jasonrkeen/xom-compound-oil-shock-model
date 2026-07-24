from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(os.getenv("TMPDIR", "/tmp")) / "xom-model-matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import Assumptions, MarketData, Scenario
from .engine import evaluate_scenario

NAVY = "#10243E"
BLUE = "#1976A8"
TEAL = "#2A9D8F"
GOLD = "#E9A23B"
RED = "#C94C4C"
LIGHT = "#EEF3F7"
MID = "#66788A"
REPORT_FONT = "ReportSans"
REPORT_FONT_BOLD = "ReportSans-Bold"

pdfmetrics.registerFont(TTFont(REPORT_FONT, "Vera.ttf"))
pdfmetrics.registerFont(TTFont(REPORT_FONT_BOLD, "VeraBd.ttf"))


def _money(value: float) -> str:
    return f"${value:,.2f}"


def create_charts(
    summary: pd.DataFrame,
    draws: pd.DataFrame,
    market: MarketData,
    chart_dir: Path,
    assumptions: Assumptions,
    threshold_scenario: Scenario,
) -> dict[str, Path]:
    chart_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 10,
        }
    )

    names = summary["scenario"].tolist()
    y = np.arange(len(names))
    p10 = summary["implied_price_p10"].to_numpy()
    p50 = summary["implied_price_p50"].to_numpy()
    p90 = summary["implied_price_p90"].to_numpy()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.hlines(y, p10, p90, color=BLUE, linewidth=6, alpha=0.28)
    ax.scatter(p50, y, color=NAVY, s=80, label="Median")
    ax.scatter(p10, y, color=BLUE, s=34, label="P10 / P90")
    ax.scatter(p90, y, color=BLUE, s=34)
    ax.axvline(
        market.xom_price,
        color=RED,
        linestyle="--",
        linewidth=1.6,
        label=f"Baseline {_money(market.xom_price)}",
    )
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel("Implied XOM price (USD per share)")
    ax.set_title("Conditional XOM Valuation Ranges by Scenario")
    ax.grid(axis="x", alpha=0.22)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    price_path = chart_dir / "scenario_price_ranges.png"
    fig.savefig(price_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(10, 5.4))
    x = np.arange(len(names))
    bars = ax1.bar(
        x,
        summary["brent_price"],
        color=[TEAL, BLUE, GOLD, RED],
        alpha=0.90,
    )
    ax1.axhline(
        market.brent_price,
        color=NAVY,
        linestyle="--",
        linewidth=1.5,
        label=f"Baseline Brent {_money(market.brent_price)}",
    )
    ax1.set_ylabel("Brent (USD/bbl)")
    ax1.set_xticks(x, names, rotation=14, ha="right")
    ax1.set_title("Oil Price Stress and Recession Offset")
    ax2 = ax1.twinx()
    ax2.plot(
        x,
        summary["recession_probability"] * 100,
        color=RED,
        marker="o",
        linewidth=2.2,
        label="Recession probability",
    )
    ax2.set_ylabel("Conditional recession probability (%)", color=RED)
    ax2.tick_params(axis="y", colors=RED)
    ax1.grid(axis="y", alpha=0.2)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, frameon=False, loc="upper left")
    for bar in bars:
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"${bar.get_height():.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    stress_path = chart_dir / "oil_recession_tradeoff.png"
    fig.savefig(stress_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    scenario = summary.iloc[-1]["scenario"]
    selected = draws.loc[draws["scenario"] == scenario, "implied_price"]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.hist(selected, bins=55, color=BLUE, alpha=0.82, edgecolor="white")
    ax.axvline(market.xom_price, color=RED, linestyle="--", linewidth=1.6)
    ax.axvline(selected.median(), color=NAVY, linewidth=2.0)
    ax.set_title(f"Monte Carlo Distribution: {scenario}")
    ax.set_xlabel("Implied XOM price (USD per share)")
    ax.set_ylabel("Simulation draws")
    ax.grid(axis="y", alpha=0.18)
    fig.tight_layout()
    distribution_path = chart_dir / "threshold_distribution.png"
    fig.savefig(distribution_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    disruption_grid = np.linspace(0.40, 1.00, 31)
    demand_grid = np.linspace(0.00, 0.16, 33)
    values = np.zeros((len(disruption_grid), len(demand_grid)))
    for row_index, disruption in enumerate(disruption_grid):
        for column_index, demand_loss in enumerate(demand_grid):
            tested = replace(
                threshold_scenario,
                hormuz_disruption_share=float(disruption),
                demand_destruction_pct=float(demand_loss),
            )
            result = evaluate_scenario(tested, market, assumptions)
            values[row_index, column_index] = (
                float(result["implied_price_deterministic"]) - market.xom_price
            )
    fig, ax = plt.subplots(figsize=(10, 5.2))
    mesh = ax.contourf(
        demand_grid * 100,
        disruption_grid * 100,
        values,
        levels=np.linspace(-80, 80, 17),
        cmap="RdYlGn",
        extend="both",
    )
    zero = ax.contour(
        demand_grid * 100,
        disruption_grid * 100,
        values,
        levels=[0],
        colors=NAVY,
        linewidths=2.2,
    )
    ax.clabel(zero, fmt={0: "Baseline-value boundary"}, inline=True, fontsize=9)
    colorbar = fig.colorbar(mesh, ax=ax)
    colorbar.set_label("Deterministic XOM value change (USD/share)")
    ax.set_xlabel("Demand destruction (%)")
    ax.set_ylabel("Hormuz transit disruption (%)")
    ax.set_title("Where the Higher-Oil Benefit Flips")
    fig.tight_layout()
    threshold_path = chart_dir / "benefit_flip_heatmap.png"
    fig.savefig(threshold_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return {
        "price_ranges": price_path,
        "oil_recession": stress_path,
        "distribution": distribution_path,
        "threshold_map": threshold_path,
    }


def write_method_log(
    path: Path,
    market: MarketData,
    assumptions: Assumptions,
    scenarios: list[Scenario],
    draws: int,
    seed: int,
) -> None:
    sources = [
        {
            "source": "U.S. Energy Information Administration",
            "url": "https://www.eia.gov/todayinenergy/detail.php?id=65504",
            "use": "Hormuz transit volume and available bypass capacity",
        },
        {
            "source": "ExxonMobil 2025 results",
            "url": "https://corporate.exxonmobil.com/news/news-releases/2026/0130-exxonmobil-announces-2025-results",
            "use": "Segment earnings, production, net income, and free cash flow baselines",
        },
        {
            "source": "ExxonMobil 2025 Form 10-K",
            "url": "https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/xom-20251231.htm",
            "use": "Asset geography, Tengiz and CPC exposure, and risk disclosures",
        },
        {
            "source": "Reuters - Kazakhstan and CPC disruption",
            "url": "https://www.reuters.com/business/energy/kazakhstans-oil-output-plummets-after-drone-attacks-forced-exporting-terminal-2026-07-23/",
            "use": "CPC route share and observed Tengiz production disruption",
        },
        {
            "source": "Reuters - July 23, 2026 crude close",
            "url": "https://www.reuters.com/business/energy/oil-prices-rise-six-week-high-us-iran-tensions-escalate-2026-07-23/",
            "use": "Fallback Brent and WTI market baselines",
        },
    ]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_version": "0.1.0",
        "market_data": market.to_dict(),
        "assumptions": assumptions.to_dict(),
        "scenarios": [scenario.to_dict() for scenario in scenarios],
        "simulation": {"draws_per_scenario": draws, "seed": seed},
        "sources": sources,
        "interpretation": (
            "Conditional stress results are modeled judgments, not forecasts of "
            "geopolitical-event probability or investment recommendations."
        ),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_pdf_report(
    path: Path,
    summary: pd.DataFrame,
    market: MarketData,
    charts: dict[str, Path],
    draws: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleWhite",
            parent=styles["Title"],
            fontName=REPORT_FONT_BOLD,
            fontSize=23,
            leading=27,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleWhite",
            parent=styles["BodyText"],
            fontName=REPORT_FONT,
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#DDE8F2"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName=REPORT_FONT_BOLD,
            fontSize=15,
            leading=18,
            textColor=colors.HexColor(NAVY),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCompact",
            parent=styles["BodyText"],
            fontName=REPORT_FONT,
            fontSize=9.3,
            leading=13.2,
            textColor=colors.HexColor("#263746"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName=REPORT_FONT_BOLD,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor(NAVY),
            alignment=TA_CENTER,
        )
    )

    def footer(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D5DEE7"))
        canvas.line(0.6 * inch, 0.55 * inch, 7.9 * inch, 0.55 * inch)
        canvas.setFont(REPORT_FONT, 7.5)
        canvas.setFillColor(colors.HexColor(MID))
        canvas.drawString(
            0.6 * inch, 0.35 * inch, "XOM Compound Oil Shock Equity Stress Model"
        )
        canvas.drawRightString(7.9 * inch, 0.35 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.58 * inch,
        leftMargin=0.58 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.68 * inch,
        title="XOM Compound Oil Shock Equity Stress Model",
        author="Jason Keen",
    )
    story: list[Any] = []

    title_box = Table(
        [
            [
                Paragraph(
                    "XOM Compound Oil Shock<br/>Equity Stress Model",
                    styles["TitleWhite"],
                )
            ],
            [
                Paragraph(
                    "A scenario-based assessment of a prolonged Strait of Hormuz "
                    "closure combined with attacks on Russian and Black Sea oil "
                    "infrastructure.",
                    styles["SubtitleWhite"],
                )
            ],
            [
                Paragraph(
                    f"Market baseline: {market.as_of_date} | "
                    f"XOM {_money(market.xom_price)} | "
                    f"Brent {_money(market.brent_price)}/bbl",
                    styles["SubtitleWhite"],
                )
            ],
        ],
        colWidths=[7.15 * inch],
    )
    title_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY)),
                ("LEFTPADDING", (0, 0), (-1, -1), 24),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                ("TOPPADDING", (0, 0), (-1, 0), 25),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                ("TOPPADDING", (0, 1), (-1, 1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 17),
                ("TOPPADDING", (0, 2), (-1, 2), 10),
                ("BOTTOMPADDING", (0, 2), (-1, 2), 18),
            ]
        )
    )
    story.extend([title_box, Spacer(1, 12)])

    story.append(Paragraph("Executive judgment", styles["Section"]))
    story.append(
        Paragraph(
            "ExxonMobil benefits from higher crude realizations and tighter refining "
            "margins during the first phase of a compound supply shock. The benefit "
            "is not unlimited. Longer disruptions increase the probability of lost "
            "company volumes, demand destruction, recession, working-capital needs, "
            "and valuation-multiple compression.",
            styles["BodyCompact"],
        )
    )
    median_best = summary.loc[summary["implied_price_p50"].idxmax()]
    threshold = summary.iloc[-1]
    callout_data = [
        [
            Paragraph(
                f"Highest median scenario<br/><font size=15>{_money(float(median_best['implied_price_p50']))}</font>",
                styles["Callout"],
            ),
            Paragraph(
                f"Demand-threshold median<br/><font size=15>{_money(float(threshold['implied_price_p50']))}</font>",
                styles["Callout"],
            ),
            Paragraph(
                f"Threshold probability above baseline<br/><font size=15>{float(threshold['probability_above_baseline']):.0%}</font>",
                styles["Callout"],
            ),
        ]
    ]
    callouts = Table(callout_data, colWidths=[2.38 * inch] * 3)
    callouts.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(LIGHT)),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#CED9E2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CED9E2")),
                ("TOPPADDING", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    story.extend([Spacer(1, 4), callouts, Spacer(1, 10)])
    story.append(
        Image(str(charts["price_ranges"]), width=7.15 * inch, height=3.86 * inch)
    )

    story.append(PageBreak())
    story.append(Paragraph("Scenario results", styles["Section"]))
    table_data: list[list[Any]] = [
        ["Scenario", "Brent", "Net income", "P10", "Median", "P90", "P(> base)"]
    ]
    for _, row in summary.iterrows():
        table_data.append(
            [
                Paragraph(str(row["scenario"]), styles["BodyCompact"]),
                _money(float(row["brent_price"])),
                f"${float(row['net_income_billion']):.1f}B",
                _money(float(row["implied_price_p10"])),
                _money(float(row["implied_price_p50"])),
                _money(float(row["implied_price_p90"])),
                f"{float(row['probability_above_baseline']):.0%}",
            ]
        )
    scenario_table = Table(
        table_data,
        colWidths=[
            1.75 * inch,
            0.72 * inch,
            0.82 * inch,
            0.76 * inch,
            0.78 * inch,
            0.76 * inch,
            0.78 * inch,
        ],
        repeatRows=1,
    )
    scenario_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), REPORT_FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), REPORT_FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(LIGHT)]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D2DC")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([scenario_table, Spacer(1, 12)])
    story.append(
        Image(str(charts["oil_recession"]), width=7.15 * inch, height=3.86 * inch)
    )

    story.append(PageBreak())
    story.append(Paragraph("Why the relationship becomes nonlinear", styles["Section"]))
    nonlinear = [
        [
            Paragraph("<b>Positive channels</b>", styles["BodyCompact"]),
            Paragraph("<b>Negative channels</b>", styles["BodyCompact"]),
        ],
        [
            Paragraph(
                "Higher realized crude prices<br/>Tighter diesel and gasoline crack spreads<br/>Inventory gains<br/>Geographic diversification through Permian and Guyana",
                styles["BodyCompact"],
            ),
            Paragraph(
                "Tengiz and CPC volume exposure<br/>Freight, insurance, and security costs<br/>Chemical-margin pressure<br/>Demand destruction and recession<br/>Equity-risk-premium expansion",
                styles["BodyCompact"],
            ),
        ],
    ]
    channel_table = Table(nonlinear, colWidths=[3.57 * inch, 3.57 * inch])
    channel_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#DFF1ED")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F8E5E5")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C7D2DC")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D2DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.extend([channel_table, Spacer(1, 12)])
    story.append(
        Image(str(charts["distribution"]), width=7.15 * inch, height=3.72 * inch)
    )
    story.append(
        Paragraph(
            "Interpretation: the distribution is conditional on the selected "
            "scenario. It does not estimate the probability that the geopolitical "
            "scenario itself will occur.",
            styles["BodyCompact"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("Threshold map and method", styles["Section"]))
    story.append(
        Image(str(charts["threshold_map"]), width=7.15 * inch, height=3.72 * inch)
    )
    story.append(
        Paragraph(
            "The dark boundary marks the modeled combination at which the "
            "deterministic XOM value crosses the current-share-price baseline. "
            "The location of this boundary is conditional on all other cascading "
            "scenario assumptions.",
            styles["BodyCompact"],
        )
    )
    story.append(Paragraph("Method and limitations", styles["Section"]))
    method_text = [
        (
            "<b>Physical supply layer.</b> Gross Hormuz disruption is reduced by "
            "available bypass capacity, policy offsets, and modeled demand response. "
            "Russian crude, product, CPC, and other losses are added separately."
        ),
        (
            "<b>Market layer.</b> A convex short-run supply-gap function estimates "
            "Brent. Product tightness affects a composite refining crack spread."
        ),
        (
            "<b>Corporate layer.</b> Brent and refining changes flow through Exxon "
            "Upstream and Energy Products. Chemical, Specialty, Corporate, volume, "
            "working-capital, and security-cost effects are modeled independently."
        ),
        (
            "<b>Valuation layer.</b> The implied share price is an ensemble of "
            "earnings-multiple, free-cash-flow-yield, and market-factor estimates. "
            f"Each scenario uses {draws:,} Monte Carlo draws."
        ),
        (
            "<b>Important limitation.</b> Public segment data cannot reproduce "
            "Exxon's internal planning model. Sensitivities are transparent research "
            "assumptions and should be recalibrated as new filings and event data "
            "become available. This is research, not investment advice."
        ),
    ]
    for item in method_text:
        story.append(Paragraph(item, styles["BodyCompact"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Primary sources", styles["Section"]))
    sources = [
        "U.S. EIA - World Oil Transit Chokepoints and Strait of Hormuz analysis.",
        "ExxonMobil - 2025 results and 2025 Form 10-K.",
        "Reuters - July 2026 CPC, Tengiz, Russian infrastructure, and crude-price reporting.",
        "FRED and yfinance - optional live market observations when available.",
    ]
    for source in sources:
        story.append(Paragraph(f"- {source}", styles["BodyCompact"]))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
