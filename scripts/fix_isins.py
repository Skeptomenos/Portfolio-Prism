import pandas as pd

CSV_PATH = "config/asset_universe.csv"

def fix_isins():
    print(f"Loading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows.")
    
    # Debug GOOGL before fix
    googl = df[df['Yahoo_Ticker'] == 'GOOGL']
    if not googl.empty:
        print("Existing GOOGL entries:")
        print(googl)
    else:
        print("GOOGL not found in file.")
    
    # Target Updates
    # Keying by Yahoo_Ticker because that's what the pipeline uses for lookup
    updates = [
        {"ISIN": "US02079K3059", "TR_Ticker": "GOOGL", "Yahoo_Ticker": "GOOGL", "Name": "Alphabet Inc Class A", "Provider": "Manual", "Asset_Class": "Stock"},
        {"ISIN": "US02079K1079", "TR_Ticker": "GOOG", "Yahoo_Ticker": "GOOG", "Name": "Alphabet Inc Class C", "Provider": "Manual", "Asset_Class": "Stock"},
        {"ISIN": "US0846707026", "TR_Ticker": "BRKB", "Yahoo_Ticker": "BRKB", "Name": "Berkshire Hathaway Inc Class B", "Provider": "Manual", "Asset_Class": "Stock"},
        {"ISIN": "US64110L1061", "TR_Ticker": "NFLX", "Yahoo_Ticker": "NFLX", "Name": "Netflix Inc", "Provider": "Manual", "Asset_Class": "Stock"},
        {"ISIN": "US8725901040", "TR_Ticker": "TMUS", "Yahoo_Ticker": "TMUS", "Name": "T-Mobile US Inc", "Provider": "Manual", "Asset_Class": "Stock"},
        {"ISIN": "CA82509L1076", "TR_Ticker": "SHOP", "Yahoo_Ticker": "SHOP", "Name": "Shopify Inc", "Provider": "Manual", "Asset_Class": "Stock"},
        {"ISIN": "US0367511005", "TR_Ticker": "AMAT", "Yahoo_Ticker": "AMAT", "Name": "Applied Materials Inc", "Provider": "Manual", "Asset_Class": "Stock"},
    ]

    for up in updates:
        ticker = up['Yahoo_Ticker']
        # Remove existing rows with this Yahoo_Ticker to avoid duplicates
        initial_len = len(df)
        df = df[df['Yahoo_Ticker'] != ticker]
        if len(df) < initial_len:
            print(f"Removed existing entry for {ticker}")
            
        # Append new row
        df = pd.concat([df, pd.DataFrame([up])], ignore_index=True)
        print(f"Upserted {ticker} -> {up['ISIN']}")
        
    # Save
    df.to_csv(CSV_PATH, index=False)
    print(f"Saved {CSV_PATH} with {len(df)} rows.")

if __name__ == "__main__":
    fix_isins()
