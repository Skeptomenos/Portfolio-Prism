# Product Spec (The "Why")

## 1. Core Philosophy
*   **User Persona:** Private Investor managing a fragmented portfolio across multiple providers (Amundi, VanEck, iShares, etc.).
*   **Key Value:** A unified, automated "Single Pane of Glass" for portfolio exposure and valuation, independent of provider interfaces.
*   **Tone/Vibe:** Reliable, Private, Local-First, "Set and Forget".

## 2. Business Goals
*   [ ] **Unified Reporting:** Aggregate holdings from PDF reports (Amundi) and Excel/CSV exports (VanEck, iShares, Brokers).
*   [ ] **True Exposure:** "Look-through" capability to see underlying assets of ETFs (e.g., Apple exposure via S&P 500 ETF).
*   [ ] **Automated Valuation:** Daily valuation updates using reliable public market data (Yahoo Finance).
*   [ ] **ISIN Resolution:** Robust mapping of raw tickers/names to global ISINs using Wikidata and self-learning caches.

## 3. Anti-Goals (Critical: What we are NOT building)
*   [ ] We are NOT building a Trading Bot (Read-only analysis).
*   [ ] We are NOT building a SaaS (Local execution only).
*   [ ] We are NOT storing data in the cloud (Zero-trust, local filesystem storage).
*   [ ] We are NOT relying solely on expensive paid APIs (Bloomberg/Morningstar) -> Use Open Data/Scraping.
