"""
Tiered ISIN enrichment for ETF holdings.

This module integrates with the unified resolution system to:
1. Resolve ISINs for Tier 1 holdings (weight > threshold)
2. Mark Tier 2 holdings as skipped
3. Track resolution status for each holding
"""

from typing import Optional

import pandas as pd

from src.core.health import health
from src.data.resolution import ISINResolver
from src.utils.isin_validator import is_valid_isin
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Default threshold: only enrich holdings with weight > 1%
ENRICHMENT_THRESHOLD = 1.0

# Module-level resolver instance (reused across ETFs in a single pipeline run)
_resolver: Optional[ISINResolver] = None


def get_resolver() -> ISINResolver:
    """Get or create the resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = ISINResolver(tier1_threshold=ENRICHMENT_THRESHOLD)
    return _resolver


def reset_resolver() -> None:
    """Reset the resolver (call at end of pipeline to flush to universe)."""
    global _resolver
    if _resolver is not None:
        _resolver.flush_to_universe()
        logger.info(_resolver.get_stats_summary())
        _resolver = None


def enrich_etf_holdings(
    holdings: pd.DataFrame,
    etf_market_value: float,
    threshold: float = ENRICHMENT_THRESHOLD,
) -> pd.DataFrame:
    """
    Enrich equity holdings with ISIN data using tiered resolution.

    Tier 1 (weight > threshold): Full resolution attempt (local + API)
    Tier 2 (weight <= threshold): Local-only resolution, else skip

    Args:
        holdings: Classified ETF holdings DataFrame (must have 'asset_class' column)
        etf_market_value: Total ETF value for coverage calculation
        threshold: Weight percentage threshold for Tier 1 (default 1.0)

    Returns:
        Holdings DataFrame with 'isin', 'resolution_status', 'resolution_detail' columns
    """
    holdings = holdings.copy()
    resolver = get_resolver()

    # Check if already has valid ISIN column
    if "isin" in holdings.columns:
        # Validate existing ISINs
        has_valid = holdings["isin"].apply(
            lambda x: is_valid_isin(str(x)) if pd.notna(x) else False
        )
        if has_valid.all():
            # All ISINs are valid, just add status columns
            holdings["resolution_status"] = "resolved"
            holdings["resolution_detail"] = "provider"
            return holdings

    logger.info("    - 'isin' column not found or incomplete. Running resolution...")

    # Initialize new columns
    if "isin" not in holdings.columns:
        holdings["isin"] = None
    holdings["resolution_status"] = "unresolved"
    holdings["resolution_detail"] = ""

    # Only process equities
    if "asset_class" not in holdings.columns:
        logger.warning("    - 'asset_class' column missing. Skipping resolution.")
        return holdings

    # Process each holding
    equity_mask = holdings["asset_class"] == "Equity"

    tier1_count = 0
    tier2_count = 0
    resolved_count = 0

    for idx in holdings.index:
        row = holdings.loc[idx]

        # Skip non-equities
        if row.get("asset_class") != "Equity":
            holdings.at[idx, "resolution_status"] = "skipped"
            holdings.at[idx, "resolution_detail"] = "non_equity"
            continue

        ticker = row.get("ticker", "")
        name = row.get("name", "")
        provider_isin = row.get("isin") if pd.notna(row.get("isin")) else None
        weight = float(row.get("weight_percentage", 0) or 0)

        # Skip invalid tickers
        if not ticker or not isinstance(ticker, str) or len(ticker.strip()) == 0:
            holdings.at[idx, "resolution_status"] = "skipped"
            holdings.at[idx, "resolution_detail"] = "invalid_ticker"
            continue

        # Track tier stats
        if weight > threshold:
            tier1_count += 1
        else:
            tier2_count += 1

        # Resolve
        result = resolver.resolve(
            ticker=str(ticker).strip(),
            name=str(name).strip() if name else "",
            provider_isin=str(provider_isin) if provider_isin else None,
            weight=weight,
        )

        # Update holdings
        holdings.at[idx, "isin"] = result.isin
        holdings.at[idx, "resolution_status"] = result.status
        holdings.at[idx, "resolution_detail"] = result.detail

        if result.status == "resolved":
            resolved_count += 1

    # Log summary
    logger.info(
        f"    - Resolution: {tier1_count} Tier1 (>{threshold}%), "
        f"{tier2_count} Tier2 (≤{threshold}%)"
    )
    logger.info(f"    - Resolved: {resolved_count} holdings with valid ISIN")

    # Record health metrics
    health.record_metric("tier1_holdings", tier1_count)
    health.record_metric("tier2_holdings", tier2_count)
    health.record_metric("resolved_holdings", resolved_count)

    # Log failures for Tier 1
    _log_tier1_failures(holdings, threshold)

    return holdings


def _log_tier1_failures(holdings: pd.DataFrame, threshold: float) -> None:
    """
    Log and record health metrics for Tier 1 ISIN resolution failures.

    Args:
        holdings: Holdings after resolution
        threshold: Weight threshold used for Tier 1
    """
    required_cols = ["weight_percentage", "asset_class", "resolution_status"]
    if not all(col in holdings.columns for col in required_cols):
        return

    # Find Tier 1 holdings that failed to resolve
    tier1_failed = holdings[
        (holdings["asset_class"] == "Equity")
        & (holdings["resolution_status"] == "unresolved")
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
        detail = row.get("resolution_detail", "unknown")
        logger.warning(f"        - {ticker} ({detail})")
        health.record_failure(
            stage="ENRICHMENT",
            item=str(ticker),
            error=f"Tier 1 ISIN Resolution Failed: {detail}",
            fix=f"Add {ticker} to config/asset_universe.csv",
            severity="MEDIUM",
        )
