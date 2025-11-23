# phases/active/data_manager.py
import pandas as pd
import sqlite3
from typing import Tuple

DATABASE_PATH = "data/working/database/portfolio.db"

def load_positions_from_db() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Connects to the SQLite database and loads the user's positions.

    Returns:
        A tuple containing two DataFrames:
        - direct_positions: Stocks and other direct holdings.
        - etf_positions: ETF holdings.
    """
    print(f"--- DataManager: Loading positions from {DATABASE_PATH} ---")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        # Updated query to match the actual schema of the populated database
        # Schema: ISIN, name, total_quantity, average_purchase_price, asset_type
        # We map:
        # - ISIN -> isin
        # - total_quantity -> quantity
        # - average_purchase_price -> current_price (as a temporary proxy for testing)
        query = """
            SELECT 
                ISIN as isin, 
                name, 
                total_quantity as quantity, 
                average_purchase_price,
                asset_type
            FROM positions
        """
        all_positions = pd.read_sql_query(query, conn)
        conn.close()

        print(f"  - Loaded {len(all_positions)} total positions from the database.")

        # Initialize current_price with None (to be filled by market data)
        # We essentially discard the purchase price as a proxy for current value
        all_positions['current_price'] = None
        
        # Initialize market_value to 0.0 (will be calculated later if price is found)
        all_positions['market_value'] = 0.0

        # Split positions into direct and ETF based on the 'asset_type' column
        direct_positions = all_positions[all_positions['asset_type'] != 'ETF'].copy()
        etf_positions = all_positions[all_positions['asset_type'] == 'ETF'].copy()

        print(f"  - Identified {len(direct_positions)} direct positions.")
        print(f"  - Identified {len(etf_positions)} ETF positions.")

        return direct_positions, etf_positions

    except sqlite3.Error as e:
        print(f"❌ FAILED: Database error while loading positions: {e}")
        # Return empty DataFrames on failure
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        print(f"❌ FAILED: An unexpected error occurred in DataManager: {e}")
        return pd.DataFrame(), pd.DataFrame()

if __name__ == '__main__':
    # Standalone test for the data manager
    direct, etfs = load_positions_from_db()
    
    print("\n--- Direct Positions ---")
    print(direct.head())
    
    print("\n--- ETF Positions ---")
    print(etfs.head())