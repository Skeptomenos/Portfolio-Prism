# Plan: Hybrid Data Source Architecture

**Objective:** Decouple the "True Exposure" analysis from the "Transaction Parsing" logic. The system should prioritize a verified "Snapshot" of holdings (the Ground Truth) while retaining the ability to update that snapshot via PDF parsing or manual entry.

## 1. First Principles Analysis

*   **What is the core goal?** To calculate the look-through exposure of the user's *current* portfolio.
*   **What is the required input?** A list of assets (ISIN/Ticker) and their current held quantities.
*   **Why did the previous approach fail?** It tried to *derive* the current state by replaying history from an incomplete log (the PDF). Replaying history requires $O(N)$ perfection; one missing transaction invalidates the sum.
*   **What is the solution?** State-based architecture. We define the "Current State" explicitly. The PDF parser becomes just one of many *methods* to modify that state, not the definition of it.

## 2. High-Level Design

We introduce a new layer: The **Portfolio State Manager**.

### Components:
1.  **Source of Truth (`portfolio_state.csv`):** A simple CSV file listing `ISIN`, `Name`, `Quantity`. This is the database for the analysis engine.
2.  **Importer Strategy (The "Write" Path):
    *   **Strategy A (PDF):** Parse Trade Republic PDF $\rightarrow$ Aggregates Trades $\rightarrow$ Updates/Overwrites `portfolio_state.csv`.
    *   **Strategy B (Manual/Override):** User edits `portfolio_state.csv` directly (or we generate it from screenshots).
    *   **Strategy C (API):** Future-proof hook for broker APIs.
3.  **Analysis Pipeline (The "Read" Path):
    *   Reads `portfolio_state.csv` exclusively.
    *   No longer touches the raw SQLite transaction table for quantities.
    *   Fetches Prices, ETF Holdings, and generates reports.

## 3. Implementation Breakdown

### Phase 1: State Definition & Migration
*   **Challenge:** We have existing logic tied to `portfolio.db`.
*   **Solution:** Create a schema for `portfolio_state.csv` (ISIN, Ticker, Name, Quantity, Asset_Type).
*   **Migration:** Create a script `scripts/migrate_to_csv.py` that takes our `portfolio_truth.csv` (from screenshots) and standardizes it into `data/working/portfolio_state.csv`.

### Phase 2: Pipeline Refactoring (`Reading`)
*   **Challenge:** `src/data/manager.py` currently queries SQLite.
*   **Solution:** Rewrite `load_positions_from_db` (rename to `load_portfolio_state`) to read the CSV.
    *   It should handle missing ISINs by looking up Tickers (since screenshots might only have Tickers).
    *   It needs to resolve `Asset Type` (Stock vs ETF) using the Registry, just like before.

### Phase 3: Importer Refactoring (`Writing`)
*   **Challenge:** The PDF parser currently writes to SQLite.
*   **Solution:** Update `setup_db.py` (rename to `import_pdf.py`).
    *   It parses transactions.
    *   It calculates *changes* in positions.
    *   It *updates* `portfolio_state.csv`.
    *   *Crucial Feature:* **"Baseline Mode"**. If the PDF is incomplete, we allow the user to set a "Starting Balance" in the CSV, and the PDF just adds/subtracts from it.

### Phase 4: Validation
*   **Challenge:** Ensuring the CSV names/tickers map to the right ISINs for the adapters.
*   **Solution:** Run the `NameNormalizer` and `TickerMap` logic on the CSV rows during the loading phase.

## 4. Solvable Technical Challenges

1.  **Ticker vs ISIN:** The screenshot data has Tickers (`IWDA`), but our pipeline loves ISINs (`IE00B4...`).
    *   *Fix:* We need a `Ticker -> ISIN` resolver. `yfinance` can often do this (`ticker.isin`), or we use a static lookup for common ETFs.
2.  **Manual vs Auto Conflict:** What if the PDF says 10 shares, but the CSV says 12?
    *   *Fix:* The CSV is King. The PDF importer *proposes* changes, but the CSV is the state. If we run a "Full Import", it overwrites. If we run "Update", it adds.
    *   *Simplification:* For now, we just use the CSV as a static snapshot. The PDF parser is a "tool to generate the CSV", not a live database sync.

## 5. Immediate Steps
1.  **Implement `src/data/state_manager.py`:** Handles reading/writing the CSV.
2.  **Migrate:** Convert `portfolio_truth.csv` to the official format.
3.  **Switch Pipeline:** Point `run_pipeline.py` to use `state_manager`.

This architecture separates "Accounting" (Transactions) from "Analysis" (Exposure), making the system robust to missing history.
