# Changelog

## [Unreleased]

### Added
- **Roadmap Automation**: Implemented a "Feature Gap Detector" that automatically captures unimplemented providers (e.g., Vanguard) and logs them to `docs/BACKLOG.md`.
- **Quality Reporting**: The pipeline now generates `outputs/data_quality_report.txt`, explicitly listing skipped ETFs and the reason for exclusion (e.g., "Provider not implemented").
- **Registry Automation**: Implemented an interactive "Setup Wizard" (`scripts/update_registry.py`) integrated into the main pipeline. It detects new/unknown ISINs and prompts the user to map them to an adapter (iShares, Amundi, etc.) or ignore them.
  - Includes safety validation to warn if the selected provider doesn't match the ETF name.
  - Persists "ignore" choices to prevent repetitive prompting.

### Fixed
- **Enrichment Failure (Europe)**: Fixed widespread 404 errors in `yfinance` enrichment for European assets.
  - **Root Cause**: iShares adapter was extracting raw tickers (e.g., `RR.`, `NESN`) which Yahoo rejects.
  - **Solution**: `ISharesAdapter` now captures exchange metadata (`Standort`, `Börse`) and intelligently generates Yahoo-compatible suffixes (e.g., `RR.L`, `NESN.SW`, `0388.HK`).
- **Data Quality**: `aggregation.py` now explicitly filters out garbage rows (e.g., `_CURRENCYUSD`, `NaN` tickers) before they reach the enrichment layer, cleaning up reports.

---

## [Phase 7] - 2025-11-20

### Added
- **Performance Optimization**: Implemented `multiprocessing` in the PDF parser (`src/pdf_parser/parser.py`), parallelizing page processing. Parsing time for a 200-page document reduced from ~10 minutes to under 2 minutes.
- **Incremental Loading**: Added a `processed_files` table and SHA256 hash checks. The pipeline now instantly skips previously parsed files.
- **Deduplication**: Implemented a `trades` table in SQLite with a `UNIQUE` constraint on transaction details. The system now uses `INSERT OR IGNORE` to seamlessly handle overlapping export files from Trade Republic.
- **Robustness**: Fixed a critical parsing bug for German number formats (e.g., `5.229,00`) that was causing crashes on large transactions.

### Changed
- **Architecture**: `portfolio.db` (SQLite) is now the single source of truth for transaction data. The legacy `trades.csv` is still generated for backward compatibility but is no longer used by the core pipeline.
- **Setup**: `scripts/setup_db.py` now orchestrates the database initialization and incremental parsing flow.

---

## [Phase 5] - 2025-11-18

### Fixed
- **Critical Bug**: Fixed a critical bug in the portfolio aggregation logic where indirect holdings for a security appearing in multiple ETFs were being overwritten instead of summed. The logic now correctly accumulates all indirect holdings before performing the final aggregation.
- **Test Suite**: Refactored the aggregation and reporting test suites to use dependency injection and accurate mock data contracts, making them more robust and reliable.
- **Pipeline Efficiency**: Refactored the main pipeline to fetch ETF holdings data only once, passing it into the aggregation function to avoid redundant I/O calls.

### Changed
- **Configuration**: Refactored the hardcoded `ADAPTER_REGISTRY` into an external JSON configuration file (`config/adapter_registry.json`). This decouples the adapter mapping from the source code, making it easier to add and maintain ETF support.

### Added
- **Data Validation**: Implemented a "fail-fast" data validation strategy using `Pandera`. All data from acquisition adapters is now validated against a strict schema at the source, preventing corrupted data from entering the pipeline.
- **Testing**: Implemented contract tests for the VanEck and iShares data adapters. These tests validate the adapters against local, saved data fixtures, ensuring that changes in the providers' data formats can be detected quickly and reliably.

### Changed
- **Dependencies**: Added `pandera` to `requirements.txt`.
- **Error Handling**: Implemented a structured logging system across the entire application, replacing all `print()` statements.
- **Resilience**: The main pipeline now features graceful degradation; it will no longer halt if a single ETF adapter fails, but will instead log the error and continue processing the remaining ETFs.

### Fixed
- **Bug**: Resolved an `AttributeError` that occurred when processing holdings data with missing tickers or ISINs. Added defensive data cleaning to the `aggregation` and `reporting` modules to filter out `NaN` values before they are processed.
---

## Project History

### Phase 4: Reporting & Analysis - 2025-11-16
- **Completed**: Consumed the aggregated exposure report to produce higher-level portfolio insights, including top holdings, sector, and geography reports. Implemented `enrichment.py` and `reporting.py` modules and validated the "Development Blueprint."

### Phase 2: Exposure Calculation & Aggregation - 2025-11-16
- **Completed**: Implemented the core "true exposure" calculation logic in `aggregation.py`. Developed against mock data and created initial unit tests.

### Phase 1: Data Acquisition - 2025-11-16
- **Completed**: Implemented data acquirers (adapters) for VanEck, iShares, Xtrackers, and Amundi, capturing key learnings about direct download vs. UI automation.
