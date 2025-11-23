# Roadmap to 100% Portfolio Coverage

This document outlines the strategic plan to achieve full reliability and accuracy for the "True Exposure" pipeline.

## Phase 1: Market Data Accuracy (Critical)
**Objective:** Eliminate the "Default 100€" fallback which corrupts valuation data.

- [ ] **Audit `market.py`:** Identify where the `100.0` default originates and remove it.
- [ ] **Implement Ticker Mapping:** Create `config/ticker_map.json` to store ISIN -> YFinance Ticker mappings for direct holdings.
- [ ] **Interactive Ticker Resolution:**
    - When `yfinance` fails to find a price for an ISIN:
    - Prompt the user: *"Could not find price for [Name] ([ISIN]). Please enter the Yahoo Finance Ticker (e.g., NESN.SW):"*
    - Validate the input by fetching a price.
    - Save mapping to `config/ticker_map.json`.
- [ ] **Fail-Safe Valuation:** If no price is found, default to the *Purchase Price* from the database (better than 100) or exclude from value-weighted stats with a warning.

## Phase 2: Self-Healing iShares Configuration (Critical)
**Objective:** Automate the discovery of iShares Product IDs to prevent pipeline failures for new ETFs.

- [ ] **Externalize Config:** Move `ISHARES_ETF_DATA` from `src/adapters/ishares.py` to `config/ishares_config.json`.
- [ ] **Interactive Setup:**
    - Catch "ISIN not configured" errors in `ISharesAdapter`.
    - Prompt the user: *"Missing Product ID for [ISIN]. Please enter the Product ID found in the iShares URL:"*
    - Update `config/ishares_config.json`.
    - Retry the fetch immediately.

## Phase 3: Data Quality & "Garbage" Handling (Medium)
**Objective:** Reduce noise in logs and reports caused by non-equity holdings (Futures, Cash).

- [ ] **Enhance Aggregation Logic:**
    - Detect identifiers for Futures (`ESZ5`), Options, and Cash (`_CURRENCY...`).
    - Classify these as `asset_type='Cash/Derivatives'`.
    - Exclude them from "Equity Enrichment" (Finnhub/Yahoo) to stop 404 errors.
    - Include them in the final "Asset Class" report.

## Phase 4: Roadmap Automation (Low)
**Objective:** Streamline the request process for new features.

- [ ] **Missing Adapter Detection:**
    - Identify when a user maps an ISIN to a supported provider (e.g., "Vanguard") that lacks a Python class.
    - **Action:** Automatically append a task to `docs/BACKLOG.md` or create a draft GitHub Issue template: "Feature Request: Create Adapter for [Provider]".
    - Notify the user: *"Support for [Provider] is not yet implemented. Added to backlog."*
