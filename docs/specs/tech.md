# Technical Spec (The "How")

## 1. Technology Stack
*   **Language:** Python 3.12+
*   **Core Libraries:**
    *   `pandas`: Data manipulation and aggregation.
    *   `pdfplumber`: PDF extraction (Amundi).
    *   `selenium` / `webdriver-manager`: Web scraping (Amundi download automation).
    *   `yfinance`: Market data and pricing.
    *   `calamine`: High-performance Excel reading (Rust-based).
*   **Database:** SQLite (Caching/State), CSV (Interchange/Storage).

## 2. Forbidden Technologies (Anti-Patterns)
*   **FORBIDDEN:** `sys.path` hacks. **Reason:** Breaks packaging and testing; use installed module structure.
*   **FORBIDDEN:** Hardcoded Secrets. **Reason:** Security risk; use environment variables or local JSON config.
*   **FORBIDDEN:** Direct API calls in Logic. **Reason:** Violates Logic/IO separation; use Adapters/Providers.

## 3. Critical Libraries (Mandatory)
*   **Validation:** `pydantic` (Target state for schema validation).
*   **Testing:** `pytest` (Unit & Integration).
*   **Linting:** `ruff` (Enforced via coding standards).

## 4. Architecture Standards
*   **Hybrid Data Sourcing:** Always support a Manual File Drop fallback for brittle scrapers.
*   **Logic/IO Separation:** Core calculation modules (`core/`) must be pure functions where possible.
*   **Cache-First:** All external data (Wikidata, Finnhub, Yahoo) must be cached with TTL.
*   **State-Awareness:** The system tracks its state in `.context/` and `data/working/`.
