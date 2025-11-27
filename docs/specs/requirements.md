# Functional Requirements (The "What")
*Syntax: EARS (Easy Approach to Requirements Syntax)*

## 1. Ubiquitous Requirements (Always True)
*   **REQ-001:** The system shall use `data/inputs/` as the primary source for portfolio files (PDFs, CSVs, XLSX).
*   **REQ-002:** The system shall maintain `config/asset_universe.csv` as the authoritative source for ISIN-to-Ticker mappings.
*   **REQ-003:** The system shall store all generated reports in `outputs/` with timestamps.

## 2. Event-Driven Requirements (When... Then...)
*   **REQ-004:** When a new PDF report is detected in `data/inputs/portfolio/`, the system shall parse it to extract holdings, quantity, and dates.
*   **REQ-005:** When an ISIN cannot be resolved locally, the system shall query Wikidata using the asset name and raw ticker.
*   **REQ-006:** When the `run_pipeline.py` script is executed, the system shall aggregate all holdings and generate a `true_exposure_report.csv`.
*   **REQ-007:** When a scraper fails (e.g., Amundi Login), the system shall check for a manual file fallback in `data/inputs/manual_holdings/`.

## 3. State-Driven Requirements (While... Then...)
*   **REQ-008:** While parsing Amundi PDFs, the system shall use spatial heuristics (pixel thresholds) to group lines correctly.
*   **REQ-009:** While fetching prices, the system shall normalize all currencies to EUR.

## 4. Unwanted Behavior (If... Then... NOT)
*   **REQ-010:** If an external API returns a rate limit error, the system shall NOT crash but retry with backoff or skip and log a warning.
*   **REQ-011:** If a ticker is missing from `asset_universe.csv`, the system shall NOT drop the holding silently but flag it for "Harvesting".
