# Plan: Comprehensive Holdings List (Direct Positions)

**Objective:** Generate a clear, audit-ready CSV (`outputs/direct_holdings_report.csv`) listing every asset the user *directly* owns. This serves as the "Level 1" view of the portfolio, distinct from the "Level 2" look-through exposure.

## 1. Purpose & Value
*   **Auditability:** Verify that the input quantities and fetched prices match reality.
*   **Validation:** Identify if a specific ETF's market value is being miscalculated (leading to downstream exposure errors like the Nvidia 100x bug).
*   **Simplicity:** A simple table to answer "What do I own and what is it worth today?"

## 2. Data Schema
The output CSV will have the following columns:

| Column | Description | Source |
| :--- | :--- | :--- |
| **ISIN** | Unique Identifier | `portfolio_holdings.csv` / Universe |
| **Name** | Display Name | `asset_universe.csv` |
| **Ticker** | Yahoo Ticker used for pricing | `asset_universe.csv` |
| **Asset_Class** | Stock vs ETF | `asset_universe.csv` |
| **Quantity** | Number of units held | `portfolio_holdings.csv` |
| **Price** | Current Market Price (EUR) | Live `yfinance` Fetch |
| **Market_Value** | `Quantity * Price` | Calculated |
| **Portfolio_Weight** | `Market_Value / Total_Portfolio_Value` | Calculated |
| **Provider** | Issuer (for ETFs only) | `asset_universe.csv` |

## 3. Implementation Strategy

### Location
We will implement this within `src/core/reporting.py` or a new module `src/core/direct_reporting.py`. Given the existing structure, extending `reporting.py` is cleanest.

### Logic Flow
1.  **Input:** Receive the `all_positions` DataFrame from `run_pipeline.py` (Phase 2 output). This DataFrame already contains the joined Universe + Holdings + Live Prices.
2.  **Processing:**
    *   Filter for relevant columns.
    *   Sort by `Market_Value` (Descending).
    *   Calculate `Total_Value` (Sum).
    *   Calculate `Portfolio_Weight` (Row / Total).
3.  **Output:** Save to `outputs/direct_holdings_report.csv`.

## 4. Integration into Pipeline
We will insert this step **after Phase 2 (Market Data)** and **before Phase 3 (Aggregation)** in `scripts/run_pipeline.py`. This ensures we capture the state *before* look-through adds complexity.

### Code Snippet (Concept)
```python
def generate_direct_holdings_report(all_positions, output_path):
    # ...
    df = all_positions.copy()
    total_val = df['market_value'].sum()
    df['weight'] = df['market_value'] / total_val
    # ... formatting ...
    df.to_csv(output_path, index=False)
```

## 5. Success Criteria
*   The file exists: `outputs/direct_holdings_report.csv`.
*   The sum of `Market_Value` equals the Total Portfolio Value (~€45k).
*   We can clearly see if `iShares Core MSCI World` is valued at €13k (correct) or €1.3M (incorrect).

## 6. Immediate Action
1.  Create `src/core/direct_reporting.py`.
2.  Hook it into `run_pipeline.py`.
3.  Run pipeline and inspect the new report.
