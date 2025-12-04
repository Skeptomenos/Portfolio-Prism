#!/usr/bin/env python3
"""
Export current ETF holdings to community_data/ for Docker distribution.

This seeds the community database with your ETF holdings so friends
get immediate functionality without needing to fetch anything.

Usage:
    python scripts/export_holdings_cache.py

Output:
    community_data/etf_holdings/*.csv - One file per ETF
    community_data/etf_holdings/_metadata.json - Cache metadata
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime

import pandas as pd

from src.adapters.registry import AdapterRegistry
from src.data.state_manager import load_portfolio_state
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

COMMUNITY_DIR = Path("community_data/etf_holdings")
METADATA_FILE = COMMUNITY_DIR / "_metadata.json"


def main() -> None:
    """Export all ETF holdings to community_data/ directory."""
    print("=" * 60)
    print("  ETF Holdings Export to Community Data")
    print("=" * 60)
    print()

    # Create output directory
    COMMUNITY_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {COMMUNITY_DIR.absolute()}")
    print()

    # Load portfolio to get ETF list
    try:
        stocks, etfs = load_portfolio_state()
    except Exception as e:
        print(f"[ERROR] Failed to load portfolio: {e}")
        return

    if etfs.empty:
        print("[ERROR] No ETFs found in portfolio")
        return

    print(f"Found {len(etfs)} ETFs in portfolio:")
    for _, etf in etfs.iterrows():
        print(f"  - {etf['name']} ({etf['isin']})")
    print()

    # Initialize adapter registry
    try:
        registry = AdapterRegistry()
    except Exception as e:
        print(f"[ERROR] Failed to initialize adapter registry: {e}")
        return

    # Track results
    metadata = _load_existing_metadata()
    success_count = 0
    fail_count = 0
    skipped_count = 0

    print("-" * 60)
    print("Processing ETFs...")
    print("-" * 60)

    for _, etf in etfs.iterrows():
        isin = etf["isin"]
        name = etf["name"]

        print(f"\n[{isin}] {name}")

        # Check if already cached and fresh
        if _is_fresh_cache(isin, metadata):
            print("  -> Skipped (already cached and fresh)")
            skipped_count += 1
            continue

        try:
            # Fetch holdings via adapter
            adapter = registry.get_adapter(isin)
            adapter_name = adapter.__class__.__name__
            print(f"  -> Using {adapter_name}")

            holdings = adapter.fetch_holdings(isin)

            # Validate
            if holdings.empty:
                print("  -> [WARN] Empty holdings, skipping")
                fail_count += 1
                continue

            # Check required columns
            required_cols = ["isin", "name", "weight_percentage"]
            missing_cols = [c for c in required_cols if c not in holdings.columns]
            if missing_cols:
                print(f"  -> [WARN] Missing columns: {missing_cols}")
                # Try to continue anyway with available data

            # Normalize weight column
            holdings = _normalize_holdings(holdings)

            # Save to community directory
            output_path = COMMUNITY_DIR / f"{isin}.csv"
            holdings.to_csv(output_path, index=False)

            # Calculate stats
            total_weight = (
                holdings["weight_percentage"].sum()
                if "weight_percentage" in holdings.columns
                else 0
            )

            # Update metadata
            metadata[isin] = {
                "name": name,
                "cached_at": datetime.now().isoformat(),
                "source": "owner_export",
                "holdings_count": len(holdings),
                "total_weight": round(total_weight, 2),
                "adapter": adapter_name,
                "columns": list(holdings.columns),
            }

            print(
                f"  -> Saved {len(holdings)} holdings ({total_weight:.1f}% total weight)"
            )
            success_count += 1

        except Exception as e:
            print(f"  -> [ERROR] {e}")
            fail_count += 1

    # Save metadata
    _save_metadata(metadata)

    # Summary
    print()
    print("=" * 60)
    print("  Export Summary")
    print("=" * 60)
    print(f"  Exported: {success_count}")
    print(f"  Skipped:  {skipped_count} (already fresh)")
    print(f"  Failed:   {fail_count}")
    print()
    print(f"  Files saved to: {COMMUNITY_DIR.absolute()}")
    print(f"  Metadata: {METADATA_FILE.absolute()}")
    print()

    if success_count > 0 or skipped_count > 0:
        print("  Community data ready for Docker distribution!")
        print()
        print("  Next steps:")
        print("    1. git add community_data/")
        print("    2. git commit -m 'Update community ETF holdings'")
        print("    3. git push")

    # List all cached files
    print()
    print("-" * 60)
    print("Cached ETF Holdings:")
    print("-" * 60)
    for csv_file in sorted(COMMUNITY_DIR.glob("*.csv")):
        if csv_file.name != "_metadata.json":
            isin = csv_file.stem
            info = metadata.get(isin, {})
            name = info.get("name", "Unknown")
            count = info.get("holdings_count", "?")
            print(f"  {isin}: {name} ({count} holdings)")


def _normalize_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize holdings DataFrame to standard format."""
    df = df.copy()

    # Ensure weight column exists and is numeric
    if "weight_percentage" in df.columns:
        df["weight_percentage"] = pd.to_numeric(
            df["weight_percentage"], errors="coerce"
        )

        # Check if weights are decimals (sum < 2) and convert to percentage
        total = df["weight_percentage"].sum()
        if 0 < total < 2:
            df["weight_percentage"] = df["weight_percentage"] * 100
            print(f"  -> Converted decimal weights to percentage (was {total:.4f})")

    # Clean string columns
    for col in ["isin", "name", "ticker"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["nan", "None", "N/A", ""], pd.NA)

    # Remove rows with no weight
    if "weight_percentage" in df.columns:
        before = len(df)
        df = df.dropna(subset=["weight_percentage"])
        df = df[df["weight_percentage"] > 0]
        after = len(df)
        if before != after:
            print(f"  -> Removed {before - after} rows with invalid weight")

    return df


def _is_fresh_cache(isin: str, metadata: dict, max_age_days: int = 7) -> bool:
    """Check if cached data is fresh enough."""
    if isin not in metadata:
        return False

    cached_at = metadata[isin].get("cached_at")
    if not cached_at:
        return False

    try:
        cache_time = datetime.fromisoformat(cached_at)
        age = datetime.now() - cache_time
        return age.days < max_age_days
    except:
        return False


def _load_existing_metadata() -> dict:
    """Load existing metadata if present."""
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text())
        except:
            pass
    return {}


def _save_metadata(metadata: dict) -> None:
    """Save metadata to JSON file."""
    # Add summary stats
    metadata["_stats"] = {
        "total_etfs": len([k for k in metadata if not k.startswith("_")]),
        "last_updated": datetime.now().isoformat(),
        "exported_by": "scripts/export_holdings_cache.py",
    }

    METADATA_FILE.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
