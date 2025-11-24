import pandas as pd
import yfinance as yf
import time
import os
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths
INPUT_TRUTH = "data/true_data/portfolio_truth.csv"
OUTPUT_UNIVERSE = "data/true_data/asset_universe.csv"
OUTPUT_HOLDINGS = "data/true_data/portfolio_holdings.csv"

# Knowledge Base (Manual Mapping for Assets)
# Maps TR Ticker -> (ISIN, Yahoo_Ticker, Provider, Asset_Class)
KNOWLEDGE_BASE = {
    # ETFs (Providers verified)
    "IWDA": ("IE00B4L5Y983", "IWDA.AS", "iShares", "ETF"),
    "IUIT": ("IE00B3WJKG14", "IUIT.L", "iShares", "ETF"),
    "CSNDX": ("IE00B53SZB19", "CSNDX.MI", "iShares", "ETF"),
    "IUSA": ("IE0031442068", "IUSA.MI", "iShares", "ETF"),
    "NQSE": ("IE00BYVQ9F29", "NQSE.DE", "iShares", "ETF"),
    "EXXT": ("DE000A0F5UF5", "EXXT.DE", "iShares", "ETF"),
    "XDEM": ("IE00BL25JP72", "XDEM.DE", "Xtrackers", "ETF"),
    "DFEN": ("IE000YYE6WK5", "DFEN.DE", "VanEck", "ETF"),
    "CSPX": ("IE00B5BMR087", "SXR8.DE", "iShares", "ETF"),
    "MEUD": ("LU0908500753", "LYP6.DE", "Amundi", "ETF"),
    "INR":  ("FR0010361683", "INR.PA", "Amundi", "ETF"),

    # Stocks (ISINs manually verified for accuracy)
    "NVDA": ("US67066G1040", "NVDA", "N/A", "Stock"),
    "GOOGL": ("US02079K3059", "GOOGL", "N/A", "Stock"),
    "MSFT": ("US5949181045", "MSFT", "N/A", "Stock"),
    "ABBV": ("US00287Y1091", "ABBV", "N/A", "Stock"),
    "CVX":  ("US1667641005", "CVX", "N/A", "Stock"),
    "AMZN": ("US0231351067", "AMZN", "N/A", "Stock"),
    "AMD":  ("US0079031078", "AMD", "N/A", "Stock"),
    "HFG":  ("DE000A161408", "HFG.DE", "N/A", "Stock"),
    "TKA":  ("DE0007500001", "TKA.DE", "N/A", "Stock"),
    "1810": ("KYG9830T1067", "1810.HK", "N/A", "Stock"),
    "META": ("US30303M1027", "META", "N/A", "Stock"),
    "TSLA": ("US88160R1014", "TSLA", "N/A", "Stock"),
    "VUL":  ("AU0000066006", "VUL.AX", "N/A", "Stock"), # Check exchange (AX=Sydney, Frankfurt is better for TR?)
    # TR likely uses Frankfurt for VUL. Let's use Frankfurt ticker for pricing: VUL.F? No, Knowledge Base Ticker is TR Ticker.
    # Yahoo Ticker for VUL in EUR: "VM3.F"
    
    "ALV":  ("DE0008404005", "ALV.DE", "N/A", "Stock"),
    "BVB":  ("DE0005493092", "BVB.DE", "N/A", "Stock"),
    "TAAT": ("CA87320L1031", "2TP.F", "N/A", "Stock"),
    "PLTR": ("US69608A1088", "PLTR", "N/A", "Stock"),
    "CL":   ("CA22587M1068", "6MH.F", "N/A", "Stock"),
    "-":    ("DE000TKMS000", "TKMS", "N/A", "Stock"), # Placeholder
}

# Special Overrides for Pricing Tickers (European Markets)
PRICING_OVERRIDES = {
    "VUL": "VM3.F",
}

def resolve_details(row):
    tr_ticker = row['Ticker']
    name = row['Name']
    
    # 1. Check Knowledge Base
    if tr_ticker in KNOWLEDGE_BASE:
        isin, yahoo_ticker, provider, asset_class = KNOWLEDGE_BASE[tr_ticker]
        
        # Apply pricing override if needed
        if tr_ticker in PRICING_OVERRIDES:
            yahoo_ticker = PRICING_OVERRIDES[tr_ticker]
            
        return isin, yahoo_ticker, provider, asset_class
    
    # 2. Fallback (Should not happen for the current portfolio if KB is complete)
    logger.warning(f"Unknown asset: {tr_ticker} ({name}). Using defaults.")
    return f"UNKNOWN_{tr_ticker}", tr_ticker, "N/A", "Stock"

def migrate():
    logger.info("--- Starting Migration to Relational Model ---")
    
    if not os.path.exists(INPUT_TRUTH):
        logger.error(f"Input file not found: {INPUT_TRUTH}")
        return

    df_truth = pd.read_csv(INPUT_TRUTH)
    
    universe_rows = []
    holdings_rows = []
    
    logger.info(f"Processing {len(df_truth)} entries...")
    
    for _, row in df_truth.iterrows():
        tr_ticker = row['Ticker']
        name = row['Name']
        quantity = row['Quantity']
        
        # Get details
        isin, yahoo_ticker, provider, asset_class = resolve_details(row)
        
        # Add to Universe
        universe_rows.append({
            "ISIN": isin,
            "TR_Ticker": tr_ticker,
            "Yahoo_Ticker": yahoo_ticker,
            "Name": name,
            "Provider": provider,
            "Asset_Class": asset_class
        })
        
        # Add to Holdings
        holdings_rows.append({
            "ISIN": isin,
            "Quantity": quantity
        })
        
        print(f"Mapped: {name[:20]}... -> {isin} | {yahoo_ticker}")

    # Create DataFrames
    df_universe = pd.DataFrame(universe_rows)
    df_holdings = pd.DataFrame(holdings_rows)
    
    # Remove duplicates from Universe
    df_universe.drop_duplicates(subset=['ISIN'], inplace=True)
    
    # Save
    df_universe.to_csv(OUTPUT_UNIVERSE, index=False)
    df_holdings.to_csv(OUTPUT_HOLDINGS, index=False)
    
    logger.info(f"--- Migration Complete ---")
    logger.info(f"Created {OUTPUT_UNIVERSE} with {len(df_universe)} assets.")
    logger.info(f"Created {OUTPUT_HOLDINGS} with {len(df_holdings)} positions.")

if __name__ == "__main__":
    migrate()