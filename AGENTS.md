> This file mirrors `.github/copilot-instructions.md` and `CLAUDE.md`; keep all three in sync when any changes.

# AGENTS.md — xom-compound-oil-shock-model

## Purpose
Scenario-based Python model translating prolonged Hormuz and Russian oil infrastructure disruptions into ExxonMobil earnings, free cash flow, and conditional equity valuation ranges.

## Tech stack
- Python; dependencies in `requirements.txt`
- Key libraries: `numpy`, `pandas`, `matplotlib`, `requests`, `python-dotenv`, `reportlab`, `streamlit`, `yfinance`, `pytest`

## Folder structure
- `.github/` (2 files)
- `config/` (2 files)
- `docs/` (2 files)
- `outputs/` (7 files)
- `src/` (8 files)
- `tests/` (1 files)
- `.env.example`
- `.gitattributes`
- `CHANGELOG.md`
- `CITATION.cff`
- `CONTRIBUTING.md`
- `MODEL_CARD.md`
- `README.md`
- `app.py`
- `main.py`
- `requirements.txt`

## Setup, run, test
- `pip install -r requirements.txt`
- Entry point present: `main.py`
- Entry point present: `app.py`
- Tests: 1 Python test file(s) under `tests/`; framework appears to be pytest. Add/update tests with any logic change.
- CI workflows exist in `.github/workflows/`; keep them passing.

## Conventions observed
- Functions use type hints; keep annotating new code.
- Uses `dataclasses` for structured config/results.
- Random seeds are set for reproducibility (Monte Carlo/simulation); keep seeded, deterministic runs.
- Credentials/API keys come from environment variables (see `.env.example`); never hardcode them.
- Public data sources referenced: FRED, EIA, yfinance.
- Write paths relative to the repo root (no absolute local paths).

## Output artifacts
- Generated outputs go to: `outputs/charts/`, `outputs/pdf/`
- A PDF report is produced with `reportlab`; keep it in sync with model changes.
- Streamlit dashboard: `app.py` (run with `streamlit run <file>`).
- Charts are generated with matplotlib.

## Guardrails
- Never commit secrets, API keys, tokens, or `.env` files.
- Do not commit large raw datasets or binaries; keep data fetched or documented with its source.
- Keep analysis source-backed: cite data sources and assumptions; label scenario/forecast outputs as model estimates, not facts.
- Preserve reproducibility: no unseeded randomness, no hidden manual steps.
