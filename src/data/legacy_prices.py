import pandas as pd
import yfinance as yf


def fetch_latest_prices(tickers: list, providers: list = None) -> pd.DataFrame:
    """
    Fetches the latest prices for a list of tickers using yfinance (Yahoo Finance).
    Tries base ticker, then with exchange suffix based on provider.
    """
    prices = []
    for i, ticker in enumerate(tickers):
        price = None
        provider = providers[i] if providers and i < len(providers) else None

        # Try base ticker
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if not data.empty:
                price = data["Close"].iloc[-1]
                if not (0.01 < price < 1000):
                    price = None
        except:
            pass

        # If not found, try with suffix
        if price is None and provider:
            suffix = get_exchange_suffix(provider)
            if suffix:
                try:
                    data = yf.Ticker(f"{ticker}{suffix}").history(period="1d")
                    if not data.empty:
                        price = data["Close"].iloc[-1]
                        if not (0.01 < price < 1000):
                            price = None
                except:
                    pass

        prices.append({"TICKER": ticker, "PRICE": price})

    return pd.DataFrame(prices)


def get_exchange_suffix(provider: str) -> str:
    """
    Returns Yahoo suffix for exchange code.
    """
    mapping = {
        "GR": ".DE",  # Germany
        "LN": ".L",  # London
        "SW": ".SW",  # Switzerland
        "NA": ".AS",  # Amsterdam
        "IM": ".MI",  # Milan
        "XV": ".PA",  # Paris
        "XF": ".BR",  # Brussels
        "US": "",  # US
    }
    return mapping.get(provider, "")
