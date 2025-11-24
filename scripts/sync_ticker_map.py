import json
import pandas as pd
import os
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

UNIVERSE_PATH = "config/asset_universe.csv"
TICKER_MAP_PATH = "config/ticker_map.json"

def sync_map():
    logger.info("--- Syncing Ticker Map from Asset Universe ---")
    
    if not os.path.exists(UNIVERSE_PATH):
        logger.error(f"Universe file not found: {UNIVERSE_PATH}")
        return

    # Load Universe
    df = pd.read_csv(UNIVERSE_PATH)
    
    # Load existing map
    if os.path.exists(TICKER_MAP_PATH):
        with open(TICKER_MAP_PATH, 'r') as f:
            ticker_map = json.load(f)
    else:
        ticker_map = {}
        
    updates = 0
    for _, row in df.iterrows():
        isin = row['ISIN']
        yahoo_ticker = row['Yahoo_Ticker']
        
        # We only sync if we have a valid Yahoo Ticker
        if pd.notna(yahoo_ticker) and yahoo_ticker != "-":
            # If mapping doesn't exist or is different, update it
            if isin not in ticker_map or ticker_map[isin] != yahoo_ticker:
                ticker_map[isin] = yahoo_ticker
                updates += 1
                
    # Save
    with open(TICKER_MAP_PATH, 'w') as f:
        json.dump(ticker_map, f, indent=4)
        
    logger.info(f"Synced {updates} tickers to {TICKER_MAP_PATH}")

if __name__ == "__main__":
    sync_map()
