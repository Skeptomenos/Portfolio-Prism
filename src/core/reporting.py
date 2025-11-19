# phases/active/reporting.py
import pandas as pd
import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.manager import load_positions_from_db
from src.data.enrichment import enrich_securities

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_report(input_filepath: str = "outputs/true_exposure_report.csv"):
    """
    Loads the aggregated exposure report, enriches it, and generates
    summary analysis files.
    """
    logger.info(f"--- Generating analysis from {input_filepath} ---")
    
    try:
        # Load the main report
        exposure_df = pd.read_csv(input_filepath)
        logger.info(f"  - Successfully loaded exposure report with {len(exposure_df)} entries.")

        # --- FIX: Filter out rows with invalid ISINs before enrichment ---
        exposure_df.dropna(subset=['isin'], inplace=True)
        exposure_df = exposure_df[exposure_df['isin'].apply(lambda x: isinstance(x, str))]

        # Get a unique list of securities (ISINs) for enrichment
        securities_to_enrich = exposure_df[['isin']].drop_duplicates().to_dict('records')
        
        # Enrich the securities with metadata (now including sector and geography)
        enriched_data = enrich_securities(securities_to_enrich)
        if not enriched_data:
            logger.warning("  - Enrichment returned no data. Skipping sector/geography analysis.")
            return

        enriched_df = pd.DataFrame(enriched_data)

        # Merge the enriched data back into the main exposure dataframe
        # Use a left merge to keep all original exposure data
        final_df = pd.merge(exposure_df, enriched_df, on='isin', how='left')

        # Reorder columns for better readability
        cols = ['isin', 'name_y', 'sector', 'geography', 'direct', 'indirect', 'total_exposure', 'portfolio_percentage']
        final_df = final_df[cols]
        final_df.rename(columns={'name_y': 'name'}, inplace=True)
        
        # --- Generate Analysis Reports ---
        
        # 1. Top 10 Holdings Report
        top_10_df = final_df.nlargest(10, 'total_exposure')
        top_10_df.to_csv('outputs/top_10_holdings.csv', index=False)
        logger.info("  - Top 10 holdings report generated.")

        # 2. Sector Exposure Report
        sector_exposure = final_df.groupby('sector')['total_exposure'].sum().reset_index()
        total_portfolio_value = final_df['total_exposure'].sum()
        if total_portfolio_value > 0:
            sector_exposure['portfolio_percentage'] = (sector_exposure['total_exposure'] / total_portfolio_value) * 100
        else:
            sector_exposure['portfolio_percentage'] = 0.0
        sector_exposure.to_csv('outputs/sector_exposure.csv', index=False)
        logger.info("  - Sector exposure report generated.")

        # 3. Geography Exposure Report
        geography_exposure = final_df.groupby('geography')['total_exposure'].sum().reset_index()
        if total_portfolio_value > 0:
            geography_exposure['portfolio_percentage'] = (geography_exposure['total_exposure'] / total_portfolio_value) * 100
        else:
            geography_exposure['portfolio_percentage'] = 0.0
        geography_exposure.to_csv('outputs/geography_exposure.csv', index=False)
        logger.info("  - Geography exposure report generated.")
        
    except FileNotFoundError:
        logger.error(f"Input file not found at {input_filepath}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during reporting: \"{e}\"")

if __name__ == '__main__':
    generate_report()
