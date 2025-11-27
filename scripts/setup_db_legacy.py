"""DEPRECATED: This script uses the old SQLite workflow.

The project now uses CSV-based state management.
For PDF parsing, use: scripts/parse_pdfs_to_csv.py (when available)

This file is kept for rollback purposes only.
"""

import sqlite3
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_parser.parser import main as run_pdf_parser
from src.core.position_keeper import calculate_positions
from src.pdf_parser.utils import parse_description
import json


# DEPRECATED: database module was removed in Phase 11
# These stubs are added for syntax validation - this script should NOT be run
def get_all_trades():
    """Stub for removed database function."""
    raise NotImplementedError("Database module removed. Use CSV workflow instead.")


def init_db():
    """Stub for removed database function."""
    raise NotImplementedError("Database module removed. Use CSV workflow instead.")


DATABASE_PATH = "data/working/database/portfolio.db"
PDF_INPUT_DIR = "data/inputs/portfolio"
CONFIG_PATH = "config/adapter_registry.json"


def run_live_population():
    """
    Parses live PDF data (incrementally), calculates positions, and saves them to the database.
    """
    print("--- Starting live data population process ---")

    # Initialize DB Schema
    init_db()

    # Step 1: Incremental Parse (Update 'trades' table in DB)
    print(f"1. Updating Database from PDFs in '{PDF_INPUT_DIR}'...")
    # The parser script needs to be run from the root, so we change dir temporarily
    original_cwd = os.getcwd()
    os.chdir(PROJECT_ROOT)

    # Inject arguments for the parser
    sys.argv = ["parser.py", "--input_folder", PDF_INPUT_DIR]
    run_pdf_parser()

    os.chdir(original_cwd)

    # Step 2: Fetch and Parse Trades from DB
    print("2. Calculating positions from Database...")
    raw_trades = get_all_trades()
    if raw_trades.empty:
        print("   - No trades found in database. Exiting.")
        return

    # Filter for 'TRADE' type and parse descriptions
    # Note: Column names in DB are lowercase (date, type, description...)

    trade_rows = raw_trades[raw_trades["type"] == "TRADE"].copy()
    if trade_rows.empty:
        print("   - No execution trades found (only cash transactions?).")
        return

    parsed_data = trade_rows["description"].apply(parse_description)

    # Reconstruct the DataFrame expected by calculate_positions
    # It expects: ISIN, NAME, QUANTITY, PRICE, TRADE_TYPE, DATE
    parsed_df = pd.DataFrame(parsed_data.tolist(), index=trade_rows.index)
    parsed_df["DATE"] = trade_rows["date"]

    # Rename cols to match position_keeper expectation (Upper Case)
    parsed_df.rename(
        columns={
            "isin": "ISIN",
            "name": "NAME",
            "quantity": "QUANTITY",
            "price": "PRICE",
            "trade_type": "TRADE_TYPE",
        },
        inplace=True,
    )

    positions_df = calculate_positions(parsed_df)

    # Normalize Asset Names (ISIN Lookup)
    print("2a. Normalizing asset names...")
    from src.data.normalization import normalize_asset_names

    positions_df = normalize_asset_names(positions_df)

    # Step 3: Classify assets as Stock or ETF
    print("3. Classifying assets...")
    with open(CONFIG_PATH, "r") as f:
        adapter_registry = json.load(f)
    etf_isins = {k for k, v in adapter_registry.items() if v != "ignore"}
    positions_df["asset_type"] = positions_df["ISIN"].apply(
        lambda x: "ETF" if x in etf_isins else "Stock"
    )

    # Step 4: Save to database
    print(f"4. Saving {len(positions_df)} positions to '{DATABASE_PATH}'...")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        positions_df.to_sql("positions", conn, if_exists="replace", index=False)
        conn.close()
        print("   - Positions successfully saved to the database.")
    except Exception as e:
        print(f"   - FAILED to save to database: {e}")
        return

    # Step 5: Verify by reading the data back
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        read_df = pd.read_sql_query("SELECT * FROM positions", conn)
        conn.close()
        print("\n--- Verification successful. Data in DB: ---")
        print(read_df.head())
        print(f"\nTotal positions found: {len(read_df)}")
        print("--- Live data population complete. ---")
    except Exception as e:
        print(f"--- Verification failed: {e} ---")


if __name__ == "__main__":
    # We are now running the live data population by default.
    run_live_population()
