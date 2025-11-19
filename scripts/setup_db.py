import sqlite3
import pandas as pd
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.pdf_parser.parser import main as run_pdf_parser
from src.core.position_keeper import calculate_positions
import json

DATABASE_PATH = "data/working/database/portfolio.db"
PDF_INPUT_DIR = "data/inputs/portfolio"
TRADES_OUTPUT_PATH = "outputs/trades.csv"
CONFIG_PATH = "config/adapter_registry.json"

def run_live_population():
    """
    Parses live PDF data, calculates positions, and saves them to the database.
    """
    print("--- Starting live data population process ---")
    
    # Step 1: Parse all PDFs to generate trades.csv
    print(f"1. Parsing all PDFs from '{PDF_INPUT_DIR}'...")
    # The parser script needs to be run from the root, so we change dir temporarily
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    # Inject arguments for the parser
    sys.argv = ["parser.py", "--input_folder", PDF_INPUT_DIR]
    run_pdf_parser()
    
    os.chdir(original_cwd)
    print(f"   - Trades saved to '{TRADES_OUTPUT_PATH}'.")
    
    # Step 2: Calculate positions from trades.csv
    print("2. Calculating positions from trades...")
    trades_df = pd.read_csv(TRADES_OUTPUT_PATH)
    positions_df = calculate_positions(trades_df)
    
    # Step 3: Classify assets as Stock or ETF
    print("3. Classifying assets...")
    with open(CONFIG_PATH, 'r') as f:
        adapter_registry = json.load(f)
    etf_isins = adapter_registry.keys()
    positions_df['asset_type'] = positions_df['ISIN'].apply(lambda x: 'ETF' if x in etf_isins else 'Stock')
    
    # Step 4: Save to database
    print(f"4. Saving {len(positions_df)} positions to '{DATABASE_PATH}'...")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        positions_df.to_sql('positions', conn, if_exists='replace', index=False)
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


if __name__ == '__main__':
    # We are now running the live data population by default.
    run_live_population()
