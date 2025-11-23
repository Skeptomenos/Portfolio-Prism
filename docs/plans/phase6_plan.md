# Phase 6 Plan: Reliability & Gap Closure

**Objective:** Address all known data gaps and stability issues identified during the Phase 5 analysis. The goal is to achieve a "Zero Noise, Zero Data Loss" pipeline state.

## 1. Clean Up Configuration
*   **Task:** Remove the dummy test case (`DE0007500001` -> `vanguard`) from `config/adapter_registry.json`.
*   **Reason:** It was a test artifact and is causing "Provider not supported" warnings for a valid stock (ThyssenKrupp).

## 2. Silence the Noise (Enrichment Filtering)
*   **Problem:** The enrichment layer hammers the Yahoo Finance API with requests for `_CURRENCY...` and `NON_EQUITY...` identifiers, causing 404 errors and slowing down the run.
*   **Solution:** Update `src/data/enrichment.py`.
    *   **Logic:** In `enrich_securities_bulk`, inspect the `identifier` before making a request.
    *   **Filter:** Skip if `identifier` starts with `_` (e.g., `_CURRENCYUSD`) or contains `NON_EQUITY`.
    *   **Result:** Cleaner logs and faster execution.

## 3. Fix Direct Holdings Pricing (Ticker Mapping)
*   **Problem:** Direct holdings like `FR0010361683` (Lyxor ETF) fail price lookups because `yfinance` needs a ticker (e.g., `CW8.PA`), not an ISIN.
*   **Solution:** Enable the Interactive Ticker Mapper.
    *   **Context:** The logic *already exists* in `src/data/market.py` (`resolve_ticker`), but it's not being triggered effectively or the user isn't prompted.
    *   **Task:** Verify `resolve_ticker` is called for direct holdings. If `yfinance` returns no data for an ISIN, the system MUST prompt the user to input the correct ticker and save it to `config/ticker_map.json`.

## 4. Automate iShares Discovery (The Big Gap)
*   **Problem:** ~2.6% of portfolio value is lost because iShares adapters need a `product_id` (e.g., `251795`) to fetch data, and this ID is currently manual.
*   **Solution:** Implement "Provider-Specific Discovery".
    *   **Component:** `src/adapters/ishares.py`
    *   **New Logic:** `_discover_product_id(isin)`
        1.  Use `requests` to search the iShares website (or Google via a scraping pattern) for the ISIN.
        2.  Parse the search result URL to extract the ID pattern (`/produkte/(\d+)/`).
        3.  Automatically update `config/ishares_config.json` and retry.
    *   **Fallback:** Keep the manual prompt only as a last resort.

## 5. Verification
*   **Success Metrics:**
    1.  **Value Conservation:** Should be >99% (currently ~97.4%).
    2.  **Log Cleanliness:** Zero "HTTP Error 404" for known non-equity assets.
    3.  **No "Skipped" Assets:** All valid holdings (including ThyssenKrupp) are processed.
