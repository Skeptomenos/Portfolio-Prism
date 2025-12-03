#!/usr/bin/env python3
"""
Portfolio Validation Script.

Compares calculated portfolio values against ground truth to identify
discrepancies in price fetching, currency conversion, or ticker mapping.

Usage:
    python scripts/validate_portfolio.py                    # Batch validation
    python scripts/validate_portfolio.py --debug ISIN       # Debug single position
    python scripts/validate_portfolio.py --date 2025-11-24  # Override date
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.historical_prices import (
    fetch_historical_price,
    get_historical_price_map,
    calculate_position_value,
    get_ticker_for_isin,
    HistoricalPriceResult,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Paths
GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "true_data" / "ground_truth_validated.csv"
DEFAULT_REFERENCE_DATE = "2025-11-24"
DEFAULT_TOLERANCE = 0.02  # 2%


@dataclass
class PositionValidation:
    """Validation result for a single position."""

    isin: str
    name: str
    gt_quantity: float
    gt_value: float
    calc_value: float
    difference: float
    difference_pct: float
    status: str  # "PASS", "FAIL", "WARN", "ERROR"
    ticker: str = ""
    raw_price: float = 0.0
    currency: str = ""
    fx_rate: float = 1.0
    notes: str = ""


@dataclass
class ValidationResult:
    """Overall validation result."""

    reference_date: str
    tolerance: float
    total_positions: int
    passed: int
    failed: int
    warnings: int
    errors: int
    gt_portfolio_value: float
    calc_portfolio_value: float
    discrepancy: float
    discrepancy_pct: float
    positions: List[PositionValidation] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Generate one-line summary."""
        return (
            f"{self.passed}/{self.total_positions} passed, "
            f"{self.failed} failed, {self.warnings} warnings, "
            f"Portfolio: {self.discrepancy_pct:+.1%} discrepancy"
        )


def load_ground_truth(path: Optional[Path] = None) -> pd.DataFrame:
    """Load and validate ground truth file."""
    path = path or GROUND_TRUTH_PATH

    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")

    df = pd.read_csv(path)

    required_cols = ["ISIN", "Name", "Quantity", "Value_EUR", "Yahoo_Ticker"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Ground truth missing required columns: {missing}")

    return df


def validate_portfolio(
    reference_date: str = DEFAULT_REFERENCE_DATE,
    tolerance: float = DEFAULT_TOLERANCE,
    ground_truth_path: Optional[Path] = None,
) -> ValidationResult:
    """
    Validate portfolio against ground truth.

    Args:
        reference_date: Date for historical price comparison (YYYY-MM-DD)
        tolerance: Acceptable difference percentage (e.g., 0.02 for 2%)
        ground_truth_path: Optional path to ground truth file

    Returns:
        ValidationResult with detailed position-by-position comparison
    """
    print(f"\n{'=' * 60}")
    print(f"PORTFOLIO VALIDATION")
    print(f"Reference Date: {reference_date}")
    print(f"Tolerance: {tolerance:.0%}")
    print(f"{'=' * 60}\n")

    # Load ground truth
    gt_df = load_ground_truth(ground_truth_path)
    print(f"Loaded {len(gt_df)} positions from ground truth\n")

    # Build ticker override map from ground truth
    ticker_overrides = {}
    for _, row in gt_df.iterrows():
        if pd.notna(row.get("Yahoo_Ticker")):
            ticker_overrides[row["ISIN"]] = row["Yahoo_Ticker"]

    # Fetch historical prices
    isins = gt_df["ISIN"].tolist()
    price_results = get_historical_price_map(isins, reference_date, ticker_overrides)

    # Compare each position
    positions = []
    gt_total = 0.0
    calc_total = 0.0
    passed = 0
    failed = 0
    warnings = 0
    errors = 0

    print("\nPosition-by-Position Comparison:")
    print("-" * 80)

    for _, row in gt_df.iterrows():
        isin = row["ISIN"]
        name = row["Name"]
        gt_qty = float(row["Quantity"])
        gt_value = float(row["Value_EUR"])

        gt_total += gt_value

        # Get price result
        price_result = price_results.get(isin)

        if price_result is None or price_result.source == "error":
            error_msg = price_result.error if price_result else "No price result"
            positions.append(
                PositionValidation(
                    isin=isin,
                    name=name,
                    gt_quantity=gt_qty,
                    gt_value=gt_value,
                    calc_value=0.0,
                    difference=-gt_value,
                    difference_pct=-1.0,
                    status="ERROR",
                    notes=error_msg,
                )
            )
            errors += 1
            print(f"  ERROR | {name[:30]:30} | {isin} | {error_msg}")
            continue

        # Calculate value
        calc_value = calculate_position_value(gt_qty, price_result)
        calc_total += calc_value

        # Compare
        difference = calc_value - gt_value
        difference_pct = difference / gt_value if gt_value != 0 else 0.0
        abs_diff_pct = abs(difference_pct)

        # Determine status
        if abs_diff_pct <= tolerance:
            status = "PASS"
            passed += 1
            status_icon = "OK"
        elif abs_diff_pct <= 0.10:  # 10% warning threshold
            status = "WARN"
            warnings += 1
            status_icon = "WARN"
        else:
            status = "FAIL"
            failed += 1
            status_icon = "FAIL"

        positions.append(
            PositionValidation(
                isin=isin,
                name=name,
                gt_quantity=gt_qty,
                gt_value=gt_value,
                calc_value=calc_value,
                difference=difference,
                difference_pct=difference_pct,
                status=status,
                ticker=price_result.ticker,
                raw_price=price_result.raw_price,
                currency=price_result.currency,
                fx_rate=price_result.fx_rate,
            )
        )

        # Print result
        print(
            f"  {status_icon:4} | {name[:30]:30} | "
            f"GT: {gt_value:>10,.2f} | Calc: {calc_value:>10,.2f} | "
            f"Diff: {difference_pct:>+7.1%}"
        )

    # Calculate overall discrepancy
    discrepancy = calc_total - gt_total
    discrepancy_pct = discrepancy / gt_total if gt_total != 0 else 0.0

    # Create result
    result = ValidationResult(
        reference_date=reference_date,
        tolerance=tolerance,
        total_positions=len(gt_df),
        passed=passed,
        failed=failed,
        warnings=warnings,
        errors=errors,
        gt_portfolio_value=gt_total,
        calc_portfolio_value=calc_total,
        discrepancy=discrepancy,
        discrepancy_pct=discrepancy_pct,
        positions=positions,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(
        f"  Positions: {passed} passed, {failed} failed, {warnings} warnings, {errors} errors"
    )
    print(f"  Ground Truth Total:  EUR {gt_total:>12,.2f}")
    print(f"  Calculated Total:    EUR {calc_total:>12,.2f}")
    print(f"  Discrepancy:         EUR {discrepancy:>+12,.2f} ({discrepancy_pct:+.1%})")
    print()

    if failed > 0 or errors > 0:
        print("FAILED POSITIONS (>10% discrepancy):")
        print("-" * 60)
        for pos in positions:
            if pos.status in ("FAIL", "ERROR"):
                print(f"  {pos.isin} | {pos.name[:30]:30}")
                print(f"    GT Value:   EUR {pos.gt_value:>10,.2f}")
                print(f"    Calc Value: EUR {pos.calc_value:>10,.2f}")
                print(f"    Difference: {pos.difference_pct:>+.1%}")
                if pos.notes:
                    print(f"    Notes: {pos.notes}")
                print()

    return result


def debug_position(isin: str, reference_date: str = DEFAULT_REFERENCE_DATE) -> None:
    """
    Debug a single position with detailed output.

    Args:
        isin: ISIN to debug
        reference_date: Date for historical price
    """
    print(f"\n{'=' * 60}")
    print(f"DEBUG: {isin}")
    print(f"Reference Date: {reference_date}")
    print(f"{'=' * 60}\n")

    # Load ground truth
    try:
        gt_df = load_ground_truth()
        gt_row = gt_df[gt_df["ISIN"] == isin]

        if gt_row.empty:
            print(f"WARNING: ISIN {isin} not found in ground truth")
            gt_qty = None
            gt_value = None
            gt_ticker = None
        else:
            gt_row = gt_row.iloc[0]
            gt_qty = float(gt_row["Quantity"])
            gt_value = float(gt_row["Value_EUR"])
            gt_ticker = gt_row.get("Yahoo_Ticker")

            print("Step 1: Ground Truth Data")
            print(f"  Name:     {gt_row['Name']}")
            print(f"  Quantity: {gt_qty}")
            print(f"  Value:    EUR {gt_value:,.2f}")
            print(f"  Ticker:   {gt_ticker}")
            print()
    except Exception as e:
        print(f"ERROR loading ground truth: {e}")
        gt_qty = None
        gt_value = None
        gt_ticker = None

    # Step 2: Ticker resolution
    print("Step 2: Ticker Resolution")
    ticker_from_map = get_ticker_for_isin(isin)
    print(f"  From ticker_map.json: {ticker_from_map}")
    print(f"  From ground truth:    {gt_ticker}")

    ticker_to_use = gt_ticker or ticker_from_map
    print(f"  Using: {ticker_to_use}")
    print()

    # Step 3: Price fetch
    print("Step 3: Historical Price Fetch")
    result = fetch_historical_price(isin, reference_date, ticker_to_use)

    print(f"  Ticker:      {result.ticker}")
    print(f"  Date:        {result.date}")
    print(f"  Actual Date: {result.actual_date}")
    print(f"  Raw Price:   {result.raw_price:.4f}")
    print(f"  Currency:    {result.currency}")
    print(f"  FX Rate:     {result.fx_rate:.4f}")
    print(f"  EUR Price:   {result.eur_price:.4f}")
    print(f"  Source:      {result.source}")
    if result.error:
        print(f"  Error:       {result.error}")
    print()

    # Step 4: Value calculation
    if gt_qty is not None:
        print("Step 4: Value Calculation")
        calc_value = calculate_position_value(gt_qty, result)
        print(f"  Quantity:    {gt_qty}")
        print(f"  EUR Price:   {result.eur_price:.4f}")
        print(f"  Calc Value:  EUR {calc_value:,.2f}")
        print()

        if gt_value is not None:
            print("Step 5: Comparison")
            difference = calc_value - gt_value
            difference_pct = difference / gt_value if gt_value != 0 else 0
            print(f"  GT Value:    EUR {gt_value:,.2f}")
            print(f"  Calc Value:  EUR {calc_value:,.2f}")
            print(f"  Difference:  EUR {difference:+,.2f} ({difference_pct:+.1%})")

            if abs(difference_pct) > 0.10:
                print()
                print("  !! LARGE DISCREPANCY - Possible causes:")
                print("     - Wrong ticker mapping")
                print("     - Currency conversion error")
                print("     - Ground truth value incorrect")
                print("     - Stock split or corporate action")


def main():
    parser = argparse.ArgumentParser(
        description="Validate portfolio against ground truth"
    )
    parser.add_argument(
        "--debug", type=str, help="Debug a single ISIN with detailed output"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=DEFAULT_REFERENCE_DATE,
        help=f"Reference date for historical prices (default: {DEFAULT_REFERENCE_DATE})",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
        help=f"Tolerance for pass/fail (default: {DEFAULT_TOLERANCE})",
    )

    args = parser.parse_args()

    if args.debug:
        debug_position(args.debug, args.date)
    else:
        result = validate_portfolio(args.date, args.tolerance)

        # Exit with error code if too many failures
        if result.failed > 0 or result.errors > 0:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
