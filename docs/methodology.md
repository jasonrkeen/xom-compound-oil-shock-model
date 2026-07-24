# Methodology

## Research question

At what point does a compound global oil-supply shock stop benefiting
ExxonMobil shareholders?

The model is designed to test a nonlinear proposition. Higher oil prices can
increase Upstream earnings, and product shortages can increase refining
margins. Those benefits can eventually be offset by lost ExxonMobil volumes,
working-capital requirements, security and logistics costs, chemical-margin
pressure, demand destruction, recession, and equity-multiple compression.

## Physical supply layer

The physical layer begins with 20 million barrels per day of Strait of Hormuz
transit volume. The scenario applies a disruption share and then subtracts
usable bypass capacity. Russian crude losses, Russian petroleum-product losses,
CPC losses, and other infrastructure losses are added separately.

Policy offsets and demand response reduce the physical loss:

`net gap = gross loss - bypass - policy offset - demand response`

Russian refinery damage and Russian crude-export damage are not treated as the
same event. A refinery outage can increase crude exports while reducing product
exports. Pipeline, port, tanker, and storage damage can constrain crude exports
directly.

## Price layer

The Brent estimate is a convex function of the percentage net supply gap:

`Brent change = 5 * gap share + 35 * gap share squared`

This form captures the idea that each additional lost barrel has a larger price
effect when inventories, spare capacity, and rerouting options are already
strained. Brent is bounded between $45 and $240 per barrel.

A composite refining crack spread responds to lost petroleum-product supply and
declines when demand destruction becomes large.

## ExxonMobil earnings layer

The starting financial baseline is ExxonMobil's 2025 segment reporting:

| Segment | Baseline earnings |
| --- | ---: |
| Upstream | $21.400 billion |
| Energy Products | $7.423 billion |
| Chemical Products | $0.800 billion |
| Specialty Products | $2.857 billion |
| Corporate and Financing | -$3.590 billion |

The Upstream and Energy Products sensitivities are explicit calibration
assumptions, not company guidance. They are intentionally stored in code and the
method log so that an analyst can change them without rewriting the model.

## Equity valuation layer

The model combines three estimates:

1. Earnings-per-share multiplied by a risk-adjusted P/E multiple.
2. Free cash flow capitalized at a risk-adjusted free-cash-flow yield.
3. A market-factor estimate using oil, refining, recession, volatility, and
   company-volume effects.

The ensemble weights are 45%, 35%, and 20%, respectively.

## Monte Carlo layer

Each scenario varies:

- Hormuz disruption
- bypass utilization
- Russian crude and product losses
- CPC and other supply losses
- policy offsets
- demand destruction
- ExxonMobil volume losses
- recession and geopolitical-risk assumptions
- Upstream and refining earnings sensitivities

The report presents the 10th percentile, median, and 90th percentile of the
conditional valuation distribution. These are not probabilities that the
geopolitical scenario will occur.

## Limitations

- Public segment disclosures cannot reproduce ExxonMobil's internal planning.
- The model does not estimate daily tactical attack probability.
- Political intervention, windfall taxes, sanctions, and emergency reserve
  policy are represented only through scenario parameters.
- The event-study component is a calibrated factor model in version 0.1.0. A
  future version should estimate rolling coefficients from a curated historical
  XOM, Brent, crack-spread, S&P 500, and VIX dataset.
- Results are analytical stress tests, not investment advice.
