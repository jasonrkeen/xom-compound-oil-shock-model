# Output policy

The repository tracks a small set of publication-ready outputs:

- `scenario_summary.csv`
- `source_and_method_log.json`
- `charts/benefit_flip_heatmap.png`
- `charts/scenario_price_ranges.png`
- `pdf/xom_compound_oil_shock_report.pdf`

The following outputs are generated locally but intentionally excluded from
version control:

- `simulation_draws.csv`
- `market_baseline.json`
- intermediate charts

This keeps the repository reviewable while preserving enough evidence to
understand the published baseline run. Run `python main.py --offline` to
reproduce every output.
