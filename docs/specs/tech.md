# Technical Spec (The "How")

## 1. Technology Stack
*   **Language:** Python 3.9+ (per `pyproject.toml`)
*   **Core Libraries:**
    *   `pandas`: Data manipulation and aggregation.
    *   `pdfplumber`: PDF extraction (Trade Republic PDFs).
    *   `selenium` / `webdriver-manager`: Web scraping (legacy, mostly replaced by direct downloads).
    *   `yfinance`: Market data and pricing.
    *   `calamine`: High-performance Excel reading (Rust-based fallback for malformed XLSX).
*   **Data Storage:** CSV (primary), JSON (config/cache).

## 2. Forbidden Technologies (Anti-Patterns)
*   **FORBIDDEN:** `sys.path` hacks. **Reason:** Breaks packaging and testing; use installed module structure.
*   **FORBIDDEN:** Hardcoded Secrets. **Reason:** Security risk; use environment variables (`.env`) or local JSON config.
*   **FORBIDDEN:** Direct API calls in Logic. **Reason:** Violates Logic/IO separation; use Adapters/Providers.
*   **FORBIDDEN:** Bare `except:` clauses. **Reason:** Catches KeyboardInterrupt/SystemExit; use `except Exception:`.

## 3. Critical Libraries (Mandatory)
*   **Validation:** `pandera` (current), `pydantic` (target state for schema validation).
*   **Testing:** `pytest` (Unit & Integration).
*   **Linting:** `ruff` (Enforced via coding standards).

## 4. Architecture Standards
*   **Hybrid Data Sourcing:** Always support a Manual File Drop fallback for brittle scrapers.
*   **Logic/IO Separation:** Core calculation modules (`core/`) must be pure functions where possible.
*   **Cache-First:** All external data (Wikidata, Finnhub, Yahoo) must be cached with TTL.
*   **State-Awareness:** The system tracks its state in `.context/` and `data/working/`.
*   **Self-Learning:** Successfully resolved ISINs are harvested back to `asset_universe.csv`.

## 5. Rate Limits & Performance
*   **Finnhub API:** 60 calls/min (free tier) → Enforced 1.1s sleep between calls.
*   **Wikidata API:** No strict limit → 10s timeout per request.
*   **yfinance:** No hard limit → Batch requests ≤50 tickers for reliability.
*   **Tiered Enrichment:** Only holdings >1% weight get full ISIN resolution (reduces API calls by ~90%).
