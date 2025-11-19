# holdings_engine/adapters/ishares.py

import requests
import pandas as pd
import json
from src.data.caching import cache_adapter_data
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# This mapping contains the unique identifiers needed to construct the download URL.
# It was discovered during the feasibility spike and can be expanded.
ISHARES_ETF_DATA = {
    "IWDA": {"product_id": "251882", "region": "de", "user_type": "privatanleger", "isin": "IE00B4L5Y983"},
    "SXR8": {"product_id": "251900", "region": "de", "user_type": "privatanleger", "isin": "IE00B5BMR087"},
    "IUSA_DIST": {"product_id": "251900", "region": "de", "user_type": "privatanleger", "isin": "IE0031442068"}, # Mapped to Acc version (holdings are identical)
    "IUIT": {"product_id": "280510", "region": "de", "user_type": "privatanleger", "isin": "IE00B3WJKG14"},
    "CSNDX": {"product_id": "251903", "region": "de", "user_type": "privatanleger", "isin": "IE00B53SZB19"},
    # Add other iShares ETFs here as needed
}

class ISharesAdapter:
    """
    Adapter for fetching ETF holdings data from iShares.
    This adapter uses the "Layer 1: Direct Download" strategy based on a
    predictable URL pattern discovered during the feasibility spike.
    """

    @cache_adapter_data(ttl_hours=24)
    def fetch_holdings(self, isin: str) -> pd.DataFrame:
        """
        Fetches the holdings for a given iShares ETF ISIN.

        Args:
            isin: The ISIN of the ETF.

        Returns:
            A pandas DataFrame containing the ETF holdings, or an empty DataFrame if fetching fails.
        """
        logger.info(f"--- Fetching holdings for {isin} ---")

        # Find the ticker associated with the ISIN
        ticker = next((t for t, data in ISHARES_ETF_DATA.items() if data["isin"] == isin), None)

        if not ticker:
            logger.error(f"ISIN {isin} is not configured for ISharesAdapter.")
            return pd.DataFrame()

        etf_info = ISHARES_ETF_DATA[ticker]

        # Construct the URL based on the discovered pattern from the spike
        url = (
            f"https://www.ishares.com/{etf_info['region']}/{etf_info['user_type']}/{etf_info['region']}/produkte/"
            f"{etf_info['product_id']}/fund/1478358465952.ajax?fileType=csv&fileName={ticker}_holdings&dataType=fund"
        )
        logger.info(f"1. Constructed URL: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            logger.info("2. Making direct request to download CSV...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            logger.info("3. Download successful. Parsing raw CSV content...")
            
            # Use StringIO to treat the string response as a file
            csv_data = StringIO(response.text)
            
            # Skip initial rows and parse the main data
            holdings_df = pd.read_csv(csv_data, skiprows=2)
            logger.info(f"   - Successfully parsed CSV. Found {len(holdings_df)} rows.")

            # We only need Ticker, Name, and Weight.
            holdings_df = holdings_df[['Emittententicker', 'Name', 'Gewichtung (%)']].copy()
            holdings_df.rename(columns={
                'Emittententicker': 'ticker',
                'Name': 'name',
                'Gewichtung (%)': 'weight_percentage'
            }, inplace=True)
            
            logger.info("4. Standardized column names.")

            # Drop rows with missing Name (often footer rows)
            holdings_df.dropna(subset=['name'], inplace=True)

            # --- Data Cleaning ---
            # Convert weight percentage to float
            holdings_df['weight_percentage'] = holdings_df['weight_percentage'].str.replace(',', '.').astype(float)
            
            # Clip negative weights to 0.0
            holdings_df['weight_percentage'] = holdings_df['weight_percentage'].clip(lower=0.0)
            
            logger.info("5. Cleaned and converted weight percentage.")
            
            return holdings_df

        except requests.exceptions.RequestException as e:
            logger.error(f"Network request failed for {ticker}. Details: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"An unexpected error occurred in ISharesAdapter for {ticker}: {e}")
            return pd.DataFrame()

# --- Example Usage (for standalone testing) ---
if __name__ == '__main__':
    adapter = ISharesAdapter()
    adapter.fetch_holdings("IWDA")
