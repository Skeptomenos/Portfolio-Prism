"""Tiered ISIN enrichment for ETF holdings."""

from typing import Tuple

import pandas as pd

from src.core.health import health
from src.data.enrichment import enrich_securities
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Default threshold: only enrich holdings with weight > 1%
ENRICHMENT_THRESHOLD = 1.0


def enrich_etf_holdings(
    holdings: pd.DataFrame,
    etf_market_value: float,
    threshold: float = ENRICHMENT_THRESHOLD,
) -> pd.DataFrame:
    """
    Enrich equity holdings with ISIN data using tiered strategy.

    Tier 1 (weight > threshold): Full ISIN resolution via API
    Tier 2 (weight <= threshold): Skip resolution, use fallback aggregation

    Args:
        holdings: Classified ETF holdings DataFrame (must have 'asset_class' column)
        etf_market_value: Total ETF value for coverage calculation
        threshold: Weight percentage threshold for Tier 1 (default 1.0)

    Returns:
        Holdings DataFrame with 'isin' column populated
    """
    # If ISIN column already exists, nothing to enrich
    if "isin" in holdings.columns:
        return holdings

    holdings = holdings.copy()

    logger.info("    - 'isin' column not found. Enriching Equity holdings data...")

    # Only enrich equities
    if "asset_class" not in holdings.columns:
        logger.warning("    - 'asset_class' column missing. Cannot filter equities.")
        holdings["isin"] = [f"UNKNOWN_{i}" for i in range(len(holdings))]
        return holdings

    equity_mask = holdings["asset_class"] == "Equity"
    equity_holdings = holdings[equity_mask].copy()

    # Filter out invalid tickers
    if "ticker" in equity_holdings.columns:
        equity_holdings = equity_holdings.dropna(subset=["ticker"])
        equity_holdings = equity_holdings[
            equity_holdings["ticker"].apply(
                lambda x: isinstance(x, str) and len(str(x)) > 0
            )
        ]

    if equity_holdings.empty:
        logger.info("    - No valid equity holdings to enrich.")
        holdings["isin"] = [f"NON_EQUITY_{i}" for i in range(len(holdings))]
        return holdings

    # Split into tiers based on weight
    tier1_holdings, tier2_holdings = _split_by_weight(
        equity_holdings, etf_market_value, threshold
    )

    # Enrich Tier 1 only
    enriched_df = _enrich_tier1(tier1_holdings)

    # Merge enrichment back into original holdings
    holdings = _merge_enrichment(holdings, enriched_df, tier2_holdings, threshold)

    return holdings


def _split_by_weight(
    equity_holdings: pd.DataFrame, etf_market_value: float, threshold: float
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split holdings into Tier 1 (>threshold) and Tier 2 (<=threshold).

    Args:
        equity_holdings: Equity-only holdings DataFrame
        etf_market_value: ETF total value for coverage calculation
        threshold: Weight percentage threshold

    Returns:
        Tuple of (tier1_holdings, tier2_holdings)
    """
    if "weight_percentage" not in equity_holdings.columns:
        logger.warning(
            "    ⚠️  'weight_percentage' column missing. Enriching all holdings."
        )
        return equity_holdings.copy(), pd.DataFrame()

    # Ensure numeric
    equity_holdings = equity_holdings.copy()
    equity_holdings["weight_percentage"] = pd.to_numeric(
        equity_holdings["weight_percentage"], errors="coerce"
    ).fillna(0.0)

    # Split by threshold
    tier1_mask = equity_holdings["weight_percentage"] > threshold
    tier1 = equity_holdings[tier1_mask].copy()
    tier2 = equity_holdings[~tier1_mask].copy()

    # Record health metrics
    health.record_metric("tier1_holdings", len(tier1))
    health.record_metric("tier2_holdings", len(tier2))

    # Calculate value coverage
    tier1_weight = tier1["weight_percentage"].sum()
    tier2_weight = tier2["weight_percentage"].sum()
    total_weight = tier1_weight + tier2_weight

    if total_weight > 0:
        tier1_val = (tier1_weight / total_weight) * etf_market_value
        tier2_val = (tier2_weight / total_weight) * etf_market_value
        health.record_value_coverage(tier1_val, tier2_val)

    logger.info(
        f"    - Tiered Enrichment: {len(tier1)} major (>{threshold}%), "
        f"{len(tier2)} minor (≤{threshold}%)"
    )
    logger.info(f"    - Skipping ISIN resolution for {len(tier2)} minor holdings")

    return tier1, tier2


def _enrich_tier1(tier1_holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich Tier 1 holdings via ISIN resolution API.

    Args:
        tier1_holdings: Holdings with weight > threshold

    Returns:
        DataFrame with [ticker, isin] columns from enrichment
    """
    if tier1_holdings.empty:
        return pd.DataFrame(columns=["ticker", "isin"])

    holdings_list = tier1_holdings.to_dict("records")
    enriched = enrich_securities(holdings_list)

    if enriched:
        enriched_df = pd.DataFrame(enriched)
        health.record_metric("tier1_resolved", len(enriched_df))
        return enriched_df

    return pd.DataFrame(columns=["ticker", "isin"])


def _merge_enrichment(
    holdings: pd.DataFrame,
    enriched_df: pd.DataFrame,
    tier2_holdings: pd.DataFrame,
    threshold: float,
) -> pd.DataFrame:
    """
    Merge enriched ISINs back into holdings DataFrame.

    Args:
        holdings: Original holdings DataFrame
        enriched_df: Enrichment results with [ticker, isin]
        tier2_holdings: Tier 2 holdings (to mark as N/A)
        threshold: Weight threshold for failure logging

    Returns:
        Holdings with 'isin' column populated
    """
    holdings = holdings.copy()

    # Check if we can merge
    if "ticker" not in holdings.columns:
        logger.error(
            "    - Cannot merge enriched data: 'ticker' column missing in holdings."
        )
        holdings["isin"] = [f"UNKNOWN_{i}" for i in range(len(holdings))]
        return holdings

    if enriched_df.empty or "ticker" not in enriched_df.columns:
        logger.warning("    - No enrichment data to merge.")
        holdings["isin"] = "N/A"
    else:
        # Merge on ticker
        holdings = pd.merge(
            holdings,
            enriched_df[["ticker", "isin"]],
            on="ticker",
            how="left",
        )
        logger.info("    - Enrichment complete. Merged ISINs into holdings.")

    # Mark Tier 2 holdings as N/A (they were intentionally skipped)
    if not tier2_holdings.empty and "ticker" in tier2_holdings.columns:
        tier2_tickers = set(tier2_holdings["ticker"].tolist())
        tier2_mask = holdings["ticker"].isin(tier2_tickers)
        holdings.loc[tier2_mask, "isin"] = "N/A"

    # Log Tier 1 failures
    _log_tier1_failures(holdings, threshold)

    # Fill remaining missing ISINs (non-equities, etc.)
    if "isin" in holdings.columns:
        missing_mask = holdings["isin"].isna()
        holdings.loc[missing_mask, "isin"] = [
            f"NON_EQUITY_{i}" for i in range(missing_mask.sum())
        ]
    else:
        holdings["isin"] = [f"UNKNOWN_{i}" for i in range(len(holdings))]

    return holdings


def _log_tier1_failures(holdings: pd.DataFrame, threshold: float) -> None:
    """
    Log and record health metrics for Tier 1 ISIN resolution failures.

    Args:
        holdings: Holdings after enrichment merge
        threshold: Weight threshold used for Tier 1
    """
    # Need both columns to identify failures
    required_cols = ["weight_percentage", "asset_class", "isin"]
    if not all(col in holdings.columns for col in required_cols):
        return

    # Find Tier 1 holdings that failed to resolve
    tier1_failed = holdings[
        (holdings["asset_class"] == "Equity")
        & (holdings["isin"].isin(["N/A", None, ""]) | holdings["isin"].isna())
        & (holdings["weight_percentage"] > threshold)
    ]

    if tier1_failed.empty:
        return

    health.record_metric("tier1_failed", len(tier1_failed))
    logger.warning(
        f"    ⚠️  {len(tier1_failed)} major holdings (>{threshold}%) "
        "FAILED ISIN resolution:"
    )

    for i, (_, row) in enumerate(tier1_failed.iterrows()):
        if i >= 10:
            logger.warning(f"        ... and {len(tier1_failed) - 10} more")
            break

        ticker = row.get("ticker", "unknown")
        logger.warning(f"        - {ticker}")
        health.record_failure(
            stage="ENRICHMENT",
            item=str(ticker),
            error="Tier 1 ISIN Resolution Failed",
            fix=f"Add {ticker} to config/asset_universe.csv",
            severity="MEDIUM",
        )
