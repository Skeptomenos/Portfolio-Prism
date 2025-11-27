import math
import os
from typing import Any, List, Optional, Tuple

import pandas as pd
from pydantic import ValidationError

from src.models import DirectPosition, ETFPosition
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _to_optional_str(value: Any) -> Optional[str]:
    """Convert pandas value to optional string, handling NaN."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return str(value) if value else None


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

    # Validate positions using Pydantic models
    direct_positions = _validate_positions(direct_positions, asset_type="Stock")
    etf_positions = _validate_positions(etf_positions, asset_type="ETF")

    return direct_positions, etf_positions


def _validate_positions(df: pd.DataFrame, asset_type: str) -> pd.DataFrame:
    """
    Validate DataFrame rows against Pydantic Position model.

    Logs validation errors but keeps valid rows to maintain pipeline continuity.
    Invalid rows are dropped with a warning.

    Args:
        df: DataFrame with position data
        asset_type: Expected asset type ("Stock" or "ETF")

    Returns:
        DataFrame with only valid positions
    """
    if df.empty:
        return df

    valid_indices = []
    validation_errors = []

    for idx, row in df.iterrows():
        try:
            # Build position dict from row, converting NaN to None for optional fields
            position_data = {
                "isin": row.get("isin", ""),
                "name": row.get("name", "Unknown"),
                "quantity": row.get("quantity", 0),
                "asset_type": asset_type,
                "ticker_src": _to_optional_str(row.get("ticker_src")),
                "provider": _to_optional_str(row.get("provider")),
            }

            # Validate using appropriate model
            if asset_type == "ETF":
                ETFPosition(**position_data)
            else:
                DirectPosition(**position_data)

            valid_indices.append(idx)

        except ValidationError as e:
            isin = row.get("isin", "unknown")
            validation_errors.append((isin, str(e)))

    # Log validation summary
    if validation_errors:
        logger.warning(
            f"Validation errors in {len(validation_errors)} {asset_type} positions:"
        )
        for isin, error in validation_errors[:5]:  # Show first 5
            logger.warning(f"  - {isin}: {error}")
        if len(validation_errors) > 5:
            logger.warning(f"  ... and {len(validation_errors) - 5} more")

    # Return only valid rows
    validated_df = df.loc[valid_indices].copy()
    logger.debug(
        f"Validated {len(validated_df)}/{len(df)} {asset_type} positions successfully."
    )

    return validated_df


def load_positions_as_models() -> Tuple[List[DirectPosition], List[ETFPosition]]:
    """
    Load portfolio positions as typed Pydantic model instances.

    Alternative to load_portfolio_state() for when you need strongly-typed
    Position objects instead of DataFrames.

    Returns:
        Tuple of (direct_positions, etf_positions) as lists of Position models
    """
    direct_df, etf_df = load_portfolio_state()

    direct_positions: List[DirectPosition] = []
    etf_positions: List[ETFPosition] = []

    for _, row in direct_df.iterrows():
        try:
            direct_positions.append(
                DirectPosition(
                    isin=row["isin"],
                    name=row["name"],
                    quantity=row["quantity"],
                    asset_type="Stock",
                    ticker_src=_to_optional_str(row.get("ticker_src")),
                    provider=_to_optional_str(row.get("provider")),
                )
            )
        except ValidationError:
            pass  # Already logged in load_portfolio_state

    for _, row in etf_df.iterrows():
        try:
            etf_positions.append(
                ETFPosition(
                    isin=row["isin"],
                    name=row["name"],
                    quantity=row["quantity"],
                    asset_type="ETF",
                    ticker_src=_to_optional_str(row.get("ticker_src")),
                    provider=_to_optional_str(row.get("provider")),
                )
            )
        except ValidationError:
            pass  # Already logged in load_portfolio_state

    logger.info(
        f"Created {len(direct_positions)} DirectPosition and {len(etf_positions)} ETFPosition models."
    )

    return direct_positions, etf_positions
