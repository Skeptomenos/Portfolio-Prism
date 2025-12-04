#!/usr/bin/env python3
"""
Test Adapter Script

A utility to test individual ETF adapters with a single ISIN.
Useful for verifying new adapters work correctly before running the full pipeline.

Usage:
    python scripts/test_adapter.py <ISIN>           # Test a specific ISIN
    python scripts/test_adapter.py --list           # List all registered adapters
    python scripts/test_adapter.py --help           # Show help

Examples:
    python scripts/test_adapter.py IE00BK5BQT80     # Test Vanguard FTSE All-World
    python scripts/test_adapter.py IE00B4L5Y983     # Test iShares MSCI World
    python scripts/test_adapter.py LU0292104469     # Test Xtrackers Europe IT
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.adapters.registry import AdapterRegistry, AdapterNotImplementedError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def list_adapters():
    """List all registered adapters and their supported ISINs."""
    registry = AdapterRegistry()

    print("\n" + "=" * 60)
    print("  Registered ETF Adapters")
    print("=" * 60)

    # Group ISINs by adapter
    adapter_isins = {}
    for isin, adapter_key in registry._isin_to_key.items():
        if adapter_key not in adapter_isins:
            adapter_isins[adapter_key] = []
        adapter_isins[adapter_key].append(isin)

    for adapter_key in sorted(adapter_isins.keys()):
        isins = adapter_isins[adapter_key]
        implemented = adapter_key in registry._key_to_class
        status = "✅" if implemented else "❌ (not implemented)"

        print(f"\n{adapter_key.upper()} {status}")
        print("-" * 40)
        for isin in sorted(isins):
            print(f"  {isin}")
        print(f"  Total: {len(isins)} ISINs")

    print("\n" + "=" * 60)
    print(f"  Total adapters: {len(adapter_isins)}")
    print(f"  Total ISINs: {len(registry._isin_to_key)}")
    print("=" * 60 + "\n")


def test_adapter(isin: str, verbose: bool = True):
    """
    Test an adapter with a specific ISIN.

    Args:
        isin: The ISIN to test
        verbose: Whether to print detailed output

    Returns:
        True if test passed, False otherwise
    """
    registry = AdapterRegistry()

    print("\n" + "=" * 60)
    print(f"  Testing Adapter for ISIN: {isin}")
    print("=" * 60)

    # 1. Check if ISIN is registered
    adapter_key = registry._isin_to_key.get(isin)
    if not adapter_key:
        print(f"\n❌ ISIN {isin} is not registered in adapter_registry.json")
        print(
            "   Add it with: python scripts/manage_assets.py add-adapter <ISIN> <provider>"
        )
        return False

    if adapter_key == "ignore":
        print(f"\n⚠️  ISIN {isin} is marked as 'ignore' (no look-through)")
        print("   This is typically for direct stocks or assets without holdings.")
        return True

    print(f"\n✅ Adapter: {adapter_key}")

    # 2. Get adapter instance
    try:
        adapter = registry.get_adapter(isin)
        if adapter is None:
            print(f"\n❌ Failed to get adapter instance for {isin}")
            return False
        print(f"✅ Adapter class: {adapter.__class__.__name__}")
    except AdapterNotImplementedError as e:
        print(f"\n❌ Adapter not implemented: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error getting adapter: {e}")
        return False

    # 3. Fetch holdings
    print(f"\n📥 Fetching holdings...")
    start_time = datetime.now()

    try:
        holdings_df = adapter.fetch_holdings(isin)
        elapsed = (datetime.now() - start_time).total_seconds()

        if holdings_df.empty:
            print(f"\n❌ Adapter returned empty DataFrame after {elapsed:.1f}s")
            print("   Check logs for error details.")
            return False

        print(f"\n✅ Fetched {len(holdings_df)} holdings in {elapsed:.1f}s")

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ Error fetching holdings after {elapsed:.1f}s: {e}")
        return False

    # 4. Validate data
    print("\n📋 Data Validation:")

    # Required columns
    required_cols = ["name", "weight_percentage"]
    optional_cols = ["ticker", "isin", "sector", "location", "country", "raw_ticker"]

    missing_required = [c for c in required_cols if c not in holdings_df.columns]
    if missing_required:
        print(f"   ❌ Missing required columns: {missing_required}")
        return False
    else:
        print(f"   ✅ Required columns present: {required_cols}")

    present_optional = [c for c in optional_cols if c in holdings_df.columns]
    print(f"   ℹ️  Optional columns present: {present_optional}")

    # Weight validation
    total_weight = holdings_df["weight_percentage"].sum()
    print(f"\n📊 Weight Statistics:")
    print(f"   Total weight: {total_weight:.2f}%")
    print(f"   Min weight: {holdings_df['weight_percentage'].min():.4f}%")
    print(f"   Max weight: {holdings_df['weight_percentage'].max():.2f}%")

    if total_weight < 90:
        print(f"   ⚠️  Warning: Total weight is below 90% (missing holdings?)")
    elif total_weight > 105:
        print(f"   ⚠️  Warning: Total weight exceeds 105% (duplicate entries?)")
    else:
        print(f"   ✅ Weight sum looks reasonable")

    # Negative weights
    neg_weights = holdings_df[holdings_df["weight_percentage"] < 0]
    if len(neg_weights) > 0:
        print(f"   ⚠️  Warning: {len(neg_weights)} holdings have negative weights")

    # 5. Sample data
    if verbose:
        print("\n📄 Sample Holdings (Top 10):")
        print("-" * 60)
        display_cols = ["name", "weight_percentage"]
        if "ticker" in holdings_df.columns:
            display_cols.insert(0, "ticker")
        if "isin" in holdings_df.columns:
            display_cols.insert(1, "isin")

        sample = holdings_df.nlargest(10, "weight_percentage")[display_cols]
        for _, row in sample.iterrows():
            name = str(row.get("name", ""))[:35]
            weight = row.get("weight_percentage", 0)
            ticker = row.get("ticker", "-") or "-"
            print(f"   {ticker:10} | {name:35} | {weight:6.2f}%")

    # 6. Summary
    print("\n" + "=" * 60)
    print("  ✅ TEST PASSED")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  ISIN: {isin}")
    print(f"  Adapter: {adapter_key}")
    print(f"  Holdings: {len(holdings_df)}")
    print(f"  Total Weight: {total_weight:.2f}%")
    print(f"  Fetch Time: {elapsed:.1f}s")
    print("")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test ETF adapters with a single ISIN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_adapter.py IE00BK5BQT80     # Test Vanguard ETF
  python scripts/test_adapter.py IE00B4L5Y983     # Test iShares ETF
  python scripts/test_adapter.py --list           # List all adapters
        """,
    )

    parser.add_argument("isin", nargs="?", help="ISIN to test")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all registered adapters"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimal output (no sample data)"
    )

    args = parser.parse_args()

    if args.list:
        list_adapters()
        return 0

    if not args.isin:
        parser.print_help()
        return 1

    # Validate ISIN format
    isin = args.isin.upper().strip()
    if len(isin) != 12:
        print(f"❌ Invalid ISIN format: {isin}")
        print("   ISIN should be exactly 12 characters")
        return 1

    # Run test
    success = test_adapter(isin, verbose=not args.quiet)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
