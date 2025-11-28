import os
import requests
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_API_URL = "https://finnhub.io/api/v1"


def test_finnhub(isin):
    print(f"Testing Finnhub for {isin}...")
    if not FINNHUB_API_KEY:
        print("Error: FINNHUB_API_KEY not found.")
        return

    try:
        response = requests.get(
            f"{FINNHUB_API_URL}/stock/profile2",
            params={"symbol": isin, "token": FINNHUB_API_KEY},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Finnhub Response: {data}")
        else:
            print(f"Finnhub Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Finnhub Exception: {e}")


def test_yfinance(isin):
    print(f"Testing YFinance for {isin}...")
    try:
        # YFinance often needs a ticker, but sometimes works with ISIN if mapped.
        # Ideally we need a Ticker. Let's try searching first?
        # Or just try the ISIN directly which sometimes works if yfinance does lookup.
        # Actually, yfinance Ticker object expects a ticker.
        # We might need a way to convert ISIN to Ticker.

        # Attempt 1: Direct ISIN (Unlikely to work without suffix)
        ticker = yf.Ticker(isin)
        info = ticker.info
        print(
            f"YFinance Direct ISIN Response: sector={info.get('sector')}, country={info.get('country')}"
        )

        # Attempt 2: Search
        # Search is not directly exposed in Ticker object nicely.
    except Exception as e:
        print(f"YFinance Exception: {e}")


if __name__ == "__main__":
    test_isins = [
        "US0378331005",  # Apple (US Stock)
        "IE00B4L5Y983",  # iShares Core MSCI World (ETF)
        "DE0007030009",  # Rheinmetall (DE Stock)
    ]
    for isin in test_isins:
        print(f"\n--- Testing {isin} ---")
        test_finnhub(isin)
        test_yfinance(isin)
