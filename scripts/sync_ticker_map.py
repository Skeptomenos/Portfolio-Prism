import json
import pandas as pd
import os
import argparse
import shutil
from datetime import datetime
from collections import Counter
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

UNIVERSE_PATH = "config/asset_universe.csv"
TICKER_MAP_PATH = "config/ticker_map.json"


def load_ticker_map():
    """Load ticker map from JSON file."""
    if os.path.exists(TICKER_MAP_PATH):
        with open(TICKER_MAP_PATH, "r") as f:
            data = json.load(f)
            # Remove _comment if present
            if "_comment" in data:
                del data["_comment"]
            return data
    return {}


def validate_map():
    """Comprehensive validation of ticker_map.json"""

    print("🔍 Validating ticker map...")

    # Load files
    ticker_map = load_ticker_map()

    if not os.path.exists(UNIVERSE_PATH):
        print(f"❌ Universe file not found: {UNIVERSE_PATH}")
        return False

    universe_df = pd.read_csv(UNIVERSE_PATH)

    issues = []
    warnings = []

    # Check 1: Duplicate ISINs in map
    dup_isins = [k for k, v in Counter(ticker_map.keys()).items() if v > 1]
    if dup_isins:
        issues.append(f"❌ Duplicate ISINs in map: {dup_isins}")

    # Check 2: Same ticker for multiple ISINs
    ticker_counts = Counter(ticker_map.values())
    dup_tickers = {t: count for t, count in ticker_counts.items() if count > 1}
    if dup_tickers:
        warnings.append(f"⚠️  Ticker used for multiple ISINs: {dup_tickers}")

    # Check 3: Orphaned entries (in map but not in universe)
    universe_isins = set(universe_df["ISIN"])
    orphaned = set(ticker_map.keys()) - universe_isins
    if orphaned:
        warnings.append(
            f"⚠️  {len(orphaned)} orphaned ISINs (in map but not in universe)"
        )
        if len(orphaned) <= 5:
            warnings.append(f"     {list(orphaned)}")

    # Check 4: Inconsistencies (different ticker for same ISIN)
    inconsistencies = []
    for _, row in universe_df.iterrows():
        isin = row["ISIN"]
        universe_ticker = row["Yahoo_Ticker"]
        if pd.notna(universe_ticker) and universe_ticker != "-":
            if isin in ticker_map and ticker_map[isin] != universe_ticker:
                inconsistencies.append(
                    f"     {isin}: map={ticker_map[isin]}, universe={universe_ticker}"
                )

    if inconsistencies:
        issues.append(f"❌ {len(inconsistencies)} ticker mismatches:")
        issues.extend(inconsistencies[:5])  # Show first 5

    # Check 5: Missing tickers (in universe but not in map)
    missing = []
    for _, row in universe_df.iterrows():
        isin = row["ISIN"]
        universe_ticker = row["Yahoo_Ticker"]
        if pd.notna(universe_ticker) and universe_ticker != "-":
            if isin not in ticker_map:
                missing.append(isin)

    if missing:
        warnings.append(
            f"⚠️  {len(missing)} ISINs in universe but not in map (run sync to add)"
        )

    # Report
    if issues:
        print("\n🔴 Critical Issues:")
        for issue in issues:
            print(f"  {issue}")

    if warnings:
        print("\n🟡 Warnings:")
        for warning in warnings:
            print(f"  {warning}")

    if not issues and not warnings:
        print("✅ Ticker map is valid!")
        return True
    elif not issues:
        print("\n✅ No critical issues (warnings can be ignored)")
        return True
    else:
        print(f"\n❌ Found {len(issues)} critical issue(s)")
        return False


def rebuild_map():
    """Rebuild ticker_map.json from scratch"""

    print("🔨 Rebuilding ticker map from asset_universe.csv")

    # Backup existing
    if os.path.exists(TICKER_MAP_PATH):
        backup = TICKER_MAP_PATH + f".backup.{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copy(TICKER_MAP_PATH, backup)
        print(f"📦 Backed up to {os.path.basename(backup)}")

    # Load universe
    if not os.path.exists(UNIVERSE_PATH):
        print(f"❌ Universe file not found: {UNIVERSE_PATH}")
        return

    df = pd.read_csv(UNIVERSE_PATH)

    # Build map (only valid tickers)
    ticker_map = {}
    for _, row in df.iterrows():
        isin = row["ISIN"]
        ticker = row["Yahoo_Ticker"]

        if pd.notna(ticker) and ticker != "-":
            ticker_map[isin] = ticker

    # Sort by ISIN
    ticker_map = dict(sorted(ticker_map.items()))

    # Add comment
    output = {
        "_comment": "AUTO-GENERATED from config/asset_universe.csv. Run: python scripts/sync_ticker_map.py --mode rebuild",
        **ticker_map,
    }

    # Save
    with open(TICKER_MAP_PATH, "w") as f:
        json.dump(output, f, indent=4)

    print(f"✅ Rebuilt with {len(ticker_map)} tickers")
    print(f"💾 Saved to {TICKER_MAP_PATH}")


def sync_map():
    """Enhanced sync (incremental update with stats)"""

    logger.info("🔄 Syncing ticker map from asset_universe.csv")

    if not os.path.exists(UNIVERSE_PATH):
        logger.error(f"Universe file not found: {UNIVERSE_PATH}")
        return

    # Load Universe
    df = pd.read_csv(UNIVERSE_PATH)

    # Load existing map
    ticker_map = load_ticker_map()
    original_count = len(ticker_map)

    added = 0
    updated = 0

    for _, row in df.iterrows():
        isin = row["ISIN"]
        yahoo_ticker = row["Yahoo_Ticker"]

        # We only sync if we have a valid Yahoo Ticker
        if pd.notna(yahoo_ticker) and yahoo_ticker != "-":
            if isin not in ticker_map:
                ticker_map[isin] = yahoo_ticker
                added += 1
                print(f"  + Added: {isin} → {yahoo_ticker}")
            elif ticker_map[isin] != yahoo_ticker:
                print(f"  ↻ Updated: {isin} ({ticker_map[isin]} → {yahoo_ticker})")
                ticker_map[isin] = yahoo_ticker
                updated += 1

    # Save
    with open(TICKER_MAP_PATH, "w") as f:
        json.dump(ticker_map, f, indent=4)

    print("\n✅ Sync complete:")
    print(
        f"   {added} added, {updated} updated, {original_count - added - updated} unchanged"
    )
    print(f"   Total: {len(ticker_map)} tickers")


def main():
    parser = argparse.ArgumentParser(
        description="Manage ticker map synchronization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/sync_ticker_map.py                    # Sync (default)
  python scripts/sync_ticker_map.py --mode validate    # Validate
  python scripts/sync_ticker_map.py --mode rebuild     # Rebuild from scratch
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["sync", "rebuild", "validate"],
        default="sync",
        help="Operation mode (default: sync)",
    )
    args = parser.parse_args()

    if args.mode == "validate":
        validate_map()
    elif args.mode == "rebuild":
        rebuild_map()
    else:
        sync_map()


if __name__ == "__main__":
    main()
