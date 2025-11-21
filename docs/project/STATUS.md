# Project Status Report
**Date:** November 20, 2025
**Status:** 🟡 Maintenance / Bug Fix Pending Verification

## 1. Overview
The **True Exposure Portfolio Analyzer** is functional but producing incomplete reports. The pipeline runs end-to-end, but the final metadata enrichment (Sector/Geography) is failing for non-US assets. We have identified the root cause as a data quality issue where adapters are discarding ISINs and passing raw tickers (e.g., `NESN`) to the enrichment API, which fails without an exchange suffix.

## 2. Recent Fixes (In Progress)
*   **Enrichment Logic:** Identified that `yfinance` requires ISINs or suffixed tickers (`NESN.SW`) for European stocks.
*   **Adapter Update:** Updating `ISharesAdapter` (and others) to preserve the `ISIN` column from source files instead of relying on tickers.
*   **Garbage Filtering:** Implementing a filter in `aggregation.py` to remove valid but useless identifiers like `_CURRENCYUSD` before enrichment.

## 3. Capabilities
*   **PDF Import:** Automatically parses Trade Republic "Umsatzübersicht" PDFs.
*   **Position Calculation:** Reconstructs portfolio positions.
*   **Live Pricing:** Fetches real-time prices for all assets via `yfinance`.
*   **ETF Look-Through:** Decomposes ETF holdings using provider-specific adapters.
*   **Reporting:** Generates Sector, Geography, and Top 10 Holdings reports.

## 4. Adapter Support
| Provider | Strategy | Status | Notes |
| :--- | :--- | :--- | :--- |
| **iShares** | API (Product Page) | 🟢 Automated | Uses hidden API JSON. Maps Product IDs. |
| **VanEck** | Direct Download | 🟢 Automated | Downloads Excel directly. |
| **Xtrackers** | Direct Download | 🟢 Automated | Downloads CSV directly. |
| **Amundi** | Semi-Manual | 🟡 "Escape Hatch" | Requires user to place XLSX in `data/inputs/manual_holdings`. |

## 5. Known Limitations
1.  **Enrichment:** Sector/Geography reports are currently empty due to the ticker issue described above.
2.  **System Resources:** The Selenium/Chrome automation can leave zombie processes if interrupted.
3.  **Currency:** Implicitly assumes EUR base currency.
