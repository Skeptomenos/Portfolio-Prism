#!/usr/bin/env python3
"""
One-time deep cache cleanup script.

Removes polluted entries from enrichment_cache.json:
- Entries with FALLBACK| pattern in key
- Entries with pipe (|) in key
- Entries with invalid/missing ISIN
- Entries where name is "Not Found"

Generates a removal report for review.

Usage:
    python -m scripts.cleanup_cache [--dry-run]
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


# Constants
CACHE_PATH = Path("data/working/cache/enrichment_cache.json")
REPORT_PATH = Path("outputs/cache_cleanup_report.csv")


def is_valid_isin(isin: str) -> bool:
    """
    Validate ISIN format and Luhn checksum.

    ISIN format: 2 letter country code + 9 alphanumeric NSIN + 1 check digit
    """
    if not isin or not isinstance(isin, str):
        return False

    isin = isin.strip().upper()

    # Basic format check
    if len(isin) != 12:
        return False
    if not isin[:2].isalpha():  # Country code
        return False
    if not isin[2:11].isalnum():  # NSIN
        return False
    if not isin[11].isdigit():  # Check digit
        return False

    # Luhn checksum validation
    try:
        # Convert letters to numbers (A=10, B=11, ..., Z=35)
        digits = ""
        for char in isin:
            if char.isdigit():
                digits += char
            else:
                digits += str(ord(char) - ord("A") + 10)

        # Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(digits)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        return total % 10 == 0
    except Exception:
        return False


def load_cache() -> dict:
    """Load the enrichment cache."""
    if not CACHE_PATH.exists():
        print(f"Cache file not found: {CACHE_PATH}")
        return {}

    with open(CACHE_PATH, "r") as f:
        return json.load(f)


def save_cache(cache: dict) -> None:
    """Save the cleaned cache."""
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def analyze_entry(key: str, value: dict) -> tuple[bool, str]:
    """
    Analyze a cache entry and determine if it should be removed.

    Returns:
        (should_remove, reason)
    """
    # Rule 1: FALLBACK pattern
    if key.startswith("FALLBACK|"):
        return True, "fallback_pattern"

    # Rule 2: Contains pipe (composite key)
    if "|" in key:
        return True, "contains_pipe"

    # Rule 3: Key starts with UNRESOLVED
    if key.startswith("UNRESOLVED:"):
        return True, "unresolved_key"

    # Rule 4: Invalid or missing ISIN in value
    isin = value.get("isin", "")
    if isin in ("N/A", None, "", "null"):
        return True, "isin_na"

    # Rule 5: ISIN format invalid
    if isin and not is_valid_isin(isin):
        return True, "isin_format_invalid"

    # Rule 6: Name is "Not Found"
    if value.get("name") == "Not Found":
        return True, "name_not_found"

    # Rule 7: Key itself looks like a composite (internal placeholders)
    if key.startswith("_") or "NON_EQUITY" in key or "CASH" in key.upper():
        return True, "internal_placeholder"

    return False, "keep"


def cleanup_cache(dry_run: bool = False) -> tuple[int, int, list[dict]]:
    """
    Perform cache cleanup.

    Args:
        dry_run: If True, don't actually modify the cache

    Returns:
        (removed_count, kept_count, removal_details)
    """
    cache = load_cache()
    initial_count = len(cache)

    removed = []
    kept = []

    for key, value in list(cache.items()):
        should_remove, reason = analyze_entry(key, value)

        if should_remove:
            removed.append(
                {
                    "key": key,
                    "reason": reason,
                    "isin": value.get("isin", ""),
                    "name": value.get("name", ""),
                    "sector": value.get("sector", ""),
                }
            )
            if not dry_run:
                del cache[key]
        else:
            kept.append(key)

    # Save cleaned cache
    if not dry_run and removed:
        save_cache(cache)

    return len(removed), len(kept), removed


def generate_report(removed: list[dict]) -> None:
    """Generate a CSV report of removed entries."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(removed)
    df.to_csv(REPORT_PATH, index=False)
    print(f"Removal report saved to: {REPORT_PATH}")


def print_summary(removed: list[dict], kept_count: int) -> None:
    """Print cleanup summary."""
    print("\n" + "=" * 60)
    print("CACHE CLEANUP SUMMARY")
    print("=" * 60)

    total = len(removed) + kept_count
    print(f"\nTotal entries processed: {total}")
    print(f"Removed: {len(removed)} ({100 * len(removed) / total:.1f}%)")
    print(f"Kept: {kept_count} ({100 * kept_count / total:.1f}%)")

    # Breakdown by reason
    if removed:
        print("\nRemoval reasons:")
        reasons = {}
        for entry in removed:
            reason = entry["reason"]
            reasons[reason] = reasons.get(reason, 0) + 1

        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Clean up polluted enrichment cache")
    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze without modifying the cache"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN MODE - No changes will be made\n")

    print(f"Cache file: {CACHE_PATH}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    removed_count, kept_count, removed = cleanup_cache(dry_run=args.dry_run)

    print_summary(removed, kept_count)

    if removed and not args.dry_run:
        generate_report(removed)
        print(f"\nCache cleaned successfully!")
    elif args.dry_run and removed:
        print(f"\nDry run complete. Run without --dry-run to apply changes.")
        # Still generate report for review
        generate_report(removed)
    else:
        print("\nNo entries to remove.")


if __name__ == "__main__":
    main()
