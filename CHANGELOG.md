# Changelog

## [Unreleased]

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