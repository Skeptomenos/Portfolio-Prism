# phases/active/aggregation.py
import pandas as pd



from typing import Dict
from src.config import TRUE_EXPOSURE_REPORT
from src.data.enrichment import enrich_securities
from src.utils.classification import classify_holding

from src.utils.logging_config import get_logger
from src.core.health import health

logger = get_logger(__name__)

def run_aggregation(
    direct_positions: pd.DataFrame, 
    etf_positions: pd.DataFrame, 
    etf_holdings_map: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Main function to run the entire exposure aggregation process.
    Accepts DataFrames and a dictionary of holdings to decouple logic from I/O.
    """
    output_filepath = TRUE_EXPOSURE_REPORT

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
    logger.info(f"Total ETFs to process: {len(etf_positions)}") # Changed from etf_holdings_map to etf_positions for count of ETFs to be processed
    all_holdings = pd.DataFrame()
    if not etf_positions.empty:
        # Assuming etf_positions already contains only ETFs, no need for asset_class filter here.
        # Iterating as dict records is generally more efficient than iterrows for many operations.
        for etf in etf_positions.to_dict('records'): 
            etf_isin = etf['isin']
            etf_market_value = etf['market_value']
            logger.info(f"  - Processing ETF: {etf['name']} (ISIN: {etf_isin}, Value: €{etf_market_value:,.2f})")

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

                # === TIERED ENRICHMENT: Only enrich holdings >1% weight ===
                # This dramatically reduces API calls (1500 → ~100)
                ENRICHMENT_THRESHOLD = 1.0  # Only enrich if weight > 1%
                
                # Ensure weight_percentage column exists and is numeric
                if 'weight_percentage' not in equity_holdings.columns:
                    logger.warning("    ⚠️  'weight_percentage' column missing. Enriching all holdings.")
                    tier1_holdings = equity_holdings
                    tier2_holdings = pd.DataFrame()
                else:
                    equity_holdings['weight_percentage'] = pd.to_numeric(
                        equity_holdings['weight_percentage'], errors='coerce'
                    ).fillna(0.0)
                    
                    # Split into Tier 1 (>1%) and Tier 2 (≤1%)
                    tier1_mask = equity_holdings['weight_percentage'] > ENRICHMENT_THRESHOLD
                    tier1_holdings = equity_holdings[tier1_mask].copy()
                    tier2_holdings = equity_holdings[~tier1_mask].copy()
                    
                    # HEALTH CHECK: Tier Counts & Value Coverage
                    health.record_metric("tier1_holdings", len(tier1_holdings))
                    health.record_metric("tier2_holdings", len(tier2_holdings))
                    
                    # Calculate Value Coverage (Approximate based on weights)
                    # etf_market_value is available in the loop scope
                    tier1_weight = tier1_holdings['weight_percentage'].sum()
                    tier2_weight = tier2_holdings['weight_percentage'].sum()
                    total_weight = tier1_weight + tier2_weight
                    
                    if total_weight > 0:
                        tier1_val = (tier1_weight / total_weight) * etf_market_value
                        tier2_val = (tier2_weight / total_weight) * etf_market_value
                        health.record_value_coverage(tier1_val, tier2_val)
                    
                    logger.info(f"    - Tiered Enrichment: {len(tier1_holdings)} major (>1%), {len(tier2_holdings)} minor (≤1%)")
                    logger.info(f"    - Skipping ISIN resolution for {len(tier2_holdings)} minor holdings (will use fallback aggregation)")
                
                # Enrich only Tier 1 holdings (>1% weight)
                if not tier1_holdings.empty:
                    holdings_list = tier1_holdings.to_dict('records')
                    enriched_holdings = enrich_securities(holdings_list)
                    
                    if enriched_holdings:
                        enriched_df = pd.DataFrame(enriched_holdings)
                        health.record_metric("tier1_resolved", len(enriched_df))
                    else:
                        enriched_df = pd.DataFrame(columns=['ticker', 'isin'])
                else:
                    enriched_df = pd.DataFrame(columns=['ticker', 'isin'])
                
                # For Tier 2 holdings, set ISIN to N/A (fallback aggregation will handle them)
                if not tier2_holdings.empty:
                    tier2_holdings['isin'] = 'N/A'
                    # Combine Tier 1 (enriched) with Tier 2 (unenriched)
                    equity_holdings = pd.concat([tier1_holdings, tier2_holdings], ignore_index=True)

                if 'ticker' in enriched_df.columns and 'ticker' in etf_holdings.columns:
                    # Merge enrichment back into main dataframe
                    etf_holdings = pd.merge(etf_holdings, enriched_df[['ticker', 'isin']], on='ticker', how='left')
                    logger.info("    - Enrichment complete. Merged ISINs into holdings.")
                    
                    # Log ISIN resolution failures (only for Tier 1)
                    tier1_failed = etf_holdings[
                        (etf_holdings['asset_class'] == 'Equity') & 
                        (etf_holdings['isin'] == 'N/A') &
                        (etf_holdings['weight_percentage'] > ENRICHMENT_THRESHOLD)
                    ]
                    if not tier1_failed.empty:
                        health.record_metric("tier1_failed", len(tier1_failed))
                        logger.warning(f"    ⚠️  {len(tier1_failed)} major holdings (>1%) FAILED ISIN resolution:")
                        for _, row in tier1_failed.iterrows():
                            ticker = row['ticker']
                            logger.warning(f"        - {ticker}")
                            health.record_failure(
                                stage="ENRICHMENT",
                                item=ticker,
                                error="Tier 1 ISIN Resolution Failed",
                                fix=f"Add {ticker} to config/asset_universe.csv",
                                severity="MEDIUM"
                            )
                        if len(tier1_failed) > 10:
                            logger.warning(f"        ... and {len(tier1_failed) - 10} more")
                    
                    # Fill missing ISINs for Non-Equities with a placeholder
                    missing_isin_mask = etf_holdings['isin'].isnull()
                    etf_holdings.loc[missing_isin_mask, 'isin'] = [f"NON_EQUITY_{i}" for i in range(missing_isin_mask.sum())]
                else:
                    logger.error("    - Cannot merge enriched data due to missing 'ticker' column.")
                    etf_holdings['isin'] = [f"UNKNOWN_{i}" for i in range(len(etf_holdings))]
            
            # Calculate indirect value
            # Ensure weight_percentage is a float
            if 'weight_percentage' in etf_holdings.columns:
                 etf_holdings['weight_percentage'] = etf_holdings['weight_percentage'].astype(str).str.replace(',', '.').apply(pd.to_numeric, errors='coerce').fillna(0.0)
            else:
                 etf_holdings['weight_percentage'] = 0.0

            etf_holdings['indirect'] = etf_holdings['weight_percentage'] / 100 * etf_market_value
            
            # DEBUG: Trace Large Holdings
            huge = etf_holdings[etf_holdings['indirect'] > 1000]
            if not huge.empty:
                 logger.info(f"🔎 FOUND LARGE HOLDING in ETF {etf_isin} ({etf['name']}):")
                 for _, row in huge.iterrows():
                     logger.info(f"    -> {row.get('name', 'Unknown')} ({row.get('isin', 'No ISIN')}): {row['weight_percentage']:.2f}% = €{row['indirect']:,.2f}")
            
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
        
        # --- TIERED AGGREGATION LOGIC ---
        # Goal: Aggregate by ISIN if available (Tier 1), else by Ticker+Name (Tier 2)
        
        def generate_group_id(row):
            isin = row.get('isin', 'N/A')
            # Check for valid ISIN (simple length check + not N/A/UNKNOWN)
            if isin and isin not in ('N/A', 'nan', None) and not isin.startswith('UNKNOWN') and not isin.startswith('NON_EQUITY'):
                return isin
            
            # Fallback: Ticker + Name
            ticker = str(row.get('ticker', ''))
            name = str(row.get('name', ''))
            return f"FALLBACK|{ticker}|{name}"

        all_holdings['group_id'] = all_holdings.apply(generate_group_id, axis=1)

        aggregated_indirect = all_holdings.groupby('group_id').agg(
            indirect=('indirect', 'sum'),
            name=('name', 'first'),
            isin=('isin', 'first'), # Keep the original ISIN (even if N/A) for reference
            asset_class=('asset_class', 'first')
        ).reset_index()

        for _, row in aggregated_indirect.iterrows():
            # Use group_id as the unique identifier (ISIN or Fallback)
            key = row['group_id']
            
            if key in aggregated_exposures:
                aggregated_exposures[key]['indirect'] += row['indirect']
            else:
                aggregated_exposures[key] = {
                    'name': row['name'],
                    'direct': 0.0,
                    'indirect': row['indirect'],
                    'asset_class': row.get('asset_class', 'Equity')
                }
                # Store the best available ISIN for reference
                if row['isin'] and row['isin'] not in ('N/A', 'nan', None):
                     aggregated_exposures[key]['isin'] = row['isin']
                else:
                     aggregated_exposures[key]['isin'] = 'N/A'
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