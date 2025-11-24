import yfinance as yf
import pandas as pd
import json
import os
import time
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

TICKER_MAP_PATH = "config/ticker_map.json"

def load_ticker_map():
    if os.path.exists(TICKER_MAP_PATH):
        with open(TICKER_MAP_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_ticker_map(map_data):
    with open(TICKER_MAP_PATH, 'w') as f:
        json.dump(map_data, f, indent=4)

def resolve_ticker(isin):
    """
    Tries to resolve an ISIN to a Yahoo Finance Ticker.
    1. Checks local map.
    2. Tries ISIN directly.
    3. Tries suffixes (.DE, .F).
    4. Asks user interactively.
    """
    ticker_map = load_ticker_map()
    
    # 1. Check Cache
    if isin in ticker_map:
        return ticker_map[isin]

    # 2. Auto-Discovery: Try ISIN directly
    try:
        t = yf.Ticker(isin)
        if hasattr(t, 'fast_info') and t.fast_info.get('last_price') is not None:
            print(f"    -> Found direct match: {isin}")
            ticker_map[isin] = isin
            save_ticker_map(ticker_map)
            return isin
    except:
        pass

    # 2b. Auto-Discovery: Try Suffixes
    suffixes = [".DE", ".F"]
    for suffix in suffixes:
        potential_ticker = f"{isin}{suffix}"
        try:
            t = yf.Ticker(potential_ticker)
            # Need to be gentle with checking validity to avoid false positives
            # fast_info is usually quick and reliable for "exists"
            if hasattr(t, 'fast_info') and t.fast_info.get('last_price') is not None:
                print(f"    -> Auto-resolved with suffix: {potential_ticker}")
                ticker_map[isin] = potential_ticker
                save_ticker_map(ticker_map)
                return potential_ticker
        except:
            pass

    # 3. Interactive Fallback
    print(f"  - Resolving ticker for {isin}...")
    user_input = input(f"    ⚠️  Could not auto-resolve ticker for {isin}.\n    Enter Yahoo Ticker (e.g., 'NESN.SW') or [s]kip: ").strip()
    
    if user_input and user_input.lower() != 's':
        # Validate user input
        try:
            t = yf.Ticker(user_input)
            hist = t.history(period="1d")
            if not hist.empty:
                print("    ✅ Verified.")
                ticker_map[isin] = user_input
                save_ticker_map(ticker_map)
                return user_input
            else:
                print(f"    ❌ Ticker '{user_input}' seems invalid or has no price data.")
        except Exception as e:
             print(f"    ❌ Error validating ticker: {e}")
    else:
        print("    -> Skipped.")
        
    return None

def _fetch_prices_batch(tickers):
    """
    Robust batch fetching with escalation strategy.
    Returns a dict {ticker: price}.
    """
    prices = {}
    remaining_tickers = [t for t in tickers if t] # Filter Nones
    
    if not remaining_tickers:
        return prices

    # Escalation Strategy: 1d -> 5d -> 1mo
    periods = ["1d", "5d", "1mo"]
    
    for period in periods:
        if not remaining_tickers:
            break
            
        logger.info(f"Fetching batch of {len(remaining_tickers)} tickers with period='{period}'...")
        
        try:
            # group_by='ticker' ensures we get a MultiIndex with Ticker as top level
            # threads=True enables parallel fetching
            data = yf.download(remaining_tickers, period=period, group_by='ticker', threads=True, progress=False)
            
            # If only one ticker, data structure is different (single level columns)
            # We standardize it
            if len(remaining_tickers) == 1:
                # Reconstruct dict-like access
                # But yf.download for 1 ticker returns just the dataframe
                # Let's handle it simply
                ticker = remaining_tickers[0]
                if not data.empty and 'Close' in data.columns:
                    last_valid = data['Close'].dropna().iloc[-1]
                    prices[ticker] = float(last_valid)
                    remaining_tickers = []
                continue

            # Multi-ticker handling
            found_in_batch = []
            for ticker in remaining_tickers:
                try:
                    # Access data for this ticker
                    # If failed, it might not be in columns or have all NaNs
                    if ticker in data.columns:
                        ticker_data = data[ticker]
                        if 'Close' in ticker_data.columns:
                            series = ticker_data['Close'].dropna()
                            if not series.empty:
                                prices[ticker] = float(series.iloc[-1])
                                found_in_batch.append(ticker)
                except Exception:
                    continue
            
            # Remove found tickers from the list for next iteration
            remaining_tickers = [t for t in remaining_tickers if t not in found_in_batch]
            
        except Exception as e:
            logger.error(f"Batch fetch failed for period {period}: {e}")

    # Fallback: Individual Fetch for stubborn tickers
    if remaining_tickers:
        logger.info(f"Falling back to individual fetch for {len(remaining_tickers)} tickers...")
        for ticker in remaining_tickers:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="1mo") # Go reasonably far back
                if not hist.empty:
                    prices[ticker] = float(hist['Close'].iloc[-1])
                    logger.debug(f"Recovered {ticker} via individual fetch.")
                else:
                    logger.warning(f"Failed to fetch price for {ticker} (Delisted or Invalid)")
            except Exception as e:
                 logger.warning(f"Error fetching {ticker}: {e}")
                 
    return prices

def get_price_map(isins):
    """
    Returns a dictionary {isin: price}.
    Resolves ISINs to Tickers first, then batch fetches prices.
    """
    logger.info(f"Resolving and fetching prices for {len(isins)} assets")
    
    # 1. Resolve all ISINs to Tickers
    isin_to_ticker = {}
    unique_tickers = set()
    
    for isin in isins:
        ticker = resolve_ticker(isin)
        if ticker:
            isin_to_ticker[isin] = ticker
            unique_tickers.add(ticker)
        else:
            logger.warning(f"⚠️  No price available for {isin} (Missing Ticker)")

    # 2. Fetch Prices for Unique Tickers (Batch)
    ticker_price_map = _fetch_prices_batch(list(unique_tickers))
    
    # 3. Map back to ISINs
    result = {}
    for isin, ticker in isin_to_ticker.items():
        if ticker in ticker_price_map:
            result[isin] = ticker_price_map[ticker]
        else:
            # Try to report why? (Already logged in batch fetch)
            pass
            
    return result

def fetch_current_price(isin):
    """Helper for single price (legacy support)"""
    res = get_price_map([isin])
    return res.get(isin)
