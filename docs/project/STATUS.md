# Project Status Report
**Date:** November 19, 2025
**Status:** 🟢 Stable / Production Ready

## 1. Overview
The **True Exposure Portfolio Analyzer** has successfully passed its "Live Data Test". It creates a complete "Look-Through" analysis of a Trade Republic portfolio, breaking down ETFs into their underlying stock exposures.

## 2. Capabilities
*   **PDF Import:** Automatically parses Trade Republic "Umsatzübersicht" PDFs to generate transaction history.
*   **Position Calculation:** Reconstructs portfolio positions (Quantity, Average Price) from transaction history.
*   **Live Pricing:** Fetches real-time prices for all assets via `yfinance` (Yahoo Finance).
*   **ETF Look-Through:** Decomposes ETF holdings using provider-specific adapters.
*   **Reporting:** Generates Sector, Geography, and Top 10 Holdings reports.
*   **Validation:** Verifies mathematical consistency (Value Conservation Check) with <2% tolerance.

## 3. Adapter Support
| Provider | Strategy | Status | Notes |
| :--- | :--- | :--- | :--- |
| **iShares** | API (Product Page) | 🟢 Automated | Uses hidden API JSON. Maps Product IDs. |
| **VanEck** | Direct Download | 🟢 Automated | Downloads Excel directly. |
| **Xtrackers** | Direct Download | 🟢 Automated | Downloads CSV directly. |
| **Amundi** | Semi-Manual | 🟡 "Escape Hatch" | Requires user to place XLSX in `data/inputs/manual_holdings`. |

## 4. Project Structure
The project follows a standard Python package layout:

```text
portfolio-master/POC/
├── src/                        # Application Source Code
│   ├── core/                   # Business Logic (Aggregation, Reporting)
│   ├── data/                   # Data Access (DB, Pricing, Enrichment)
│   ├── adapters/               # ETF Provider Integrations
│   ├── pdf_parser/             # Trade Republic PDF Parsing
│   └── utils/                  # Logging, Schemas
├── scripts/                    # Executable Scripts
│   ├── run_pipeline.py         # Main Entry Point
│   └── setup_db.py             # PDF -> Database Step
├── data/                       # Data Storage
│   ├── inputs/
│   │   ├── portfolio/          # Input: Trade Republic PDFs
│   │   └── manual_holdings/    # Input: Manual ETF Files (Amundi)
│   └── working/                # System State (DB, Cache, Raw)
│       ├── database/
│       ├── cache/
│       └── raw_downloads/
├── outputs/                    # Generated Reports
└── run.sh                      # Master Execution Script
```

## 5. Known Limitations
1.  **Currency:** Implicitly assumes EUR base currency. Multi-currency portfolios (USD cash) handled via simple conversion or yfinance defaults.
2.  **Amundi:** Due to Selenium instability and file inconsistencies, Amundi requires manual file download.
3.  **Finnhub Rate Limits:** Enrichment process is throttled (1 call/1.1s) to respect free tier limits.
