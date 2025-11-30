import pandas as pd
import os
import glob
import yfinance as yf

# --- Part 1: Debug Ghost Nvidia ---
print("--- Debugging Ghost NVIDIA ---")
cache_dir = "data/working/cache/adapter_cache"
etf_files = glob.glob(os.path.join(cache_dir, "*_*.csv"))

# Load ETF Market Values from export.csv to see how big the source is
try:
    export_df = pd.read_csv("data/inputs/2025-11-25T13-09_export.csv")
    # Create a map of ISIN -> Market Value
    etf_values = dict(zip(export_df["isin"], export_df["market_value"]))
    etf_names = dict(zip(export_df["isin"], export_df["name"]))
except Exception as e:
    print(f"Error loading export.csv: {e}")
    etf_values = {}

print(f"Loaded {len(etf_values)} ETF values from export.csv")

total_nvidia_indirect = 0

for f in etf_files:
    try:
        df = pd.read_csv(f)
        # Normalize columns
        df.columns = [c.strip().lower() for c in df.columns]

        # Find Nvidia
        # Ticker 'NVDA' or Name contains 'NVIDIA'
        mask = df["name"].str.contains("NVIDIA", case=False, na=False)
        if "ticker" in df.columns:
            mask = mask | (df["ticker"] == "NVDA")

        nvidia_rows = df[mask]

        if not nvidia_rows.empty:
            # Get parent ISIN from filename
            filename = os.path.basename(f)
            parent_isin = filename.split("_")[0]

            parent_value = etf_values.get(parent_isin, 0)
            parent_name = etf_names.get(parent_isin, "Unknown")

            for _, row in nvidia_rows.iterrows():
                weight = row.get("weight_percentage", 0)

                # Check if weight is valid number
                try:
                    weight = float(weight)
                except (ValueError, TypeError):
                    weight = 0

                indirect_val = (weight / 100.0) * parent_value
                total_nvidia_indirect += indirect_val

                if indirect_val > 1000:  # Only show significant contributors
                    print(f"FOUND HUGE CHUNK: Parent={parent_name} ({parent_isin})")
                    print(f"  - Parent Value: {parent_value:.2f}")
                    print(f"  - Nvidia Weight: {weight}")
                    print(f"  - Indirect Value: {indirect_val:.2f}")
    except Exception:
        pass

print(f"Calculated Total Indirect Nvidia: {total_nvidia_indirect:.2f}")

# --- Part 2: Debug Xiaomi Currency ---
print("\n--- Debugging Xiaomi Currency ---")
ticker = "1810.HK"
try:
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    last_price = hist["Close"].iloc[-1]
    currency = t.fast_info.get("currency")
    print(f"Ticker: {ticker}")
    print(f"Price: {last_price}")
    print(f"Currency: {currency}")

    # Check EUR rate
    if currency != "EUR":
        pair = f"{currency}EUR=X"
        fx = yf.Ticker(pair)
        rate = fx.history(period="1d")["Close"].iloc[-1]
        print(f"FX Rate ({pair}): {rate}")
        print(f"Price in EUR: {last_price * rate}")
except Exception as e:
    print(f"Error checking Xiaomi: {e}")

# --- Part 3: Debug SXR8 Existence ---
print("\n--- Debugging SXR8 Existence ---")
holdings_path = "data/true_data/portfolio_holdings.csv"
if os.path.exists(holdings_path):
    df_h = pd.read_csv(holdings_path)
    sxr8 = df_h[
        df_h["ticker"].str.contains("SXR8", na=False) | (df_h["isin"] == "IE00B5BMR087")
    ]
    if not sxr8.empty:
        print("Found SXR8 in portfolio_holdings.csv:")
        print(sxr8.to_string())
    else:
        print("SXR8 NOT found in portfolio_holdings.csv")
else:
    print("portfolio_holdings.csv missing")
