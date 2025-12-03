#!/usr/bin/env python3
"""
Ground Truth Quantity Recalculation Script.

Reverse-engineers correct quantities from GT values using actual Nov 24, 2025 prices.

Formula: Recalculated Quantity = GT Value (EUR) / Actual Price (EUR)

Usage:
    python scripts/recalculate_gt.py                    # Preview changes
    python scripts/recalculate_gt.py --apply            # Apply changes to GT file
    python scripts/recalculate_gt.py --debug ISIN       # Debug single position
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.historical_prices import (
    fetch_historical_price,
    get_historical_price_map,
    HistoricalPriceResult,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths
GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "true_data" / "ground_truth_validated.csv"
RECALCULATED_PATH = (
    PROJECT_ROOT / "data" / "true_data" / "ground_truth_recalculated.csv"
)
REFERENCE_DATE = "2025-11-24"

# Threshold for flagging a significant quantity change
CHANGE_THRESHOLD = 0.10  # 10% - quantities differing more than this will be highlighted


def load_ground_truth() -> pd.DataFrame:
    """Load the current ground truth file."""
    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(f"Ground truth file not found: {GROUND_TRUTH_PATH}")
    return pd.read_csv(GROUND_TRUTH_PATH)


def recalculate_quantities(
    preview_only: bool = True,
    debug_isin: Optional[str] = None,
) -> pd.DataFrame:
    """
    Recalculate quantities for all positions.

    Args:
        preview_only: If True, only show changes without applying
        debug_isin: If provided, only process this ISIN

    Returns:
        DataFrame with recalculated quantities
    """
    print(f"\n{'=' * 70}")
    print("GROUND TRUTH QUANTITY RECALCULATION")
    print(f"Reference Date: {REFERENCE_DATE}")
    print(f"Formula: Quantity = GT Value (EUR) / Actual Price (EUR)")
    print(f"{'=' * 70}\n")

    # Load ground truth
    df = load_ground_truth()

    if debug_isin:
        df = df[df["ISIN"] == debug_isin]
        if len(df) == 0:
            print(f"ERROR: ISIN {debug_isin} not found in ground truth")
            return pd.DataFrame()

    print(f"Processing {len(df)} positions...\n")

    # Build ticker override map
    ticker_overrides = {}
    for _, row in df.iterrows():
        if pd.notna(row.get("Yahoo_Ticker")):
            ticker_overrides[row["ISIN"]] = row["Yahoo_Ticker"]

    # Fetch all historical prices
    isins = df["ISIN"].tolist()
    price_results = get_historical_price_map(isins, REFERENCE_DATE, ticker_overrides)

    # Process each position
    results = []

    print("\nRecalculation Results:")
    print("-" * 90)
    print(
        f"{'ISIN':<15} {'Name':<25} {'GT Qty':>12} {'Recalc Qty':>12} {'Change':>10} {'Status':<8}"
    )
    print("-" * 90)

    changes_needed = 0
    errors = 0

    for _, row in df.iterrows():
        isin = row["ISIN"]
        name = row["Name"][:25]
        gt_qty = float(row["Quantity"])
        gt_value = float(row["Value_EUR"])

        price_result = price_results.get(isin)

        if price_result is None or price_result.source == "error":
            error_msg = price_result.error if price_result else "No price result"
            results.append(
                {
                    **row.to_dict(),
                    "Recalc_Quantity": None,
                    "Recalc_Notes": f"ERROR: {error_msg}",
                }
            )
            errors += 1
            print(
                f"{isin:<15} {name:<25} {gt_qty:>12.4f} {'ERROR':>12} {'-':>10} {'ERROR':<8}"
            )
            continue

        # Recalculate quantity
        if price_result.eur_price > 0:
            recalc_qty = gt_value / price_result.eur_price
        else:
            recalc_qty = gt_qty  # Keep original if price is zero

        # Calculate change percentage
        if gt_qty > 0:
            change_pct = (recalc_qty - gt_qty) / gt_qty
        else:
            change_pct = 0.0

        # Determine status
        abs_change = abs(change_pct)
        if abs_change <= 0.02:  # Within 2%
            status = "OK"
        elif abs_change <= CHANGE_THRESHOLD:
            status = "MINOR"
        else:
            status = "CHANGE"
            changes_needed += 1

        # Build notes
        notes = []
        if status == "CHANGE":
            notes.append(f"qty {gt_qty:.6f}->{recalc_qty:.6f} ({change_pct:+.1%})")

        # Store result
        result_row = row.to_dict()
        result_row["Recalc_Quantity"] = recalc_qty
        result_row["Recalc_Price_EUR"] = price_result.eur_price
        result_row["Recalc_Notes"] = "; ".join(notes) if notes else ""
        results.append(result_row)

        # Print row
        status_display = status
        if status == "CHANGE":
            status_display = "CHANGE*"

        print(
            f"{isin:<15} {name:<25} {gt_qty:>12.4f} {recalc_qty:>12.4f} {change_pct:>+9.1%} {status_display:<8}"
        )

        # Debug output for significant changes
        if debug_isin or (status == "CHANGE" and not preview_only):
            print(
                f"    Price: {price_result.raw_price:.2f} {price_result.currency} -> {price_result.eur_price:.2f} EUR (FX: {price_result.fx_rate:.4f})"
            )
            print(
                f"    GT Value: {gt_value:.2f} EUR / Price: {price_result.eur_price:.2f} EUR = {recalc_qty:.4f} units"
            )

    print("-" * 90)
    print(
        f"\nSummary: {changes_needed} positions need quantity updates, {errors} errors\n"
    )

    # Create result DataFrame
    result_df = pd.DataFrame(results)

    # Show detailed changes
    if changes_needed > 0:
        print("\nDetailed Changes Required:")
        print("-" * 70)
        for r in results:
            if r.get("Recalc_Notes") and "qty" in str(r.get("Recalc_Notes", "")):
                print(f"  {r['ISIN']}: {r['Name'][:30]}")
                print(f"    {r['Recalc_Notes']}")
                print()

    return result_df


def apply_recalculation(result_df: pd.DataFrame) -> None:
    """
    Apply recalculated quantities to create a new GT file.

    Args:
        result_df: DataFrame with recalculated quantities
    """
    print("\nApplying recalculated quantities...")

    # Load original for structure
    original_df = load_ground_truth()

    # Create output DataFrame
    output_df = original_df.copy()

    # Update quantities where recalculation succeeded
    updates = 0
    for _, row in result_df.iterrows():
        recalc_qty = row.get("Recalc_Quantity")
        if pd.notna(recalc_qty):
            isin = row["ISIN"]
            original_qty = output_df.loc[output_df["ISIN"] == isin, "Quantity"].values[
                0
            ]

            # Only update if significant change (>2%)
            if abs(recalc_qty - original_qty) / original_qty > 0.02:
                output_df.loc[output_df["ISIN"] == isin, "Quantity"] = recalc_qty

                # Update notes
                old_notes = output_df.loc[output_df["ISIN"] == isin, "Notes"].values[0]
                new_note = f"Recalc: qty {original_qty:.6f}->{recalc_qty:.6f}"
                if pd.isna(old_notes) or old_notes == "":
                    output_df.loc[output_df["ISIN"] == isin, "Notes"] = new_note
                else:
                    output_df.loc[output_df["ISIN"] == isin, "Notes"] = (
                        f"{old_notes}; {new_note}"
                    )

                updates += 1

    # Backup original
    backup_path = GROUND_TRUTH_PATH.with_suffix(
        f".csv.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    original_df.to_csv(backup_path, index=False)
    print(f"  Backed up original to: {backup_path}")

    # Save recalculated version
    output_df.to_csv(RECALCULATED_PATH, index=False)
    print(f"  Saved recalculated to: {RECALCULATED_PATH}")

    # Also save to main GT path
    output_df.to_csv(GROUND_TRUTH_PATH, index=False)
    print(f"  Updated main GT file:  {GROUND_TRUTH_PATH}")

    print(f"\n  {updates} positions updated")


def main():
    parser = argparse.ArgumentParser(
        description="Recalculate ground truth quantities from values and prices"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply recalculated quantities (default: preview only)",
    )
    parser.add_argument(
        "--debug",
        type=str,
        help="Debug a single ISIN with detailed output",
    )

    args = parser.parse_args()

    result_df = recalculate_quantities(
        preview_only=not args.apply,
        debug_isin=args.debug,
    )

    if args.apply and len(result_df) > 0:
        apply_recalculation(result_df)
        print("\nRecalculation complete. Run validation to verify:")
        print("  python scripts/validate_portfolio.py")
    elif not args.apply and len(result_df) > 0:
        print("\nThis was a preview. To apply changes, run:")
        print("  python scripts/recalculate_gt.py --apply")


if __name__ == "__main__":
    main()
