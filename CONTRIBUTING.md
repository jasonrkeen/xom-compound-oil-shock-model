# Contributing

Contributions that improve transparency, calibration, testing, or source quality
are welcome.

## Good contribution candidates

- Replace a research assumption with a reproducible public-data estimate.
- Add an event-study dataset for XOM, Brent, crack spreads, the S&P 500, and VIX.
- Improve treatment of refinery outages versus crude-export interruptions.
- Add sensitivity tests without converting stress results into point forecasts.
- Correct documentation, units, source links, or scenario definitions.

## Development workflow

1. Create a branch from `main`.
2. Install the dependencies in `requirements.txt`.
3. Make the smallest change that addresses the issue.
4. Run `python -m pytest -q`.
5. Run `python main.py --offline --draws 500 --output-dir outputs-ci`.
6. Explain changed assumptions and their effect in the pull request.

Do not commit API keys, `.env`, virtual environments, caches, or the full
Monte Carlo draw file.

## Evidence expectations

Model changes should cite a primary source when one is available. Clearly label
analyst assumptions when no authoritative observation exists. Do not present a
conditional scenario distribution as the probability that a geopolitical event
will occur.
