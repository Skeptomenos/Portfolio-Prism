import pandas as pd
from pathlib import Path
import sys
import os

# Add paths for imports
sys.path.extend(
    [
        os.path.join(os.path.dirname(__file__), "..", "completed"),
        os.path.join(os.path.dirname(__file__), "..", "active"),
        os.path.join(os.path.dirname(__file__), "..", "shared"),
    ]
)

from position_keeper import calculate_positions
from security_mapper import map_isins_to_tickers
from price_fetcher import fetch_latest_prices
from holdings_fetcher import fetch_etf_holdings, save_holdings_to_csv
from database import init_db, insert_security, insert_holdings


def phase2_pipeline() -> pd.DataFrame:
    """
    Phase 2: Map ISINs to tickers and fetch current prices.
    Returns a DataFrame with positions enriched with ticker and price data.
    """
    # Get positions
    script_dir = Path(__file__).parent
    trades_file = script_dir.parent / "outputs" / "trades.csv"

    if not trades_file.exists():
        raise FileNotFoundError(f"Trades file not found: {trades_file}")

    df = pd.read_csv(trades_file)
    positions = calculate_positions(df)

    if positions.empty:
        print("No positions found.")
        return pd.DataFrame()

    # Initialize DB
    init_db()

    # Map ISINs to tickers
    isins = positions["ISIN"].tolist()
    mappings = map_isins_to_tickers(isins)

    # Merge mappings
    positions = pd.merge(positions, mappings, on="ISIN", how="left")

    # Fetch prices for tickers
    tickers = positions["TICKER"].dropna().tolist()
    providers = positions["PROVIDER"].dropna().tolist()
    if tickers:
        prices = fetch_latest_prices(tickers, providers)
        positions = pd.merge(positions, prices, on="TICKER", how="left")
    else:
        positions["PRICE"] = None

    # Insert securities into DB
    for _, row in positions.iterrows():
        insert_security(
            isin=row["ISIN"],
            name=row["name"],
            ticker=row["TICKER"],
            provider=row["PROVIDER"],
            asset_type="etf"
            if row["TICKER"] in ["IWDA", "IUSA", "INDI", "DFNS", "XDEM"]
            else "stock",  # Hardcode for now
            price=row["PRICE"],
        )

    # Calculate current value
    positions["current_value"] = positions["total_quantity"] * positions["PRICE"]

    # Fetch holdings for ETFs
    for ticker in positions["TICKER"].dropna().unique():
        df_holdings = fetch_etf_holdings(ticker)
        if not df_holdings.empty:
            save_holdings_to_csv(ticker, df_holdings)
            # Find ISIN for this ticker
            isin = positions.loc[positions["TICKER"] == ticker, "ISIN"].iloc[0]
            insert_holdings(isin, df_holdings)

    return positions


def main():
    try:
        result = phase2_pipeline()
        print("Phase 2 Results:")
        print(result)
        # Save to CSV
        output_file = (
            Path(__file__).parent.parent / "outputs" / "positions_with_prices.csv"
        )
        result.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")
    except Exception as e:
        print(f"Error in Phase 2: {e}")


if __name__ == "__main__":
    main()
