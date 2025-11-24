# Plan: ISIN-Based Asset Normalization

**Objective:** Eliminate "polluted" asset names (e.g., "-38,94 ALPHABET...") and consolidation issues by ignoring the messy text from PDF exports and replacing it with standardized, official names fetched via ISIN.

## 1. Analysis of the Problem
*   **Current State:** We rely on Regex to scrape asset names from Trade Republic PDF descriptions. This is brittle because the layout changes (e.g., merged columns, price prefixing).
*   **Symptom:** We have multiple variants of the same asset (`ALPHABET INC.CL.A`, `ALPHABET INC CL C`) preventing proper aggregation, and names containing garbage data (`€10.00...`).
*   **Solution:** "Source of Truth" inversion. Instead of trusting the PDF text, we trust the ISIN (which is parsed reliably). We uses the ISIN to fetch the canonical name from a market data provider (Yahoo Finance).

## 2. Implementation Strategy

### Step 1: Create `NameNormalizer` Module
We will create a new utility `src/data/normalization.py` to handle this logic centrally.
*   **Input:** List of ISINs and Raw Names.
*   **Logic:**
    1.  **Check Cache:** Look in `config/asset_names.json`.
    2.  **Primary Layer (Deterministic):** Query `yfinance.Ticker(isin).info['longName']`.
    3.  **Secondary Layer (LLM Fallback):** If `yfinance` fails (or ISIN is missing), use an LLM to extract the clean name from the raw polluted string.
    4.  **Update Cache:** Save the result.
*   **Output:** Dictionary `{isin: clean_name}`.

### Step 2: Integrate into `setup_db.py`
We will modify the database population script to run this normalization step *before* saving positions.
*   **Current Flow:** Parse PDF -> `calculate_positions` -> Save to DB.
*   **New Flow:** Parse PDF -> `calculate_positions` -> **Normalize Names** -> Save to DB.
*   **Logic:**
    ```python
    # In setup_db.py
    positions_df = calculate_positions(...)
    
    # New Step
    from src.data.normalization import normalize_asset_names
    positions_df = normalize_asset_names(positions_df)
    
    to_sql(...)
    ```

### Step 3: Handle "No ISIN" Cases
For assets where ISIN parsing failed (rare) or the asset has no ISIN (Crypto?):
*   **Fallback:** The LLM Fallback layer will handle this by cleaning the raw text.
*   **Logging:** Log a warning so we can manually inspect/fix these edge cases.

## 3. Technical Components

### A. `config/asset_names.json`
A persistent cache to avoid hitting Yahoo/LLM API every time we rebuild the DB.
```json
{
  "US02079K3059": "Alphabet Inc. Class A",
  "IE00B4L5Y983": "iShares Core MSCI World UCITS ETF"
}
```

### B. `src/data/normalization.py`
```python
def normalize_asset_names(df):
    """
    Takes a DataFrame with 'ISIN' and 'NAME' columns.
    Updates 'NAME' with canonical data where possible.
    """
    # ... implementation ...
    # _fetch_yahoo(isin)
    # _fetch_llm(raw_name)
```

## 4. Benefits
1.  **Clean Dashboard:** "Alphabet Inc. Class A" looks professional.
2.  **Auto-Consolidation:** If TR lists "Alphabet" and "Google" separately but they share an ISIN, they will now merge perfectly.
3.  **Zero Maintenance:** No more Regex tweaking when TR changes their font size or column width.
4.  **LLM Resilience:** Even unknown/unmapped assets get cleaned names.

## 5. Execution Steps
1.  Create `src/data/normalization.py`.
2.  Modify `scripts/setup_db.py` to use it.
3.  Run `setup_db.py` (Database Rebuild).
4.  Verify `positions` table contains clean names.