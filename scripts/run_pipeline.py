# main.py
import pandas as pd
import sys
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.manager import load_positions_from_db
from src.core.aggregation import run_aggregation
from src.core.reporting import generate_report
from src.data.market import get_price_map
from src.core.validation import validate_final_report
from src.utils.logging_config import get_logger
from src.adapters.registry import AdapterRegistry, AdapterNotImplementedError
from src.utils.schemas import HoldingsSchema
import pandera as pa
from datetime import datetime
from scripts.update_registry import update_registry_interactive
from src.utils.metrics import tracker

logger = get_logger(__name__)

def generate_quality_report(failed_etfs: list, output_path: str):
    """Generates a report on data that could not be processed."""
    if not failed_etfs:
        logger.info("--- Data Quality Report: All ETFs processed successfully. ---")
        return

    with open(output_path, 'w') as f:
        f.write(f"--- Data Quality Report ---\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("The following ETFs could not be processed and were EXCLUDED from the calculation:\n")
        for isin, reason in failed_etfs:
            f.write(f"- {isin}: {reason}\n")
        f.write("\nWARNING: The 'true_exposure_report.csv' is based on incomplete data.\n")
    logger.warning(f"--- Data Quality Report generated at {output_path} detailing {len(failed_etfs)} failures. ---")


def run_pipeline():
    """
    Orchestrates the entire True Exposure pipeline from start to finish.
    """
    tracker.start_run()
    logger.info("--- Starting True Exposure Pipeline ---")

    # --- Phase 1 & 2 (Data Loading) ---
    direct_positions, etf_positions = load_positions_from_db()
    
    tracker.set_funnel_metric("total_positions_db", len(direct_positions) + len(etf_positions))
    tracker.set_funnel_metric("direct_holdings", len(direct_positions))
    tracker.set_funnel_metric("etf_positions", len(etf_positions))

    if direct_positions.empty and etf_positions.empty:
        logger.warning("--- Pipeline Halted: No positions found in the database. ---")
        tracker.save("outputs/pipeline_metrics.json")
        return

    # --- Phase 2.1: Registry Update (Human-in-the-Loop) ---
    # Combine positions to scan for new assets. We rename columns to match what update_registry expects (ISIN, NAME)
    # The DB load returns lowercase columns 'isin', 'name'
    all_positions_scan = pd.concat([direct_positions, etf_positions])
    all_positions_scan = all_positions_scan.rename(columns={'isin': 'ISIN', 'name': 'NAME'})
    
    # Only run interactive update if we are in a TTY (terminal)
    if sys.stdout.isatty():
        update_registry_interactive(all_positions_scan)
    else:
        logger.info("Non-interactive mode detected. Skipping registry update prompt.")

    # --- RE-SYNC DB with Registry ---
    # The positions table might still have 'Stock' as asset_type if they were loaded before mapping.
    # We must update the asset_type in the DB based on the new registry.
    import sqlite3
    import json
    
    registry_path = os.path.join(project_root, 'config', 'adapter_registry.json')
    db_path = os.path.join(project_root, 'data', 'working', 'database', 'portfolio.db')
    
    if os.path.exists(registry_path) and os.path.exists(db_path):
        try:
            with open(registry_path, 'r') as f:
                registry_data = json.load(f)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            for isin, provider in registry_data.items():
                if provider and provider != "ignore":
                    cursor.execute("UPDATE positions SET asset_type = 'ETF' WHERE ISIN = ?", (isin,))
                    updated_count += cursor.rowcount
            
            conn.commit()
            conn.close()
            logger.info(f"--- Synced DB with Registry: Updated {updated_count} positions to 'ETF' ---")
        except Exception as e:
            logger.error(f"Failed to sync DB with registry: {e}")

    # --- RE-LOAD Data (Critical) ---
    # We must reload positions because the classification (ETF vs Stock) depends on the
    # now-updated adapter_registry.json.
    logger.info("--- Reloading positions with updated registry... ---")
    direct_positions, etf_positions = load_positions_from_db()
    
    # Update funnel metrics again after reload/re-sync
    tracker.set_funnel_metric("total_positions_db", len(direct_positions) + len(etf_positions))
    tracker.set_funnel_metric("direct_holdings", len(direct_positions))
    tracker.set_funnel_metric("etf_positions", len(etf_positions))

    # --- Setup Adapter Registry (after potential updates) ---
    adapter_registry = AdapterRegistry()

    # --- Phase 2.5 (Market Data) ---
    # Combine to fetch prices for ALL assets (Stocks + ETFs)
    all_positions = pd.concat([direct_positions, etf_positions], ignore_index=True)

    if not all_positions.empty:
        logger.info("--- Updating All Positions with Live Prices (yfinance) ---")
        all_isins = all_positions['isin'].tolist()
        live_prices = get_price_map(all_isins)
        
        for index, row in all_positions.iterrows():
            isin = row['isin']
            if isin in live_prices:
                new_price = live_prices[isin]
                quantity = row['quantity']
                # Update price and market value
                all_positions.at[index, 'current_price'] = new_price
                all_positions.at[index, 'market_value'] = quantity * new_price
                logger.debug(f"  - Updated {isin}: €{new_price:.2f}")
            else:
                price_val = row['current_price']
                price_str = f"€{price_val:.2f}" if price_val is not None else "N/A"
                logger.warning(f"  - ⚠️ No live price for {isin}. Using database value: {price_str}")

    # Re-split for processing
    direct_positions = all_positions[all_positions['asset_type'] != 'ETF'].copy()
    etf_positions = all_positions[all_positions['asset_type'] == 'ETF'].copy()

    # --- Phase 3 (Aggregation) ---
    logger.info("--- Running Phase 3: Aggregation ---")
    etf_holdings_map = {}
    failed_etfs = [] # Now stores tuples of (isin, reason)
    
    # Load registry directly to check for 'ignore' status without instantiating adapter
    # (AdapterRegistry.get_adapter returns None for unknown/ignore, but we want to distinguish)
    # Actually, let's inspect the _isin_to_key map from the registry instance
    registry_map = adapter_registry._isin_to_key

    for _, etf in etf_positions.iterrows():
        isin = etf['isin']
        
        # Check if ignored
        if registry_map.get(isin) == "ignore":
            logger.info(f"--- Skipping Ignored ETF: {etf['name']} ({isin}) ---")
            continue

        holdings = pd.DataFrame()
        try:
            logger.info(f"--- Processing ETF: {etf['name']} ({isin}) ---")
            
            # 1. Get Adapter
            adapter = adapter_registry.get_adapter(isin)
            if not adapter:
                failed_etfs.append((isin, "No adapter registered for this ISIN."))
                tracker.increment_system_metric("etfs_failed")
                continue
            
            tracker.increment_system_metric("etfs_with_adapter")

            # 2. Fetch Data
            holdings = adapter.fetch_holdings(isin)
            if holdings.empty:
                failed_etfs.append((isin, "Adapter returned no data."))
                tracker.increment_system_metric("etfs_failed")
                continue

            # 3. Validate Data
            holdings = HoldingsSchema.validate(holdings)
            
            etf_holdings_map[isin] = holdings
            tracker.increment_system_metric("etfs_successfully_fetched")
            logger.info(f"--- Successfully fetched and validated {len(holdings)} holdings for {etf['name']}. ---")

        except AdapterNotImplementedError as e:
            logger.warning(f"Skipping {etf['name']}: {e}")
            failed_etfs.append((isin, f"Not Implemented: {e} (Added to Roadmap)"))
            tracker.increment_system_metric("etfs_failed")
        except pa.errors.SchemaError as e:
            logger.error(f"Data contract validation failed for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Validation Error: {e.args[0]}"))
            tracker.increment_system_metric("etfs_failed")
        except Exception as e:
            logger.error(f"An unexpected error occurred for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Unexpected Error: {e}"))
            tracker.increment_system_metric("etfs_failed")
    
    aggregated_df = run_aggregation(direct_positions, etf_positions, etf_holdings_map)
    if aggregated_df.empty and not failed_etfs:
        logger.warning("--- Pipeline Halted: Aggregation produced no results, and no ETF failures were recorded. ---")
        tracker.save("outputs/pipeline_metrics.json")
        return

    # --- Phase 4 (Reporting) ---
    logger.info("--- Running Phase 4: Reporting & Analysis ---")
    generate_report()

    # --- Phase 5 (Validation) ---
    logger.info("--- Running Phase 5: Final Validation ---")
    final_report_df = pd.read_csv("outputs/true_exposure_report.csv")
    validate_final_report(all_positions, final_report_df)

    # --- Final Step: Data Quality Report ---
    generate_quality_report(failed_etfs, "outputs/data_quality_report.txt")
    
    tracker.save("outputs/pipeline_metrics.json")

    logger.info("--- True Exposure Pipeline Finished ---")

if __name__ == '__main__':
    run_pipeline()
