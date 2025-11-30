# Price Source Evaluation: yfinance vs. Alpaca

**Date:** November 19, 2025
**Context:** The project requires fetching live market prices for a portfolio containing a mix of US stocks (e.g., Nvidia, Alphabet) and European ETFs (e.g., iShares Core S&P 500 UCITS ETF, Amundi MSCI India).

## 1. Comparison

| Feature | **yfinance** (Yahoo Finance) | **Alpaca API** |
| :--- | :--- | :--- |
| **Type** | Unofficial Scraper/Wrapper | Official Brokerage/Market Data API |
| **Cost** | Free | Free (Basic) / Paid (Premium) |
| **Coverage** | **Global** (US, Xetra, Euronext, LSE, etc.) | **Primarily US** (Stocks & Crypto) |
| **Authentication** | None required | API Key & Secret required |
| **Reliability** | Moderate (Subject to Yahoo changes) | High (SLA provided) |
| **Identifier Support** | Tickers (requires exchange suffix, e.g., `SIE.DE`) | Tickers (US format) |

## 2. Analysis for This Project

### The "Global Coverage" Blocker
The decisive factor for this project is **European Market Data**.
*   **Alpaca:** The free/basic tier of Alpaca provides excellent data for US equities (NYSE, NASDAQ). However, it does **not** provide data for European exchanges (Xetra, Euronext Paris, LSE) where the project's UCITS ETFs are listed (e.g., `IE...`, `DE...`, `FR...` ISINs).
*   **yfinance:** Yahoo Finance aggregates data from almost all global exchanges. It supports suffixes like `.DE` (Xetra), `.PA` (Paris), `.L` (London), allowing us to fetch prices for the exact listing currency (EUR) of our ETFs.

### Project History
This trade-off was previously evaluated during the Proof of Concept phase. As noted in `docs/archive/poc-project-plan.md`:
> *"Price fetching: Live market prices via yfinance (switched from Alpaca for global support; includes suffixes like .DE and sanity checks)."*

## 3. Recommendation

**Stick with `yfinance`.**

Alpaca is not a viable option for this specific portfolio because it cannot price the European assets. While `yfinance` is less "official," its global coverage is a hard requirement. To make it robust, we must implement:
1.  **Ticker Mapping:** A reliable way to map ISINs to Yahoo Tickers (e.g., `FR0010361683` -> `CW8.PA` or similar).
2.  **Fallback Logic:** If a specific exchange ticker fails, try the US equivalent or a different exchange.
3.  **Caching:** Cache prices for at least 15-60 minutes to avoid hitting Yahoo's rate limits.
