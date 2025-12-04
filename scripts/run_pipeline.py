# main.py
import pandas as pd
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

import sys
import os

# Add project root to sys.path to ensure scripts package is resolvable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from src.data.state_manager import load_portfolio_state
from src.core.aggregation import run_aggregation
from src.core.reporting import generate_report

# Note: We use TR prices from pytr instead of yfinance for portfolio valuation.
# get_price_map from market.py is only used for historical charts, not main pipeline.
from src.core.validation import validate_final_report
from src.utils.logging_config import get_logger
from src.adapters.registry import AdapterRegistry, AdapterNotImplementedError
from src.utils.schemas import HoldingsSchema
from src.core.direct_reporting import generate_direct_holdings_report
from pandera import errors as pa_errors
from datetime import datetime
from src.utils.metrics import tracker
from src.core.health import health

# Note: load_asset_universe from enrichment returns {ticker: isin} which excludes
# ISINs without Yahoo_Ticker. For health checks, we load the CSV directly.
from src.data.holdings_cache import HoldingsCache, ManualUploadRequired
from src.core.enrichment_gaps import EnrichmentGapCollector

logger = get_logger(__name__)

# Global gap collector instance - will be set in run_pipeline()
_gap_collector: EnrichmentGapCollector = None


def get_gap_collector() -> EnrichmentGapCollector:
    """Get the current gap collector instance."""
    global _gap_collector
    if _gap_collector is None:
        _gap_collector = EnrichmentGapCollector()
    return _gap_collector


def generate_quality_report(failed_etfs: list, output_path: str):
    """Generates a report on data that could not be processed."""
    if not failed_etfs:
        logger.info("--- Data Quality Report: All ETFs processed successfully. ---")
        return

    with open(output_path, "w") as f:
        f.write("--- Data Quality Report ---\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(
            "The following ETFs could not be processed and were EXCLUDED from the calculation:\n"
        )
        for isin, reason in failed_etfs:
            f.write(f"- {isin}: {reason}\n")
        f.write(
            "\nWARNING: The 'true_exposure_report.csv' is based on incomplete data.\n"
        )
    logger.warning(
        f"--- Data Quality Report generated at {output_path} detailing {len(failed_etfs)} failures. ---"
    )


def run_pipeline():
    """
    Orchestrates the entire True Exposure pipeline from start to finish.
    """
    tracker.start_run()
    logger.info("--- Starting True Exposure Pipeline ---")

    # --- Phase 1 & 2 (Data Loading) ---
    # Use State Manager (Prioritizes Truth CSV)
    direct_positions, etf_positions = load_portfolio_state()

    # Ensure columns exist for market data updates
    if "current_price" not in direct_positions.columns:
        direct_positions["current_price"] = None
    if "market_value" not in direct_positions.columns:
        direct_positions["market_value"] = 0.0

    if "current_price" not in etf_positions.columns:
        etf_positions["current_price"] = None
    if "market_value" not in etf_positions.columns:
        etf_positions["market_value"] = 0.0

    tracker.set_funnel_metric(
        "total_positions_db", len(direct_positions) + len(etf_positions)
    )
    tracker.set_funnel_metric("direct_holdings", len(direct_positions))
    tracker.set_funnel_metric("etf_positions", len(etf_positions))

    if direct_positions.empty and etf_positions.empty:
        logger.warning(
            "--- Pipeline Halted: No positions found in the portfolio state. ---"
        )
        tracker.save("outputs/pipeline_metrics.json")
        return

    # --- HEALTH CHECK: Inputs ---
    health.reset()
    health.record_metric("direct_holdings", len(direct_positions), "set")
    health.record_metric("etf_positions", len(etf_positions), "set")

    # Check Unmapped Direct Holdings
    # Note: We load the CSV directly instead of using load_asset_universe() from enrichment,
    # because that function returns {ticker: isin} and excludes ISINs without Yahoo_Ticker.
    # Auto-added ISINs from Trade Republic often don't have Yahoo_Ticker yet.
    try:
        universe_path = "config/asset_universe.csv"
        if os.path.exists(universe_path):
            universe_df = pd.read_csv(universe_path)
            known_isins = set(universe_df["ISIN"].dropna())
        else:
            known_isins = set()

        for _, row in direct_positions.iterrows():
            isin = row.get("isin")
            if isin and isin not in known_isins:
                health.record_failure(
                    stage="DIRECT_HOLDINGS",
                    item=isin,
                    error="Direct holding ISIN not found in asset_universe",
                    fix=f"Add {isin} to config/asset_universe.csv",
                    severity="MEDIUM",
                )
    except Exception as e:
        logger.warning(f"Health check failed: {e}")

    # --- Setup Adapter Registry and Holdings Cache ---
    adapter_registry = AdapterRegistry()
    holdings_cache = HoldingsCache()

    # --- Phase 2.5 (Market Data) ---
    # Use Trade Republic prices from pytr (already loaded via state_manager)
    # No need to fetch from yfinance - TR provides real-time prices
    all_positions = pd.concat([direct_positions, etf_positions], ignore_index=True)

    if not all_positions.empty:
        logger.info("--- Using Trade Republic Prices for Portfolio Valuation ---")

        for index, row in all_positions.iterrows():
            isin = row["isin"]
            tr_price = row.get("tr_price")

            # Use TR price if available (from pytr's NetValue/Quantity)
            if tr_price is not None and pd.notna(tr_price) and float(tr_price) > 0:
                quantity = row["quantity"]
                all_positions.at[index, "current_price"] = float(tr_price)
                all_positions.at[index, "market_value"] = quantity * float(tr_price)
                logger.debug(f"  - {isin}: €{float(tr_price):.2f} (from TR)")
            else:
                # Fallback: check if current_price already set
                current = row.get("current_price")
                if current is not None and pd.notna(current) and float(current) > 0:
                    quantity = row["quantity"]
                    all_positions.at[index, "market_value"] = quantity * float(current)
                    logger.debug(f"  - {isin}: €{float(current):.2f} (existing)")
                else:
                    logger.warning(
                        f"  - ⚠️ No price for {isin}. Market value may be inaccurate."
                    )

    # --- Phase 2.6 (Direct Reporting) ---
    generate_direct_holdings_report(all_positions)

    # Re-split for processing
    direct_positions = all_positions[all_positions["asset_type"] != "ETF"].copy()
    etf_positions = all_positions[all_positions["asset_type"] == "ETF"].copy()

    # --- Phase 3 (Aggregation) ---
    logger.info("--- Running Phase 3: Aggregation ---")

    # Initialize and set gap collector for enrichment
    from src.core.aggregation.enrichment import set_gap_collector

    gap_collector = get_gap_collector()
    set_gap_collector(gap_collector)

    etf_holdings_map = {}
    failed_etfs = []  # Now stores tuples of (isin, reason)

    # Load registry directly to check for 'ignore' status without instantiating adapter
    # (AdapterRegistry.get_adapter returns None for unknown/ignore, but we want to distinguish)
    # Actually, let's inspect the _isin_to_key map from the registry instance
    registry_map = adapter_registry._isin_to_key

    for _, etf in etf_positions.iterrows():
        isin = etf["isin"]

        # Check if ignored
        if registry_map.get(isin) == "ignore":
            logger.info(f"--- Skipping Ignored ETF: {etf['name']} ({isin}) ---")
            continue

        holdings = pd.DataFrame()
        try:
            logger.info(f"--- Processing ETF: {etf['name']} ({isin}) ---")

            # Option B: Direct cache check in pipeline
            # TIER 1 & 2: Try holdings cache first (local cache + community data)
            try:
                holdings = holdings_cache.get_holdings(isin)
                logger.info(f"  -> Found in holdings cache ({len(holdings)} holdings)")
                tracker.increment_system_metric("cache_hits")
            except ManualUploadRequired:
                # Cache miss - fall through to adapter
                holdings = None

            # TIER 3: Fall back to adapter/scraper if cache missed
            if holdings is None or (
                isinstance(holdings, pd.DataFrame) and holdings.empty
            ):
                adapter = adapter_registry.get_adapter(isin)
                if not adapter:
                    failed_etfs.append((isin, "No adapter registered for this ISIN."))
                    tracker.increment_system_metric("etfs_failed")
                    health.record_etf_stat(isin, 0, 0.0, "NO_ADAPTER")
                    health.record_failure(
                        "ETF_DECOMPOSITION",
                        isin,
                        "No adapter found",
                        "Update src/adapters/registry.py or upload to data/inputs/manual_holdings/",
                        "HIGH",
                    )
                    continue

                tracker.increment_system_metric("etfs_with_adapter")
                holdings = adapter.fetch_holdings(isin)

                # Save successful fetch to local cache for next time
                if holdings is not None and not holdings.empty:
                    holdings_cache._save_to_local_cache(
                        isin, holdings, source="adapter_fetch", name=etf["name"]
                    )

            # HEALTH CHECK: ETF Stats
            if holdings is not None and not holdings.empty:
                count = len(holdings)
                weight_sum = (
                    holdings["weight_percentage"].sum()
                    if "weight_percentage" in holdings.columns
                    else 0.0
                )
                health.record_etf_stat(isin, count, weight_sum, "OK")
                health.record_metric("etfs_processed", 1)
            else:
                health.record_etf_stat(isin, 0, 0.0, "EMPTY")
                health.record_failure(
                    "ETF_DECOMPOSITION",
                    isin,
                    "Returned empty holdings",
                    "Check provider website or upload to data/inputs/manual_holdings/",
                    "HIGH",
                )
                failed_etfs.append((isin, "No holdings data available."))
                tracker.increment_system_metric("etfs_failed")
                continue

            # 3. Validate Data
            holdings = HoldingsSchema.validate(holdings)

            etf_holdings_map[isin] = holdings
            tracker.increment_system_metric("etfs_successfully_fetched")
            logger.info(
                f"--- Successfully fetched and validated {len(holdings)} holdings for {etf['name']}. ---"
            )

        except ManualUploadRequired as e:
            logger.warning(f"Manual upload required for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Manual upload required: {e}"))
            health.record_failure(
                "ETF_DECOMPOSITION",
                isin,
                str(e),
                f"Upload holdings to data/inputs/manual_holdings/{isin}.csv",
                "HIGH",
            )
            tracker.increment_system_metric("etfs_failed")
        except AdapterNotImplementedError as e:
            logger.warning(f"Skipping {etf['name']}: {e}")
            failed_etfs.append((isin, f"Not Implemented: {e} (Added to Roadmap)"))
            tracker.increment_system_metric("etfs_failed")
        except pa_errors.SchemaError as e:
            logger.error(f"Data contract validation failed for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Validation Error: {e.args[0]}"))
            tracker.increment_system_metric("etfs_failed")
        except Exception as e:
            logger.error(f"An unexpected error occurred for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Unexpected Error: {e}"))
            tracker.increment_system_metric("etfs_failed")

    aggregated_df = run_aggregation(direct_positions, etf_positions, etf_holdings_map)
    if aggregated_df.empty and not failed_etfs:
        logger.warning(
            "--- Pipeline Halted: Aggregation produced no results, and no ETF failures were recorded. ---"
        )
        tracker.save("outputs/pipeline_metrics.json")
        return

    # --- Finalize and Formatting Output ---
    logger.info("--- Finalizing and Formatting Output ---")

    # Save Health Report
    health.save_artifacts()
    print("\n" + health.generate_report())

    # Calculate True Portfolio Value for Reporting
    portfolio_total_value = (
        all_positions["market_value"].sum() if not all_positions.empty else 0.0
    )
    logger.info(
        f"--- Calculated True Portfolio Value: €{portfolio_total_value:,.2f} ---"
    )

    # Generate Reports with Correct Percentage Base
    generate_report(total_portfolio_value=portfolio_total_value)

    # --- Phase 6: Visualization ---
    from scripts.visualize_portfolio import run_visualization

    run_visualization()

    # 7. Harvest New Securities (Auto-Learning)
    logger.info("--- Step 7: Harvesting New Securities to Asset Universe ---")
    try:
        from scripts.harvest_enrichment import harvest_cache

        harvest_cache()
    except Exception as e:
        logger.error(f"Failed to harvest new securities: {e}")

    # --- Phase 5 (Validation) ---
    logger.info("--- Running Phase 5: Final Validation ---")
    final_report_df = pd.read_csv("outputs/true_exposure_report.csv")
    validate_final_report(all_positions, final_report_df)

    # --- Optional: Ground Truth Validation (Development Mode) ---
    if os.environ.get("VALIDATE_PORTFOLIO", "false").lower() == "true":
        logger.info("--- Running Ground Truth Validation ---")
        try:
            from scripts.validate_portfolio import validate_portfolio

            validation_result = validate_portfolio(
                reference_date="2025-11-24",
                tolerance=0.02,
            )
            if validation_result.discrepancy_pct > 0.10:
                logger.warning(
                    f"Portfolio validation: High discrepancy detected "
                    f"({validation_result.discrepancy_pct:.1%})"
                )
        except Exception as e:
            logger.warning(f"Ground truth validation skipped: {e}")

    # --- Final Step: Data Quality Report ---
    generate_quality_report(failed_etfs, "outputs/data_quality_report.txt")

    # Save enrichment gaps for dashboard
    gap_collector = get_gap_collector()
    gap_collector.save()
    summary = gap_collector.get_summary()
    if summary.total_gaps > 0:
        logger.info(
            f"--- Enrichment Gaps: {summary.total_gaps} items "
            f"({summary.total_weight_affected:.2f}% of portfolio) ---"
        )

    tracker.save("outputs/pipeline_metrics.json")

    logger.info("--- True Exposure Pipeline Finished ---")


if __name__ == "__main__":
    run_pipeline()
