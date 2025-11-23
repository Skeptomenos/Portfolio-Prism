# Quickstart Guide

## 1. Prerequisites
*   Python 3.9+
*   `pip`
*   (Optional) `venv`

## 2. Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Setup Data
1.  **Portfolio:** Place your Trade Republic PDF exports (e.g., `Umsatzübersicht.pdf`) in:
    ```
    data/inputs/portfolio/
    ```
2.  **ETF Data (Amundi Only):** If you own Amundi ETFs, download the "Zusammensetzung" (Holdings) XLSX file from the Amundi website and save it to:
    ```
    data/inputs/manual_holdings/{ISIN}.xlsx
    ```
    *Example: `data/inputs/manual_holdings/FR0010361683.xlsx`*

## 4. Run the Pipeline
Run the master script to parse PDFs, update the database, and generate the report:

```bash
bash run.sh
```

> **Note:** If the system detects a new ETF in your portfolio that it hasn't seen before, it will pause and ask you to select the correct provider (e.g., iShares, Amundi). Your choice will be saved for future runs.

## 5. View Results
The analysis is saved to the `outputs/` directory:
*   `outputs/true_exposure_report.csv`: Full look-through exposure list.
*   `outputs/data_quality_report.txt`: Details of any missing data.
*   `outputs/trades.csv`: Parsed transaction history.

## 6. Troubleshooting
*   **Amundi Errors:** Ensure the manual XLSX file is in `data/inputs/manual_holdings/` and is a valid Excel file.