# Finnhub API Analysis

**Date:** November 19, 2025
**Source:** [Finnhub Pricing](https://finnhub.io/pricing) & [API Documentation](https://finnhub.io/docs/api/introduction)

## 1. Overview
Finnhub is a stock market data provider offering a wide range of financial data including real-time stock prices, fundamental data, and alternative data. While it offers a generous free tier compared to some competitors, it has strict limitations that impact its viability for comprehensive, global portfolio analysis without a paid subscription.

## 2. Free Tier Limitations (The "Sandbox" Plan)

### Rate Limits
*   **Limit:** 60 API calls per minute.
*   **Implication:** This is effectively **1 call per second**.
*   **Impact on Project:** Our current `enrichment.py` script processes securities in a loop. For a portfolio with >60 underlying assets (common with S&P 500 or World ETFs), the script currently hits this limit almost immediately, resulting in `429 Too Many Requests` errors.
*   **Headers:** Responses include `X-Ratelimit-Limit` and `X-Ratelimit-Remaining` headers to track usage.

### Market Coverage
*   **Scope:** Primarily **US Market** data.
*   **International Data:** Real-time or delayed data for international exchanges (LSE, Euronext, Xetra, etc.) is generally **restricted** to the "All-In-One" premium plan.
*   **Impact on Project:** Our portfolio contains European assets (e.g., `FR...`, `DE...`, `IE...` ISINs). The free tier returns "Symbol not found" or empty data for many of these non-US tickers, leading to "Unknown" sectors and geographies in our reports.

## 3. Endpoint Availability

### Available on Free Tier
*   **Company Profile 2 (`/stock/profile2`):** Basic metadata (Sector, Country, Currency, Ticker, Share Outstanding). *Note: Coverage is good for US stocks, spotty for International.*
*   **Quote (`/quote`):** Real-time price data for US stocks.
*   **Candles/OHLC (`/stock/candle`):** Historical price data (1 year limit on some granularities).
*   **Company News:** Last 1 year.
*   **Basic Financials:** "As Reported" financials.

### Restricted (Premium Only)
*   **ETF Holdings:** Full constituent lists for ETFs. *Critical: This forces us to build our own adapters.*
*   **ETF Sector/Country Exposure:** Pre-calculated exposure data.
*   **Global Market Data:** comprehensive data for non-US exchanges.
*   **Company Profile 1:** Detailed profile data.
*   **Dividends:** Historical dividend data.

## 4. Strategic Recommendations

### Short Term (Current POC)
1.  **Throttling:** Implement a rate-limiter in `enrichment.py` to enforce a max of 1 request per second.
2.  **Caching:** Maximize reliance on `enrichment_cache.json` to avoid hitting the API for static metadata.
3.  **Error Handling:** Gracefully handle 429s with exponential backoff.

### Long Term
1.  **Hybrid Approach:** Finnhub is insufficient for a European-centric portfolio. We need to integrate a second free API that covers EU markets (e.g., Yahoo Finance via `yfinance` is currently used for prices, but could potentially be mined for metadata).
2.  **Symbol Mapping:** We need a robust way to map ISINs to the specific ticker format Finnhub expects (e.g., mapping a German stock `DE...` to its US listing if available, or accepting that we cannot get data for it from Finnhub).
