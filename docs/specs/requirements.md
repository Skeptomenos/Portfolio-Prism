# Functional Requirements (The "What")
*Syntax: EARS (Easy Approach to Requirements Syntax)*

## 1. Ubiquitous Requirements (Always True)

### Core Invariants
*   **REQ-001:** The system shall accept a portfolio of holdings (ISINs + quantities) as input.
*   **REQ-002:** The system shall produce a true exposure report showing all underlying securities.
*   **REQ-003:** The system shall normalize all monetary values to EUR.
*   **REQ-004:** The system shall preserve total portfolio value within ±2% tolerance (input ≈ output).

### Data Sources
*   **REQ-005:** The system shall use `data/inputs/` as the primary source for portfolio files (PDFs, CSVs, XLSX).
*   **REQ-006:** The system shall maintain `config/asset_universe.csv` as the authoritative source for ISIN-to-Ticker mappings.
*   **REQ-007:** The system shall store all generated reports in `outputs/`.

## 2. Event-Driven Requirements (When... Then...)

### Pipeline Triggers
*   **REQ-010:** When `run_pipeline.py` is executed, the system shall load portfolio state, fetch prices, decompose ETFs, and generate reports.
*   **REQ-011:** When a PDF is placed in `data/inputs/portfolio/`, the parser shall extract all TRADE transactions.

### ETF Look-Through
*   **REQ-012:** When an ETF is encountered, the system shall fetch its underlying holdings via the appropriate adapter.
*   **REQ-013:** When an ETF adapter fails, the system shall log the failure and exclude that ETF from look-through (graceful degradation).
*   **REQ-014:** When a scraper fails (e.g., Amundi), the system shall check for a manual file fallback in `data/inputs/manual_holdings/`.

### ISIN Resolution
*   **REQ-015:** When an ISIN cannot be resolved locally, the system shall attempt resolution via Finnhub, then Wikidata.
*   **REQ-016:** When ISIN resolution succeeds, the system shall cache the result for future runs (self-learning).

## 3. State-Driven Requirements (While... Then...)
*   **REQ-020:** While processing ETF holdings, the system shall classify each as Equity, Cash, or Derivative.
*   **REQ-021:** While fetching prices, the system shall convert foreign currencies to EUR using live FX rates.
*   **REQ-022:** While enriching holdings, the system shall skip ISIN resolution for holdings with weight <1% (Tier 2 fallback).

## 4. Unwanted Behavior (If... Then... NOT)
*   **REQ-030:** If value conservation check fails (>2% drift), the system shall NOT silently continue but alert the user.
*   **REQ-031:** If a locally-resolved ISIN exists in `asset_universe.csv`, the system shall NOT overwrite it with API data.
*   **REQ-032:** If a holding has negative weight, the system shall NOT include it in aggregation.
*   **REQ-033:** If an adapter is marked "ignore" in the registry, the system shall NOT attempt to fetch holdings.
*   **REQ-034:** If an external API returns a rate limit error, the system shall NOT crash but log and continue.
