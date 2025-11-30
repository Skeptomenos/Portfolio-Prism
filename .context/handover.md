# Handover: Pipeline Validation & Data Fix (TASK-015)

## Status: ✅ COMPLETE

The Data Pipeline validation logic has been fixed, and a critical data gap in the PDF input has been bridged using a manual workaround.

## Key Changes
1.  **Architecture:** Removed `state_manager.py` fallback logic. Pipeline no longer cheats by reading the truth file.
2.  **Validation:** `scripts/validate_pipeline.py` now compares Direct Holdings Quantities against `data/true_data/ground_truth_merged.csv`.
3.  **Manual Injection:** `scripts/parse_pdfs_to_csv.py` now checks for `data/inputs/manual_holdings/manual_positions.csv` and merges it with parsed results. This fixes the missing Microsoft, Amazon, etc. positions.

## Operational Notes
*   **Running the Pipeline:**
    ```bash
    python -m scripts.run_full_pipeline
    ```
*   **Running Validation:**
    ```bash
    python -m scripts.validate_pipeline
    ```
    *   *Expectation:* "VALIDATION PASSED" (Quantities match). Ignore Value Drift warnings.

## Known Issues (Market Data)
*   Some assets (TKMS, Cresco Labs, TAAT) are failing to get live prices from Yahoo Finance ("Delisted" or "No Data"). This causes Value Drift warnings but does not break the pipeline.

## Next Steps
*   **TASK-014 (Backlog):** Implement Vanguard ETF Adapter.
*   **Future:** If better PDFs (Depotauszug) become available, update the parser to remove the manual injection dependency.
