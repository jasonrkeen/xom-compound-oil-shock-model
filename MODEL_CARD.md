# Model Card

## Model details

**Name:** XOM Compound Oil Shock Equity Stress Model
**Version:** 0.1.0
**Author:** Jason Keen
**Release date:** July 23, 2026
**License:** MIT

## Intended use

The model is designed for transparent research on how a prolonged Strait of
Hormuz disruption and attacks on Russian or Black Sea oil infrastructure could
flow through physical supply, market prices, ExxonMobil segment earnings, free
cash flow, and an equity valuation range.

Appropriate uses include:

- geopolitical and energy-security scenario analysis;
- corporate-finance and market-risk education;
- sensitivity testing of public assumptions;
- reproducible portfolio research;
- discussion of nonlinear oil-price effects on an integrated energy company.

## Out-of-scope uses

The model is not intended to:

- predict attacks, military operations, or escalation probability;
- provide a single XOM price target;
- recommend buying, selling, or holding a security;
- reproduce ExxonMobil's internal financial planning;
- replace professional investment, legal, security, or policy advice.

## Inputs

The model uses:

- Hormuz transit and bypass-capacity baselines;
- scenario assumptions for Russian crude and product losses;
- CPC and other infrastructure disruption;
- policy offsets and demand destruction;
- ExxonMobil public segment and cash-flow data;
- optional XOM, Brent, and WTI market updates;
- transparent earnings and valuation sensitivities.

## Outputs

- conditional Brent and WTI estimates;
- physical supply gap;
- conditional recession probability;
- segment earnings;
- net income and free cash flow;
- deterministic valuation ensemble;
- Monte Carlo P10, median, and P90 XOM values;
- probability of exceeding the selected market baseline.

## Validation

Version 0.1.0 includes tests for:

- economic bounds;
- monotonic oil-price response to larger unoffset supply loss;
- negative effect of greater ExxonMobil volume loss;
- demand-response reduction of the supply gap;
- Monte Carlo reproducibility.

GitHub Actions runs the tests on Python 3.11 and 3.12 and executes an offline
500-draw smoke test.

## Important limitations

- Company sensitivities are calibrated research assumptions, not ExxonMobil
  guidance.
- Public segment results do not disclose every asset-level exposure.
- Recession and valuation effects are simplified.
- The historical factor component is calibrated rather than estimated from a
  curated event-study dataset.
- Tail risks outside the configured bounds are not represented.
- Conditional scenario percentiles are not event probabilities.

## Responsible interpretation

Use the model to compare assumptions and identify decision thresholds. Do not
describe its outputs as predictions. Any public discussion should state the
market baseline date, scenario conditions, uncertainty range, and principal
limitations.
