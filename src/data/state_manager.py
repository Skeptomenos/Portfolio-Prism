import pandas as pd
import os
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths
UNIVERSE_PATH = "config/asset_universe.csv"
HOLDINGS_PATH = "data/true_data/portfolio_holdings.csv"
LEGACY_TRUTH_PATH = "data/true_data/portfolio_truth.csv"  # Fallback


def load_portfolio_state():
    """
    Loads the portfolio state from the Relational CSVs (Universe + Holdings).
    Prioritizes the new model, falls back to legacy if needed.

    Returns:
        (direct_positions, etf_positions) - Tuple of DataFrames
    """
    # 1. Strategy: Relational Model
    if os.path.exists(UNIVERSE_PATH) and os.path.exists(HOLDINGS_PATH):
        logger.info(
            "Loading portfolio from Relational Database (Universe + Holdings)..."
        )
        df_uni = pd.read_csv(UNIVERSE_PATH)
        df_hold = pd.read_csv(HOLDINGS_PATH)

        # Merge
        # We merge on ISIN.
        df = pd.merge(df_hold, df_uni, on="ISIN", how="left")

        # Check for unmapped assets
        unmapped = df[df["Name"].isna()]
        if not unmapped.empty:
            logger.warning(
                f"{len(unmapped)} assets in Holdings could not be mapped to Universe (Check ISINs)."
            )

    elif os.path.exists(LEGACY_TRUTH_PATH):
        logger.info(f"Loading portfolio from Legacy Truth: {LEGACY_TRUTH_PATH}")
        df = pd.read_csv(LEGACY_TRUTH_PATH)
        if "ISIN" not in df.columns:
            df["ISIN"] = df["Ticker"]
        if "Asset_Class" not in df.columns:
            df["Asset_Class"] = "Stock"
    else:
        logger.warning("No portfolio state found.")
        return pd.DataFrame(), pd.DataFrame()

    # 2. Standardize for Pipeline
    # Pipeline expects columns: isin, name, quantity, asset_type, ticker_src, provider

    # Rename columns to match pipeline standard (lowercase)
    # Universe has: ISIN, TR_Ticker, Yahoo_Ticker, Name, Provider, Asset_Class
    # Holdings has: ISIN, Quantity

    df_clean = df.rename(
        columns={
            "ISIN": "isin",
            "Name": "name",
            "Quantity": "quantity",
            "Asset_Class": "asset_type",
            "Yahoo_Ticker": "ticker_src",  # Important for market.py
            "Provider": "provider",
        }
    )

    # Fill NAs
    df_clean["name"] = df_clean["name"].fillna("Unknown Asset")
    df_clean["asset_type"] = df_clean["asset_type"].fillna("Stock")

    # Split
    direct_positions = df_clean[df_clean["asset_type"] == "Stock"].copy()
    etf_positions = df_clean[df_clean["asset_type"] == "ETF"].copy()

    logger.info(
        f"Loaded {len(direct_positions)} Stocks and {len(etf_positions)} ETFs from database."
    )

    return direct_positions, etf_positions
