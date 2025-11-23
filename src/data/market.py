import yfinance as yf
import pandas as pd
import time
import json
import os
import sys
from typing import Optional, Dict

# Add project root to path to locate config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TICKER_MAP_PATH = os.path.join(project_root, 'config', 'ticker_map.json')

def load_ticker_map() -> Dict[str, str]:
    if os.path.exists(TICKER_MAP_PATH):
        try:
            with open(TICKER_MAP_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_ticker_map(mapping: Dict[str, str]):
    try:
        os.makedirs(os.path.dirname(TICKER_MAP_PATH), exist_ok=True)
        with open(TICKER_MAP_PATH, 'w') as f:
            json.dump(mapping, f, indent=2)
    except Exception as e:
        print(f"Error saving ticker map: {e}")

def resolve_ticker(isin: str) -> Optional[str]:
    """
    Resolves an ISIN to a Yahoo Finance Ticker.
    1. Checks local config/ticker_map.json
    2. Tries using ISIN directly
    3. Prompts user (if interactive)
    """
    ticker_map = load_ticker_map()
    
    # 1. Check Cache
    if isin in ticker_map:
        return ticker_map[isin]
    
    print(f"  - Resolving ticker for {isin}...")

    # 2. Auto-Discovery: Try ISIN directly
    try:
        t = yf.Ticker(isin)
        # Check if valid by hitting fast_info or history
        # Note: info is slow, fast_info is better
        if hasattr(t, 'fast_info') and t.fast_info.get('last_price') is not None:
            print(f"    -> Found direct match: {isin}")
            ticker_map[isin] = isin
            save_ticker_map(ticker_map)
            return isin
    except:
        pass

    # 3. Interactive Fallback
    if sys.stdout.isatty():
        print(f"    ⚠️  Could not auto-resolve ticker for {isin}.")
        user_input = input(f"    Enter Yahoo Ticker (e.g., 'NESN.SW') or [s]kip: ").strip()
        if user_input and user_input.lower() != 's':
            # Validate?
            try:
                t = yf.Ticker(user_input)
                valid = False
                
                # Check fast_info
                if hasattr(t, 'fast_info') and t.fast_info.get('last_price') is not None:
                    valid = True
                else:
                    # Fallback to history
                    hist = t.history(period="1d")
                    if not hist.empty:
                        valid = True
                
                if valid:
                    print(f"    ✅ Verified.")
                    ticker_map[isin] = user_input
                    save_ticker_map(ticker_map)
                    return user_input
                else:
                    print(f"    ❌ Ticker '{user_input}' seems invalid or has no price data.")
            except Exception as e:
                print(f"    ❌ Validation error: {e}")
        else:
            print("    -> Skipped.")
            # Optionally save as "ignore" to stop asking?
            # For now, let's just return None.
            
    return None

def fetch_current_price(ticker_symbol: str) -> Optional[float]:
    """
    Fetches the current market price for a given Ticker.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        price = None
        
        # Try fast info first
        if hasattr(ticker, 'fast_info'):
             price = ticker.fast_info.get('last_price')
             if not price:
                 price = ticker.fast_info.get('previous_close')
        
        # Fallback to history
        if price is None:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]

        return price

    except Exception as e:
        print(f"  - ❌ ERROR: yfinance failed for {ticker_symbol}: {e}")
        return None

def get_price_map(isins: list) -> Dict[str, float]:
    """
    Batch fetches prices for a list of ISINs. 
    Returns a dictionary {isin: price}.
    """
    price_map = {}
    print(f"--- MarketData: Resolving and fetching prices for {len(isins)} assets ---")
    
    for isin in isins:
        ticker = resolve_ticker(isin)
        
        if ticker:
            price = fetch_current_price(ticker)
            if price is not None:
                price_map[isin] = price
                # print(f"  - {isin} ({ticker}): €{price:.2f}")
            else:
                print(f"  - ❌ Failed to fetch price for {ticker}")
            
            time.sleep(0.1) # Rate limit politeness
        else:
            print(f"  - ⚠️  No price available for {isin} (Missing Ticker)")
            
    return price_map

if __name__ == "__main__":
    # Test the module
    test_isins = ["DE0007500001", "INVALID123"]
    prices = get_price_map(test_isins)
    print("\nResults:")
    print(prices)