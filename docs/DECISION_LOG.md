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
