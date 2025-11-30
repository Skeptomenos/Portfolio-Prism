#!/usr/bin/env python3
"""
Pipeline Validation Script

Compares pipeline output (Direct Holdings) against ground truth data (ground_truth_merged.csv).
Uses QUANTITY as the primary invariant check.

Usage:
    python -m scripts.validate_pipeline
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict

# Paths
TRUTH_PATH = Path("data/true_data/ground_truth_merged.csv")
PIPELINE_OUTPUT = Path("outputs/direct_holdings_report.csv")


def load_ground_truth() -> pd.DataFrame:
    """
    Load ground truth data from ground_truth_merged.csv.

    Returns:
        DataFrame with normalized columns: [isin, truth_qty, truth_value_eur]
    """
    if not TRUTH_PATH.exists():
        print(f"ERROR: Ground Truth file not found at {TRUTH_PATH}")
        sys.exit(1)

    df = pd.read_csv(TRUTH_PATH)

    # Normalize columns
    # Expected inputs: ISIN, Name, TR_Ticker, Yahoo_Ticker, Asset_Class, Provider, Quantity, Value_EUR
    df = df[["ISIN", "Quantity", "Value_EUR", "Name"]].copy()
    df.columns = ["isin", "truth_qty", "truth_value_eur", "truth_name"]

    return df


def load_pipeline_output() -> pd.DataFrame:
    """
    Load pipeline output from direct_holdings_report.csv.

    Returns:
        DataFrame with normalized columns: [isin, pipe_qty, pipe_value_eur]
    """
    if not PIPELINE_OUTPUT.exists():
        print(f"ERROR: Pipeline output not found at {PIPELINE_OUTPUT}")
        print("Run the pipeline first: python -m scripts.run_pipeline")
        sys.exit(1)

    df = pd.read_csv(PIPELINE_OUTPUT)

    # Expected inputs: isin, name, quantity, market_value...
    df = df[["isin", "quantity", "market_value", "name"]].copy()
    df.columns = ["isin", "pipe_qty", "pipe_value_eur", "pipe_name"]

    return df


def compare_positions(truth: pd.DataFrame, pipeline: pd.DataFrame) -> pd.DataFrame:
    """
    Compare positions matching on ISIN.
    """
    # Merge on ISIN
    merged = pd.merge(truth, pipeline, on="isin", how="outer")

    # Fill NAs
    merged["truth_qty"] = merged["truth_qty"].fillna(0.0)
    merged["pipe_qty"] = merged["pipe_qty"].fillna(0.0)
    merged["truth_value_eur"] = merged["truth_value_eur"].fillna(0.0)
    merged["pipe_value_eur"] = merged["pipe_value_eur"].fillna(0.0)

    # Name fallback
    merged["name"] = merged["truth_name"].fillna(merged["pipe_name"])

    # Calculate Diffs
    merged["qty_diff"] = merged["pipe_qty"] - merged["truth_qty"]
    merged["value_diff"] = merged["pipe_value_eur"] - merged["truth_value_eur"]

    # Percentage Diff (handle div by zero)
    merged["value_pct_diff"] = merged.apply(
        lambda x: (x["value_diff"] / x["truth_value_eur"] * 100)
        if x["truth_value_eur"] > 0
        else 0.0,
        axis=1,
    )

    # Status Logic
    def determine_status(row):
        # 1. Critical: Quantity Mismatch (Allow very small float tolerance)
        if abs(row["qty_diff"]) > 0.001:
            if row["truth_qty"] == 0:
                return "EXTRA_IN_PIPELINE"
            if row["pipe_qty"] == 0:
                return "MISSING_IN_PIPELINE"
            return "QTY_MISMATCH"

        # 2. Warning: Value Mismatch (>5%)
        if abs(row["value_pct_diff"]) > 5.0:
            return "VALUE_DRIFT"

        return "OK"

    merged["status"] = merged.apply(determine_status, axis=1)

    return merged


def print_report(df: pd.DataFrame):
    """Print formatted CLI report."""
    print("=" * 100)
    print("PIPELINE VALIDATION REPORT (Direct Holdings)")
    print(f"Truth Source: {TRUTH_PATH}")
    print("=" * 100)

    # Summary Counts
    print("\n## STATUS SUMMARY")
    counts = df["status"].value_counts()
    for status, count in counts.items():
        icon = {
            "OK": "✅",
            "VALUE_DRIFT": "⚠️",
            "QTY_MISMATCH": "❌",
            "MISSING_IN_PIPELINE": "🚫",
            "EXTRA_IN_PIPELINE": "➕",
        }.get(status, "❓")
        print(f"{icon} {status}: {count}")

    # Failures (Qty)
    failures = df[
        df["status"].isin(
            ["QTY_MISMATCH", "MISSING_IN_PIPELINE", "EXTRA_IN_PIPELINE", "QTY_MISMATCH"]
        )
    ]
    if not failures.empty:
        print("\n## ❌ CRITICAL FAILURES (Quantity Mismatch)")
        print(
            f"{'ISIN':<14} {'Name':<30} {'Truth Qty':>12} {'Pipe Qty':>12} {'Diff':>12}"
        )
        print("-" * 85)
        for _, row in failures.iterrows():
            print(
                f"{row['isin']:<14} {str(row['name'])[:28]:<30} {row['truth_qty']:>12.4f} {row['pipe_qty']:>12.4f} {row['qty_diff']:>12.4f}"
            )

    # Warnings (Value)
    warnings = df[df["status"] == "VALUE_DRIFT"]
    if not warnings.empty:
        print("\n## ⚠️ WARNINGS (Value Drift > 5%)")
        print(f"{'ISIN':<14} {'Name':<30} {'Truth €':>12} {'Pipe €':>12} {'Diff %':>8}")
        print("-" * 85)
        for _, row in warnings.iterrows():
            print(
                f"{row['isin']:<14} {str(row['name'])[:28]:<30} {row['truth_value_eur']:>12.2f} {row['pipe_value_eur']:>12.2f} {row['value_pct_diff']:>8.1f}%"
            )

    print("\n" + "=" * 100)


def main():
    print("Loading Data...")
    truth = load_ground_truth()
    pipeline = load_pipeline_output()

    print("Comparing Positions...")
    results = compare_positions(truth, pipeline)

    print_report(results)

    # Exit Code Logic
    # Fail only on Quantity issues
    critical_errors = len(
        results[
            results["status"].isin(
                ["QTY_MISMATCH", "MISSING_IN_PIPELINE", "EXTRA_IN_PIPELINE"]
            )
        ]
    )

    if critical_errors > 0:
        print(
            f"\n❌ VALIDATION FAILED: {critical_errors} critical quantity mismatches found."
        )
        sys.exit(1)

    print("\n✅ VALIDATION PASSED (Quantities Match)")
    sys.exit(0)


if __name__ == "__main__":
    main()
