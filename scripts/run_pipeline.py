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
from src.adapters.registry import AdapterRegistry
from src.utils.schemas import HoldingsSchema
import pandera as pa
from datetime import datetime

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
    logger.info("--- Starting True Exposure Pipeline ---")

    # --- Setup ---
    adapter_registry = AdapterRegistry()

    # --- Phase 1 & 2 (Data Loading) ---
    direct_positions, etf_positions = load_positions_from_db()
    if direct_positions.empty and etf_positions.empty:
        logger.warning("--- Pipeline Halted: No positions found in the database. ---")
        return
    
    # --- Phase 2.5 (Market Data) ---
    if not direct_positions.empty:
        logger.info("--- Updating Direct Positions with Live Prices (yfinance) ---")
        direct_isins = direct_positions['isin'].tolist()
        live_prices = get_price_map(direct_isins)
        
        for index, row in direct_positions.iterrows():
            isin = row['isin']
            if isin in live_prices:
                new_price = live_prices[isin]
                quantity = row['quantity']
                # Update price and market value
                direct_positions.at[index, 'current_price'] = new_price
                direct_positions.at[index, 'market_value'] = quantity * new_price
                logger.debug(f"  - Updated {isin}: €{new_price:.2f}")
            else:
                logger.warning(f"  - ⚠️ No live price for {isin}. Using database value: €{row['current_price']:.2f}")

    all_positions = pd.concat([direct_positions, etf_positions])

    # --- Phase 3 (Aggregation) ---
    logger.info("--- Running Phase 3: Aggregation ---")
    etf_holdings_map = {}
    failed_etfs = [] # Now stores tuples of (isin, reason)
    for _, etf in etf_positions.iterrows():
        isin = etf['isin']
        holdings = pd.DataFrame()
        try:
            logger.info(f"--- Processing ETF: {etf['name']} ({isin}) ---")
            
            # 1. Get Adapter
            adapter = adapter_registry.get_adapter(isin)
            if not adapter:
                failed_etfs.append((isin, "No adapter registered for this ISIN."))
                continue

            # 2. Fetch Data
            holdings = adapter.fetch_holdings(isin)
            if holdings.empty:
                failed_etfs.append((isin, "Adapter returned no data."))
                continue

            # 3. Validate Data
            holdings = HoldingsSchema.validate(holdings)
            
            etf_holdings_map[isin] = holdings
            logger.info(f"--- Successfully fetched and validated {len(holdings)} holdings for {etf['name']}. ---")

        except pa.errors.SchemaError as e:
            logger.error(f"Data contract validation failed for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Validation Error: {e.args[0]}"))
        except Exception as e:
            logger.error(f"An unexpected error occurred for {etf['name']}: {e}")
            failed_etfs.append((isin, f"Unexpected Error: {e}"))
    
    aggregated_df = run_aggregation(direct_positions, etf_positions, etf_holdings_map)
    if aggregated_df.empty and not failed_etfs:
        logger.warning("--- Pipeline Halted: Aggregation produced no results, and no ETF failures were recorded. ---")
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

    logger.info("--- True Exposure Pipeline Finished ---")

if __name__ == '__main__':
    run_pipeline()
