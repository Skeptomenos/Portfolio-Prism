# Handover: 2025-11-24 - Architecture Shift to Relational/Hybrid

## Executive Summary
We have successfully transitioned the project from a fragile "PDF Transaction Replay" model to a robust **Relational Snapshot Architecture**. The system now relies on a validated `asset_universe.csv` (metadata) and `portfolio_holdings.csv` (quantities) as the source of truth. This eliminated the "AstraZeneca Ghost" (data artifact) and the "Nvidia Scaling Bug".

## Current State (Green)
- **Pipeline:** `scripts/run_pipeline.py` runs error-free without user intervention.
- **Data Source:** `src/data/state_manager.py` loads from the Relational CSVs.
- **Market Data:** `src/data/market.py` uses batch fetching (1d->5d->1mo) to reliably capture prices even on weekends.
- **Validation:** All checks passed. Total Portfolio Value matches the audit trail (~€45k).
- **Dashboard:** Visualizes both "Direct Holdings" (Level 1) and "True Exposure" (Level 2).

## New Architecture Components
1.  **`data/true_data/asset_universe.csv`**: The Master Record (ISIN, Ticker, Name, Provider).
2.  **`data/true_data/portfolio_holdings.csv`**: The User State (ISIN, Quantity).
3.  **`src/core/direct_reporting.py`**: Generates the Level 1 Audit report.
4.  **`scripts/migrate_to_universe.py`**: (One-off) Created the initial universe from legacy data.

## Immediate Next Steps (Refactoring Phase)
1.  **Revive Automation:** The PDF Parser (`scripts/setup_db.py`) currently writes to a "Zombie" SQLite database. It must be refactored to parse the PDF and **update** `portfolio_holdings.csv` instead.
2.  **Clean Up Dead Code:**
    - `src/data/manager.py` (Obsolete Loader) -> Delete.
    - `src/data/legacy_prices.py` -> Delete.
    - `src/core/legacy_pipeline.py` -> Delete.
    - `data/working/database/portfolio.db` -> Delete (once parser is updated).
3.  **Enhance Universe:** Add a script to easily add new assets to `asset_universe.csv` (e.g., `python scripts/add_asset.py US000...`).

## Known Issues / Watchlist
- **Yahoo Tickers:** Some obscure assets (e.g., `TKMS`, `Cresco Labs`) required manual overrides in `config/ticker_map.json`. If they change tickers, pricing will fail.
- **Currency:** The current CSV model assumes all holdings are compatible (Quantity). We rely on `yfinance` to provide EUR prices (via suffixes like `.DE`).

## Command to Run
```bash
source venv/bin/activate
python scripts/run_pipeline.py
./run_dashboard.sh
```
