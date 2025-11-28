"""
Aggregation module for portfolio exposure calculation (v2).

This module decomposes ETF holdings and aggregates all exposures
(direct + indirect) into a single report.

Public API:
    run_aggregation(direct_positions, etf_positions, etf_holdings_map) -> DataFrame
"""

from typing import Dict

import pandas as pd

from src.config import TRUE_EXPOSURE_REPORT
from src.models import AggregatedExposure
from src.utils.logging_config import get_logger

from .classification import classify_etf_holdings
from .direct import process_direct_holdings
from .enrichment import enrich_etf_holdings
from .grouping import aggregate_indirect_holdings, calculate_indirect_values
from .output import finalize_and_save

logger = get_logger(__name__)

__all__ = ["run_aggregation"]


def run_aggregation(
    direct_positions: pd.DataFrame,
    etf_positions: pd.DataFrame,
    etf_holdings_map: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Run the entire exposure aggregation process.

    This function:
    1. Processes direct stock holdings
    2. Decomposes ETF holdings via classification, enrichment, and value calculation
    3. Aggregates all exposures by security
    4. Saves results to CSV

    Args:
        direct_positions: DataFrame with columns [isin, name, market_value]
        etf_positions: DataFrame with columns [isin, name, market_value]
        etf_holdings_map: Dict mapping ETF ISIN to holdings DataFrame

    Returns:
        DataFrame with aggregated true exposure per security
    """
    output_filepath = TRUE_EXPOSURE_REPORT

    if direct_positions.empty and etf_positions.empty:
        logger.warning("No positions found. Exiting aggregation.")
        return pd.DataFrame()

    # Initialize aggregator
    exposures = AggregatedExposure()

    # Step 1: Process direct holdings
    process_direct_holdings(direct_positions, exposures)

    # Step 2: Process ETF holdings
    logger.info("Processing indirect holdings (via ETFs)...")
    logger.info(f"Total ETFs to process: {len(etf_positions)}")

    all_holdings = pd.DataFrame()

    if not etf_positions.empty:
        for etf in etf_positions.to_dict("records"):
            etf_isin = etf["isin"]
            etf_market_value = etf["market_value"]

            logger.info(
                f"  - Processing ETF: {etf['name']} "
                f"(ISIN: {etf_isin}, Value: €{etf_market_value:,.2f})"
            )

            # Get holdings for this ETF
            holdings = etf_holdings_map.get(etf_isin)
            if holdings is None or holdings.empty:
                logger.warning(f"    - No holdings found for {etf_isin}. Skipping.")
                continue

            # Process: Classify -> Enrich -> Calculate values
            holdings = holdings.copy()
            holdings = classify_etf_holdings(holdings)
            holdings = enrich_etf_holdings(holdings, etf_market_value)
            holdings = calculate_indirect_values(holdings, etf_market_value)

            # Debug: log large holdings
            _log_large_holdings(holdings, etf_isin, etf["name"])

            # Accumulate
            all_holdings = pd.concat([all_holdings, holdings], ignore_index=True)

    # Debug: save intermediate results
    if not all_holdings.empty:
        try:
            all_holdings.to_csv("outputs/debug_all_holdings.csv", index=False)
        except Exception as e:
            logger.debug(f"Could not save debug file: {e}")

    # Step 3: Aggregate all indirect holdings
    aggregate_indirect_holdings(all_holdings, exposures)

    # Step 4: Finalize and save
    return finalize_and_save(exposures, output_filepath)


def _log_large_holdings(holdings: pd.DataFrame, etf_isin: str, etf_name: str) -> None:
    """Log holdings with indirect value > €1000 for debugging."""
    if "indirect" not in holdings.columns:
        return

    large = holdings[holdings["indirect"] > 1000]
    if large.empty:
        return

    logger.info(f"🔎 FOUND LARGE HOLDING in ETF {etf_isin} ({etf_name}):")
    for _, row in large.iterrows():
        weight = row.get("weight_percentage", 0)
        indirect = row.get("indirect", 0)
        name = row.get("name", "Unknown")
        isin = row.get("isin", "No ISIN")
        logger.info(f"    -> {name} ({isin}): {weight:.2f}% = €{indirect:,.2f}")
