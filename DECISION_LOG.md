# Architectural Decision Log

This log records significant architectural decisions and trade-offs.

## 2025-11-20: Parallel PDF Parsing & Incremental SQLite Loading

### Context
Parsing large Trade Republic PDF exports (200+ pages) was CPU-bound and prohibitively slow (>10 mins). Additionally, the lack of deduplication meant re-running the pipeline required deleting the DB or processing everything from scratch.

### Decision
1.  **Multiprocessing:** We utilized Python's `multiprocessing.Pool` to parallelize page parsing.
    *   **Trade-off:** Increased memory usage (one process per core).
    *   **Constraint:** Used `spawn` safe arguments (file path + page index) instead of passing complex objects.
2.  **Incremental Loading:** We leveraged SQLite as the state store.
    *   `processed_files` table tracks file hashes.
    *   `trades` table uses `UNIQUE` constraints and `INSERT OR IGNORE` to handle overlapping data.
    *   **Trade-off:** Requires database schema management (migrations/init scripts), but significantly improves UX and robustness.

### Consequences
*   **Performance:** 5x-10x speedup on multi-core machines.
*   **UX:** Subsequent runs are instant.
*   **Complexity:** `parser.py` is more complex due to process management, but `setup_db.py` logic is simplified (just call parser).

## 2025-11-20: Adoption of Rust-based Excel Parsing (Calamine)

### Context
Amundi exports malformed `.xlsx` files (invalid XML/styles) that cause the standard `openpyxl` engine to crash. Users were forced to manually convert files to CSV, violating the "Radical Simplicity" principle.

### Decision
We integrated `python-calamine` (a Python binding for the Rust `calamine` library) as a fallback engine in the `AmundiAdapter`.

### Consequences
*   **Robustness:** The system can now read corrupted/non-compliant Excel files that `pandas`/`openpyxl` reject.
*   **Dependencies:** Added `python-calamine` to `requirements.txt`.
*   **UX:** Users can simply download files (even if broken) and the system handles them transparently.

## 2025-11-24: Shift to Relational Snapshot Architecture (Hybrid Model)

### Context
The initial "PDF Replay" architecture was fragile. A single missing historical transaction (e.g., from an old PDF not included in the export) resulted in incorrect current quantities. Furthermore, data quality issues (phantom holdings like AstraZeneca) were hard to debug because the state was derived dynamically rather than stored explicitly. Finally, we faced a "Ticker vs. ISIN" conflict where pricing APIs needed Tickers but Holdings APIs needed ISINs.

### Decision
We transitioned to a **State-Based / Relational Architecture**:
1.  **Snapshot Source:** We prioritize a validated "Snapshot" of current holdings (`portfolio_holdings.csv`) over replaying transaction history.
2.  **Relational Data:** We split asset definition from ownership.
    *   **`asset_universe.csv`:** The Master Record. Contains `ISIN`, `Name`, `Yahoo_Ticker`, `Provider`. Solves the identity crisis.
    *   **`portfolio_holdings.csv`:** The State. Contains `ISIN` and `Quantity`.
3.  **Batch Pricing:** We replaced single-ticker fetching with robust batch fetching (`period='5d'`) to handle market closures and prevent false "Delisted" errors.

### Consequences
*   **Robustness:** The system is now resilient to missing history. "What you see is what you analyze."
*   **Maintainability:** The `asset_universe.csv` can be curated and shared (e.g., open-sourced) without exposing user holdings.
*   **Accuracy:** Ticker/ISIN mapping is explicit and verified, eliminating lookup failures.
*   **Trade-off:** The automated PDF parser is temporarily disconnected from the main pipeline (it writes to the old DB). A future refactor is needed to make the parser update the CSVs instead.

## 2025-11-24: Codebase Modernization (Packaging & Config)

### Context
The codebase suffered from "Script Rot": brittle `sys.path` hacks, hardcoded paths scattered across files, and monolithic functions that were hard to test. This made the project fragile and difficult to install or extend.

### Decision
1.  **Packaging First:** We converted the project into a standard Python package using `pyproject.toml`.
2.  **Centralized Config:** We moved all filesystem paths to `src/config.py`.
3.  **Modular Refactoring:** We broke down the largest "God Method" (`AmundiAdapter`) into testable units.

### Consequences
*   **Robustness:** Tests can now run reliably without path hacks.
*   **Maintainability:** Changing a data directory now requires editing 1 line in `config.py` instead of 10 files.
*   **Quality:** Type hints and smaller functions enable better static analysis and testing.

---

## 2025-11-25: Technical Debt Resolution (CSV-First & Tool Automation)

### Decision: Deprecate SQLite Database Workflow
**Context:** PDF parser wrote to SQLite DB that was no longer used by main pipeline.  
**Decision:** Delete database modules, preserve CSV-first workflow.  
**Rationale:** Manual CSV from screenshots = authoritative (complete, current). PDF parser = supplemental for new positions only. Simpler architecture with fewer moving parts.

### Decision: Incremental PDF Parser
**Context:** PDFs may not have complete historical data.  
**Decision:** PDF parser only adds new positions, never replaces existing CSV.  
**Rationale:** Screenshots provide complete portfolio view. PDFs useful for tracking new trades incrementally. Default mode: `add_new` (only append missing ISINs).

### Decision: Ticker Management Automation
**Context:** 60+ manual entries in `ticker_map.json` with duplicates.  
**Decision:** Auto-generate from `asset_universe.csv` with validation.  
**Rationale:** Eliminates manual JSON editing, prevents duplicates and orphaned entries. Single source of truth: `asset_universe.csv`. Implementation: validate/rebuild/sync modes.

### Decision: Asset Management CLI
**Context:** Manual CSV editing error-prone and requires column order knowledge.  
**Decision:** Create CLI tool for all asset management operations.  
**Rationale:** Prevents CSV corruption, validates ISINs before insertion, auto-syncs ticker_map. Better UX with search, validation, and structured output. Commands: add, list, search, validate, remove.

---

## 2025-11-25: Stability & Data Integrity (Phase 11.5)

### Decision: Enforce Base Currency Normalization
**Context:** `yfinance` returns prices in local currency (HKD, GBP, USD). Naive multiplication with quantity results in massive valuation errors (e.g., Xiaomi valued 10x higher because HKD/EUR ~0.11).
**Decision:** All prices fetched from external APIs *must* be converted to the portfolio's Base Currency (EUR) immediately upon receipt.
**Implementation:** `market.py` now detects the currency of the ticker and applies a real-time FX rate conversion before returning the price map.

### Decision: Distinct Naming for ISIN Variants
**Context:** The system contained two S&P 500 ETFs (Distributing vs Accumulating) with the exact same Name string. This made debugging impossible and confused the user (duplicate entries).
**Decision:** `asset_universe.csv` names must be semantically distinct even if the provider calls them the same thing.
**Implementation:** Renamed to "... (Dist)" and "... (Acc)" to enforce uniqueness and clarity.


## 2025-11-26: Local Resolution Priority (Data Enrichment)

### Context
The `enrichment.py` module was fetching data from the Finnhub API. However, for some securities (like Nvidia in iShares ETFs), Finnhub returned `N/A` for the ISIN, overwriting the correct ISIN that had already been resolved locally from `asset_universe.csv`. This caused downstream aggregation failures (ghost assets).

### Decision
**Local Authority:** Locally resolved data (from `asset_universe.csv`) is considered authoritative for identity (ISIN). External APIs are treated as "Enrichment Only".
**Implementation:** Modified `enrichment.py` to check if an ISIN is already present. If so, the API response only updates metadata (Sector, Geography) and *never* overwrites the ISIN unless the API provides a non-null value.

### Consequences
*   **Reliability:** Prevents "regression by enrichment" where valid data is destroyed by incomplete API responses.

## 2025-11-27: ISIN Resolution & Self-Learning (Phase 11.5)

### Decision: Wikidata for ISIN Resolution
**Context:** Free financial APIs (Finnhub, YFinance) failed to provide ISINs for major US stocks (Apple, Microsoft), causing massive overvaluation bugs due to failed aggregation. Paid APIs (Bloomberg) were out of scope.
**Decision:** Use Wikidata as the primary source for ISIN resolution, implementing a "Sophisticated Lookup" strategy.
**Rationale:** Wikidata is free, open, and contains ISINs for most public companies. By cross-referencing Company Name, Raw Ticker (from provider), and Yahoo Ticker, we achieve high-confidence matching (>95%) without external costs.

### Decision: Auto-Harvesting (Self-Learning)
**Context:** Resolving 1000+ ISINs via API on every run is slow (~1 hour) and wasteful. Manually populating `asset_universe.csv` is tedious.
**Decision:** Implement an "Auto-Harvesting" mechanism that runs at the end of the pipeline.
**Rationale:** Successfully resolved ISINs are automatically promoted from the temporary cache to the permanent `asset_universe.csv`. This turns the system into a self-learning engine: the more it runs, the faster and more robust it becomes, with zero manual effort.
*   **Stability:** Fixes the Nvidia overvaluation bug permanently.

---

## 2025-12-03: Ground Truth Quantity Recalculation Strategy

### Context
Portfolio validation showed -27% discrepancy between calculated values and ground truth (GT). Investigation revealed the GT **values** (EUR amounts) were correct (from Trade Republic app display), but **quantities** were systematically wrong for 12/30 positions—some by 100-400%. Root cause: unknown data capture method that corrupted quantities while preserving values.

### Decision
**Reverse-Engineering Approach:** Instead of discarding GT or waiting for a fresh export, use the trusted GT values to recalculate correct quantities:

```
Corrected_Quantity = GT_Value_EUR / Actual_Price_EUR_on_Reference_Date
```

**Implementation:**
1. Created `scripts/recalculate_gt.py` with preview and apply modes
2. Fetches historical prices for reference date (2025-11-24) via yfinance
3. Handles currency conversion (USD→EUR, GBP→EUR, HKD→EUR)
4. Creates timestamped backups before modifying GT
5. Updates quantities only when change exceeds 2% threshold

### Consequences
*   **Accuracy:** Reduced portfolio discrepancy from -27% to -0.2% (114 EUR on 41k portfolio)
*   **Transparency:** Each recalculation is logged with before/after values in GT Notes field
*   **Reusability:** Script can be re-run whenever GT needs correction
*   **Trade-off:** Assumes GT values are authoritative (reasonable for broker-displayed amounts)

### Ticker Mapping Fix (Related)
Discovered Vulcan Energy ticker `VM3.F` was wrong (€0.10 price vs actual €3.18). Fixed to `VUL.DE`. **Lesson:** Extreme recalculation changes (>500%) indicate ticker mapping errors, not quantity errors.
