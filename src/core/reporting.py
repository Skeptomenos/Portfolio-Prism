# phases/active/reporting.py
import pandas as pd
import sys
import os



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

        # Check for missing values in exposure data (due to missing prices)
        missing_value_mask = final_df['total_exposure'].isna()
        missing_value_count = missing_value_mask.sum()
        
        if missing_value_count > 0:
            logger.warning(f"  - ⚠️  {missing_value_count} assets have missing value data (Price not found). They are excluded from total portfolio value.")
            # Fill NaNs with 0.0 for calculation purposes so they don't break sums
            final_df['total_exposure'] = final_df['total_exposure'].fillna(0.0)
            final_df['direct'] = final_df['direct'].fillna(0.0)
            final_df['indirect'] = final_df['indirect'].fillna(0.0)

        # --- Fill Missing Metadata based on Asset Class ---
        if 'asset_class' in final_df.columns:
            # Cash
            cash_mask = final_df['asset_class'] == 'Cash'
            final_df.loc[cash_mask, 'sector'] = final_df.loc[cash_mask, 'sector'].fillna('Cash & Equivalents')
            final_df.loc[cash_mask, 'geography'] = final_df.loc[cash_mask, 'geography'].fillna('Global')

            # Derivatives
            deriv_mask = final_df['asset_class'] == 'Derivative'
            final_df.loc[deriv_mask, 'sector'] = final_df.loc[deriv_mask, 'sector'].fillna('Derivatives')
            final_df.loc[deriv_mask, 'geography'] = final_df.loc[deriv_mask, 'geography'].fillna('Global')

        # Fill remaining gaps
        final_df['sector'] = final_df['sector'].fillna('Unknown')
        final_df['geography'] = final_df['geography'].fillna('Unknown')

        # Reorder columns for better readability
        # Check if asset_class exists in columns to include it
        base_cols = ['isin', 'name_y', 'sector', 'geography', 'direct', 'indirect', 'total_exposure', 'portfolio_percentage']
        if 'asset_class' in final_df.columns:
             base_cols.insert(2, 'asset_class')
        
        final_df = final_df[base_cols]
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
