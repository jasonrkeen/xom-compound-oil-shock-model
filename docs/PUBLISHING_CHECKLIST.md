# Publishing Checklist

## GitHub

- [x] Repository name selected: `xom-compound-oil-shock-model`
- [x] No naming conflict found in the connected `jasonrkeen` account
- [x] README includes findings, charts, architecture, sources, and limitations
- [x] License, citation metadata, changelog, contribution guide, and model card
- [x] GitHub Actions workflow for Python 3.11 and 3.12
- [x] Selected baseline outputs tracked; full simulation draws ignored
- [x] Local tests and offline smoke test pass
- [ ] Create the public GitHub repository
- [ ] Commit the staged release candidate
- [ ] Push `main`
- [ ] Confirm the GitHub Actions workflow passes
- [ ] Verify README charts and PDF links render on GitHub
- [ ] Add repository description and topics
- [ ] Create the `v0.1.0` release and attach the executive PDF

### Recommended repository description

Scenario-based Python model translating prolonged Hormuz and Russian oil
infrastructure disruptions into ExxonMobil earnings, free cash flow, and
conditional equity valuation ranges.

### Recommended topics

- `exxonmobil`
- `geopolitical-risk`
- `oil-market`
- `energy-security`
- `monte-carlo-simulation`
- `equity-valuation`
- `scenario-analysis`
- `python`

## LinkedIn

- [ ] Use the final GitHub URL in the post
- [ ] Lead with the counterintuitive finding, not the code
- [ ] Attach `outputs/charts/benefit_flip_heatmap.png`
- [ ] Explain that conditional valuation ranges are not event probabilities
- [ ] Mention the 40,000 total Monte Carlo draws
- [ ] Credit the EIA, ExxonMobil filings, and current infrastructure reporting
- [ ] Invite critique of assumptions and calibration
- [ ] Add the repository link in the post and first comment

### Recommended post angle

The strongest launch framing is:

> Higher oil prices can help ExxonMobil - until physical asset exposure,
> demand destruction, recession risk, and valuation compression become more
> important than the commodity-price benefit.

The post should briefly explain the transition from physical disruption to
market prices, segment earnings, cash flow, and the conditional XOM range.
