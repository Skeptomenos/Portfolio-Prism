# Product Spec (The "Why")

## 1. Core Philosophy
*   **User Persona:** Private Investor managing a fragmented portfolio across multiple providers (Amundi, VanEck, iShares, etc.).
*   **Key Value:** A unified, automated "Single Pane of Glass" for portfolio exposure and valuation, independent of provider interfaces.
*   **Tone/Vibe:** Reliable, Private, Local-First, "Set and Forget".

## 2. Business Goals
*   [x] **Unified Reporting:** Aggregate holdings from PDF reports (Trade Republic) and Excel/CSV exports (VanEck, iShares, Brokers).
*   [x] **True Exposure:** "Look-through" capability to see underlying assets of ETFs (e.g., Apple exposure via S&P 500 ETF).
*   [x] **Automated Valuation:** Daily valuation updates using reliable public market data (Yahoo Finance).
*   [x] **ISIN Resolution:** Robust mapping of raw tickers/names to global ISINs using Wikidata and self-learning caches.

## 3. Anti-Goals (Critical: What we are NOT building)
*   [x] We are NOT building a Trading Bot (Read-only analysis).
*   [x] We are NOT building a SaaS (Local execution only).
*   [x] We are NOT storing data in the cloud (Zero-trust, local filesystem storage).
*   [x] We are NOT relying solely on expensive paid APIs (Bloomberg/Morningstar) -> Use Open Data/Scraping.

## 4. Key User Questions Answered

| Question | Answer Source |
|----------|---------------|
| "What do I actually own?" | `outputs/true_exposure_report.csv` |
| "Am I overweight in any single stock?" | `outputs/top_10_holdings.csv` |
| "What sectors am I exposed to?" | `outputs/sector_exposure.csv` |
| "What countries am I invested in?" | `outputs/geography_exposure.csv` |
| "Is my data accurate?" | `outputs/PIPELINE_HEALTH.md` |

## 5. Known Limitations
*   **Amundi ETFs:** Require manual file download due to anti-bot protection.
*   **Weekend/Holiday Pricing:** May be 1-2 days stale (last trading day).
*   **Non-Equity Components:** Bonds, commodities, derivatives classified as "Other".
*   **Currency Risk:** FX rates fetched at runtime; no historical tracking.
