# phases/active/aggregation.py
import pandas as pd
import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.manager import load_positions_from_db
from src.data.enrichment import enrich_securities
from src.utils.classification import classify_holding

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def run_aggregation(direct_positions, etf_positions, etf_holdings_map):
    """
    Main function to run the entire exposure aggregation process.
    Accepts DataFrames and a dictionary of holdings to decouple logic from I/O.
    """
    output_filepath = 'outputs/true_exposure_report.csv'

    if direct_positions.empty and etf_positions.empty:
        logger.warning("No positions found. Exiting aggregation.")
        return pd.DataFrame()

    aggregated_exposures = {}

    # 1. Process Direct Holdings
    logger.info("Processing direct holdings...")
    if not direct_positions.empty:
        for _, row in direct_positions.iterrows():
            isin = row['isin']
            aggregated_exposures[isin] = {
                'name': row['name'],
                'direct': row['market_value'],
                'indirect': 0.0,
                'sector': 'Direct Holding', # Temporary default, ideally enriched too
                'geography': 'Global'
            }
            # Note: Direct holdings enrichment happens in reporting.py usually, 
            # or we should enrich them here if we want consistent 'sector' data in the aggregation step.
            # For now, we keep the existing flow where reporting.py enriches the final list.
            
    logger.info("Direct holdings processed.")

    # 2. Process Indirect Holdings
    logger.info("Processing indirect holdings (via ETFs)...")
    all_holdings = pd.DataFrame()
    if not etf_positions.empty:
        for _, etf in etf_positions.iterrows():
            etf_isin = etf['isin']
            etf_market_value = etf['market_value']
            logger.info(f"  - Processing ETF: {etf['name']} (Value: €{etf_market_value:,.2f})")

            etf_holdings = etf_holdings_map.get(etf_isin)
            if etf_holdings is None or etf_holdings.empty:
                logger.warning(f"    - No holdings found for {etf_isin} in the provided map. Skipping.")
                continue
            
            # Make a copy to avoid SettingWithCopy warnings on the original dataframe in the map
            etf_holdings = etf_holdings.copy()

            # --- Step 1: Classification ---
            # Apply classification logic to identify Cash/Derivatives
            etf_holdings['asset_class'] = etf_holdings.apply(
                lambda x: classify_holding(x.get('ticker', ''), x.get('name', '')), axis=1
            )
            
            non_equity_count = len(etf_holdings[etf_holdings['asset_class'] != 'Equity'])
            if non_equity_count > 0:
                logger.info(f"    - Classified {non_equity_count} rows as Non-Equity (Cash/Derivatives).")

            # --- Step 2: Enrichment (Equity Only) ---
            # Only enrich rows classified as Equity
            equity_mask = etf_holdings['asset_class'] == 'Equity'
            equity_holdings = etf_holdings[equity_mask]

            # If 'isin' column is missing (iShares), enrich to get it
            # Note: We only need to fetch metadata/ISINs for Equities.
            if 'isin' not in etf_holdings.columns:
                logger.info("    - 'isin' column not found. Enriching Equity holdings data...")
                
                # Filter out rows with invalid tickers before enrichment
                equity_holdings = equity_holdings.dropna(subset=['ticker'])
                equity_holdings = equity_holdings[equity_holdings['ticker'].apply(lambda x: isinstance(x, str))]

                holdings_list = equity_holdings.to_dict('records')
                enriched_holdings = enrich_securities(holdings_list)
                
                if enriched_holdings:
                    enriched_df = pd.DataFrame(enriched_holdings)
                else:
                    enriched_df = pd.DataFrame(columns=['ticker', 'isin'])

                if 'ticker' in enriched_df.columns and 'ticker' in etf_holdings.columns:
                    # Merge enrichment back into main dataframe
                    etf_holdings = pd.merge(etf_holdings, enriched_df[['ticker', 'isin']], on='ticker', how='left')
                    logger.info("    - Enrichment complete. Merged ISINs into holdings.")
                    
                    # Fill missing ISINs for Non-Equities with a placeholder
                    missing_isin_mask = etf_holdings['isin'].isnull()
                    etf_holdings.loc[missing_isin_mask, 'isin'] = [f"NON_EQUITY_{i}" for i in range(missing_isin_mask.sum())]
                else:
                    logger.error("    - Cannot merge enriched data due to missing 'ticker' column.")
                    etf_holdings['isin'] = [f"UNKNOWN_{i}" for i in range(len(etf_holdings))]
            
            # Calculate indirect value
            etf_holdings['indirect'] = etf_holdings['weight_percentage'] / 100 * etf_market_value
            
            # DEBUG: Trace Large Holdings
            huge = etf_holdings[etf_holdings['indirect'] > 1000]
            if not huge.empty:
                 logger.info(f"🔎 FOUND LARGE HOLDING in ETF {etf_isin} ({etf['name']}):")
                 logger.info(huge[['name', 'weight_percentage', 'indirect']].to_string())
            
            all_holdings = pd.concat([all_holdings, etf_holdings])

    # DEBUG: Save intermediate holdings
    all_holdings.to_csv('outputs/debug_all_holdings.csv', index=False)

    if not all_holdings.empty:
        # We need to preserve asset_class info for reporting
        # But aggregation groups by ISIN. 
        # 'NON_EQUITY_X' ISINs are unique per ETF load (because of range index).
        # This means Cash won't be aggregated across ETFs.
        # To fix this, we should standardize ISINs for Cash.
        
        # Normalize Cash ISINs
        cash_mask = all_holdings['asset_class'] == 'Cash'
        all_holdings.loc[cash_mask, 'isin'] = 'CASH_USD' # Simplification
        all_holdings.loc[cash_mask, 'name'] = 'Cash & Equivalents'
        
        # Normalize Derivative ISINs? Maybe keep unique to see what they are.
        
        aggregated_indirect = all_holdings.groupby('isin').agg(
            indirect=('indirect', 'sum'),
            name=('name', 'first'),
            asset_class=('asset_class', 'first')
        ).reset_index()

        for _, row in aggregated_indirect.iterrows():
            isin = row['isin']
            if isin in aggregated_exposures:
                aggregated_exposures[isin]['indirect'] += row['indirect']
            else:
                aggregated_exposures[isin] = {
                    'name': row['name'],
                    'direct': 0.0,
                    'indirect': row['indirect'],
                    'asset_class': row.get('asset_class', 'Equity')
                }
    logger.info("Indirect holdings processed.")
    # --- Finalize and Formatting Output ---
    logger.info("--- Finalizing and Formatting Output ---")
    
    # Consolidate all holdings into a list of dictionaries
    final_holdings = []
    for isin, data in aggregated_exposures.items():
        final_holdings.append({
            'isin': isin,
            'name': data['name'],
            'direct': data.get('direct', 0.0),
            'indirect': data.get('indirect', 0.0),
            'asset_class': data.get('asset_class', 'Equity') # Pass this to reporting
        })

    if not final_holdings:
        logger.warning("No holdings to process. Output file will be empty.")
        # Create an empty file with headers
        pd.DataFrame(columns=['isin', 'name', 'direct', 'indirect', 'total_exposure', 'portfolio_percentage']).to_csv(output_filepath, index=False)
        return

    # Convert to DataFrame for final calculations
    final_df = pd.DataFrame(final_holdings)
    
    # Calculate total exposure and portfolio percentage
    final_df['total_exposure'] = final_df['direct'] + final_df['indirect']
    total_portfolio_value = final_df['total_exposure'].sum()
    
    if total_portfolio_value > 0:
        final_df['portfolio_percentage'] = (final_df['total_exposure'] / total_portfolio_value) * 100
    else:
        final_df['portfolio_percentage'] = 0.0

    # Save the final aggregated report
    final_df.to_csv(output_filepath, index=False)
    logger.info(f"Report saved to {output_filepath}")

    return final_df

if __name__ == '__main__':
    run_aggregation()