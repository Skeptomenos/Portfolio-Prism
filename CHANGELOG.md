# Changelog

## [Phase 13] - 2025-11-28

### Changed
- **Aggregation Module Refactor**: Decomposed monolithic `src/core/aggregation.py` (350+ lines) into a modular package `src/core/aggregation/` with 6 focused modules:
    - `direct.py` - Direct stock holdings processing
    - `classification.py` - Asset classification (Equity/Cash/Derivative)
    - `grouping.py` - ISIN grouping and value aggregation
    - `enrichment.py` - Tiered ISIN resolution (>1% weight threshold)
    - `output.py` - CSV output formatting and saving
    - `__init__.py` - Public API (`run_aggregation`)

### Added
- **Unit Tests**: Created `tests/test_aggregation_v2.py` with 13 unit tests covering all aggregation submodules:
    - `TestDirectModule` (2 tests) - Direct holdings processing
    - `TestClassificationModule` (2 tests) - Asset classification
    - `TestGroupingModule` (6 tests) - ISIN grouping, fallback IDs, cash normalization
    - `TestOutputModule` (2 tests) - File output and empty handling
    - `TestAggregationIntegration` (1 test) - End-to-end overlapping holdings
- **Integration Tests**: Created `tests/test_integration.py` with end-to-end pipeline validation:
    - Validates direct + indirect holdings aggregation
    - Uses controlled fixtures (`asset_universe_test.csv`, `portfolio_holdings_test.csv`, `ishares_holdings.csv`)
    - Mocks external API calls for deterministic testing

### Fixed
- **Ruff Format**: Applied `ruff format .` across 42 files for consistent code style.
- **Integration Test Mock**: Fixed `finalize_and_save` mock signature to properly handle `AggregatedExposure` objects.
- **Pydantic v2 Deprecation**: Updated `src/models/holdings.py` to use `ConfigDict` instead of deprecated `class Config`.
- **Pandera Import Warnings**: Updated imports to `import pandera.pandas as pa` to eliminate FutureWarning.
- **Bare Except Anti-Pattern**: Fixed E722 in `scripts/visualize_portfolio.py` by using specific exception types.

### Removed
- **Legacy Aggregation**: Deleted monolithic `src/core/aggregation.py` after successful migration.

---

## [Phase 12.5] - 2025-11-27

### Fixed
- **Lint Compliance**: Resolved 148 ruff lint errors across the codebase (85% reduction from 173 to 25).
    - Fixed CRITICAL: `scripts/migrate_db_to_csv.py` had 63 syntax errors from unicode emojis in f-strings.
    - Fixed HIGH: Added stubs for removed database functions in legacy files (`setup_db_legacy.py`, `parser.py`).
    - Fixed MEDIUM: Replaced 7 bare `except:` with specific exception types.
    - Fixed LOW: Split multiple statements on single lines (E701).
    - Auto-fixed: Removed 50 unused imports, 16 empty f-strings, 4 unused variables.

### Added
- **Ruff Linter**: Installed `ruff 0.14.6` to enforce coding standards.
- **Pipeline Flow Diagram**: Added comprehensive Mermaid flowchart to README.md showing all 10 pipeline stages.
- **Documentation**: Enhanced README.md with:
    - Pipeline stages table with key files
    - Tiered Enrichment and Self-Learning pattern documentation
    - Development section (pytest, ruff commands)
    - Key Design Patterns summary table

### Changed
- **README.md**: Major rewrite with detailed architecture documentation (+164 lines).

---

## [Phase 12] - 2025-11-27

### Changed
- **Directives & Standards**: Updated `@docs/agent/AI_CODING_DIRECTIVES.md` and `@docs/agent/CODING_STANDARDS.md` to `v3` (Spec-Driven & State-Aware).
- **Agent Protocol**: Rewrote `docs/agent/GEMINI.md` to act as a lightweight "Bootloader" that enforces reading the new Directives.
- **Documentation Architecture**: Transitioned from ephemeral "Plans" to living "Specifications".
    - Added `docs/specs/product.md`
    - Added `docs/specs/tech.md`
    - Added `docs/specs/requirements.md`
    - Added `docs/specs/tasks.md`

### Added
- **Spec-Driven Workflow**: Implemented strict phases for Spec Check, Recursive Decomposition, and Archival Rotation.

## [Phase 11.5] - 2025-11-25

### Fixed
- **Currency Blindness**: Fixed a major valuation bug where `yfinance` prices in foreign currencies (e.g., HKD) were treated as EUR. Added a mandatory FX rate conversion layer in `src/data/market.py`.
- **Ghost Values**: Fixed an aggregation bug where numeric strings (e.g., "22,50") caused massive outliers (e.g., 35k Nvidia). Implemented strict numeric coercion in `src/core/aggregation.py`.
- **Asset Confusion**: Renamed "iShares Core S&P 500 ETF" variants in `asset_universe.csv` to explicitly distinguish between `(Acc)` and `(Dist)`, resolving duplicate entries.
- **Cache Integrity:** Implemented `force_refresh` logic to ensure stale `N/A` values are purged when logic changes.
- **Critical Bug Fix:** Resolved Nvidia overvaluation issue caused by Finnhub API overwriting locally resolved ISINs with `N/A`. Modified `enrichment.py` to preserve local ISINs.
- **ISIN Resolution:** Fixed persistent ISIN loss for US stocks (Apple, Microsoft) by implementing a sophisticated Wikidata lookup strategy.
- **Data Loss:** Fixed issue where iShares adapter dropped the raw ticker, making downstream resolution impossible.

### Added
- **Wikidata Integration:** Implemented `fetch_isin_from_wikidata` with multi-signal validation (Name + Raw Ticker + Yahoo Ticker) to reliably resolve ISINs without paid APIs.
- **Auto-Harvesting:** Created `scripts/harvest_enrichment.py` and integrated it into the pipeline. The system now automatically saves successfully resolved ISINs to `asset_universe.csv`, making future runs instant.

---

## [Phase 11] - 2025-11-25

### Added
- **PDF-to-CSV Parser**: Created `scripts/parse_pdfs_to_csv.py` for incremental portfolio updates from PDFs (3 modes: dry_run, add_new, merge).
- **Asset Management CLI**: Created `scripts/manage_assets.py` with 5 commands (add, list, search, validate, remove) for managing `asset_universe.csv`.
- **Data Migration Script**: Created `scripts/migrate_db_to_csv.py` for one-time SQLite → CSV migration.
- **Ticker Management**: Enhanced `scripts/sync_ticker_map.py` with validation, rebuild, and sync modes.

### Changed
- **PDF Parser**: Added `parse_pdfs_from_folder()` helper function in `src/pdf_parser/parser.py` for CSV workflow integration.

### Removed
- **Legacy Database Code**: Deleted `src/data/manager.py` and `src/data/database.py` (SQLite workflow deprecated).
- **Unused Imports**: Removed `manager.py` imports from `aggregation.py`, `reporting.py`, and `generate_inputs.py`.

### Fixed
- **Ticker Map**: Rebuilt from 60 entries (with duplicates) to 32 clean entries sorted by ISIN.

### Deprecated
- **SQLite Workflow**: Renamed `scripts/setup_db.py` → `setup_db_legacy.py` (kept for rollback purposes only).

---

## [Phase 10] - 2025-11-24

### Added
- **Packaging**: Introduced `pyproject.toml` to make the project an installable Python package.
- **Configuration**: Created `src/config.py` to centralize all file paths and remove hardcoded strings.
- **Type Safety**: Added comprehensive type hints to `src/core/aggregation.py` and `src/data/enrichment.py`.

### Changed
- **Refactoring**: Split the monolithic `AmundiAdapter.fetch_holdings` method into modular components (`_fetch_from_manual_file`, `_fetch_via_selenium`, `_parse_downloaded_file`).
- **Standardization**: Removed all `sys.path.insert(...)` hacks from the codebase.
- **Cleanup**: Deleted legacy files (`legacy_pipeline.py`, `legacy_prices.py`) and tests.

### Fixed
- **Test Suite**: Fixed all 9 production tests by updating import paths and removing obsolete mocks (100% passing).

---

## [Phase 9] - 2025-11-24

### Added
- **Architecture**: Implemented a **Hybrid Relational Architecture**. Introduced `asset_universe.csv` (Metadata) and `portfolio_holdings.csv` (State) to decouple asset definition from ownership.
- **Auditability**: Created a "Direct Holdings Report" (Level 1 Audit) and visualized it in a new Dashboard tab. This allows users to verify input data before complex aggregation.
- **Market Data**: Implemented **Batch Price Fetching** with escalation (`1d` -> `5d` -> `1mo`). This resolved widespread "Delisted" errors caused by weekend/holiday execution.
- **Identity Resolution**: Implemented an **Auto-Suffix** strategy for Yahoo Tickers (trying `.DE`, `.F` automatically), drastically reducing manual user prompts.
- **iShares Automation**: Implemented `_discover_product_id` in `ISharesAdapter` to scrape product IDs automatically, closing data gaps.
- **Noise Filtering**: Updated enrichment to skip internal identifiers, reducing API noise.

### Fixed
- **AstraZeneca Ghost**: Eliminated the massive phantom holding (50% portfolio weight) by moving to a Clean Slate + Relational Model, enforcing strict referential integrity.
- **Scaling Bug**: Fixed a Look-Through Scaling error (100x inflation of Nvidia) by ensuring percentage weights are correctly normalized in the aggregation logic.
- **Ticker/ISIN Conflict**: Resolved the conflict between Pricing (needs Ticker) and Holdings (needs ISIN) by using the Relational Model as a bridge.
- **Enrichment Failure (Europe)**: Fixed widespread 404 errors in `yfinance` by generating Yahoo-compatible suffixes (e.g., `NESN.SW`).
- **Price Valuation Bug**: Fixed a corrupted `ticker_map.json` that caused 10x overvaluation.
- **Critical Value Error**: Fixed a parsing bug where English fractional shares were misinterpreted as German thousands.

### Changed
- **Configuration**: Removed invalid test cases from `adapter_registry.json`.
- **Market Data**: Verified and documented the interactive `resolve_ticker` flow.

### Deprecated
- **Legacy Modules**: `src/data/manager.py` (Old DB Loader) is now obsolete. `scripts/setup_db.py` writes to a SQLite DB that is no longer used by the main pipeline.

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