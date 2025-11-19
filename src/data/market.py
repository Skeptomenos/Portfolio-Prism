import yfinance as yf
import pandas as pd
import time
from typing import Optional, Dict

# Static mapping for the POC (Live Data Test)
# In a production system, this would be a database lookup or an external API search.
ISIN_TO_TICKER = {
    "DE0007500001": "TKA.DE",   # ThyssenKrupp
    "DE000A0F5UF5": "EXXT.DE",  # iShares NASDAQ-100 (DE)
    "US0079031078": "AMD",      # Advanced Micro Devices
    "US02079K3059": "GOOGL",    # Alphabet Class A
    "US67066G1040": "NVDA"      # NVIDIA
}

def fetch_current_price(isin: str) -> Optional[float]:
    """
    Fetches the current market price for a given ISIN using yfinance.
    Returns None if the ISIN is not mapped or the fetch fails.
    """
    ticker_symbol = ISIN_TO_TICKER.get(isin)
    
    if not ticker_symbol:
        print(f"  - ⚠️ WARNING: No ticker mapping found for ISIN {isin}. Using default price.")
        return None

    try:
        # Create a Ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Try fast info first (faster, no history download)
        price = None
        if hasattr(ticker, 'fast_info'):
             # Prioritize last_price, then previous_close
             price = ticker.fast_info.get('last_price')
             if not price:
                 price = ticker.fast_info.get('previous_close')
        
        # Fallback to history if fast_info fails (e.g., old yfinance version)
        if price is None:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]

        if price:
            # print(f"  - Fetched price for {isin} ({ticker_symbol}): {price:.2f}")
            return price
        else:
            print(f"  - ❌ FAILED: Could not retrieve price data for {ticker_symbol}")
            return None

    except Exception as e:
        print(f"  - ❌ ERROR: yfinance failed for {ticker_symbol}: {e}")
        return None

def get_price_map(isins: list) -> Dict[str, float]:
    """
    Batch fetches prices for a list of ISINs. 
    Returns a dictionary {isin: price}.
    """
    price_map = {}
    print(f"--- MarketData: Fetching live prices for {len(isins)} assets ---")
    
    for isin in isins:
        price = fetch_current_price(isin)
        if price is not None:
            price_map[isin] = price
            # Small sleep to be polite to Yahoo
            time.sleep(0.2) 
        else:
            # Fallback to a dummy price? No, let the caller handle missing data.
            # For the POC, we might just default to 100.0 if missing to avoid crashes,
            # but ideally we want to know.
            pass
            
    return price_map

if __name__ == "__main__":
    # Test the module
    test_isins = list(ISIN_TO_TICKER.keys())
    prices = get_price_map(test_isins)
    print("\nResults:")
    for isin, price in prices.items():
        print(f"{isin}: {price}")
