#!/usr/bin/env python3
"""
One-time migration: portfolio.db -> portfolio_holdings.csv

Safely merge SQLite positions into CSV format.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data/working/database/portfolio.db"
CSV_PATH = PROJECT_ROOT / "data/true_data/portfolio_holdings.csv"


def check_status():
    """Analyze current state."""
    db_exists = DB_PATH.exists()
    csv_exists = CSV_PATH.exists()

    print("=== Migration Status ===")
    status_db = "[OK] Found" if db_exists else "[X] Not found"
    print(f"SQLite DB: {status_db}")
    if db_exists:
        db_stat = DB_PATH.stat()
        print(f"  Path: {DB_PATH}")
        print(f"  Size: {db_stat.st_size / 1024:.1f} KB")
        print(f"  Modified: {datetime.fromtimestamp(db_stat.st_mtime):%Y-%m-%d %H:%M}")

    status_csv = "[OK] Found" if csv_exists else "[X] Not found"
    print(f"CSV File: {status_csv}")
    if csv_exists:
        csv_stat = CSV_PATH.stat()
        print(f"  Path: {CSV_PATH}")
        print(f"  Size: {csv_stat.st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(csv_stat.st_mtime):%Y-%m-%d %H:%M}")

    return db_exists, csv_exists


def load_db_positions():
    """Load positions from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT ISIN, total_quantity FROM positions", conn)
    except Exception as e:
        print(f"Error reading DB: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    # Rename to match CSV schema
    df.columns = ["ISIN", "Quantity"]
    return df


def migrate(mode="merge"):
    """
    Migrate DB to CSV.

    Args:
        mode: 'merge' (combine), 'overwrite' (replace CSV), or 'skip' (keep CSV)
    """
    db_exists, csv_exists = check_status()

    if not db_exists:
        print("\n[OK] No database found - migration not needed")
        return

    # Load DB data
    db_df = load_db_positions()
    if db_df.empty:
        print("\n[WARN] Database is empty or unreadable.")
        return

    print(f"\n[INFO] Found {len(db_df)} positions in database")

    if not csv_exists:
        print("-> CSV does not exist, creating from DB...")
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        db_df.to_csv(CSV_PATH, index=False)
        print(f"[OK] Created {CSV_PATH}")

    else:
        # CSV exists - merge strategy
        try:
            csv_df = pd.read_csv(CSV_PATH)
            print(f"[INFO] Found {len(csv_df)} positions in CSV")
        except Exception as e:
            print(f"[WARN] Error reading existing CSV: {e}")
            csv_df = pd.DataFrame(columns=["ISIN", "Quantity"])

        if mode == "skip":
            print("-> Skipping migration (keeping CSV)")
            return

        elif mode == "overwrite":
            # Backup CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = CSV_PATH.with_suffix(f".csv.backup.{timestamp}")
            shutil.copy(CSV_PATH, backup_path)
            print(f"[BACKUP] Backed up CSV to {backup_path}")

            # Overwrite
            db_df.to_csv(CSV_PATH, index=False)
            print("[OK] Overwrote CSV with DB data")

        else:  # merge
            # Merge: DB takes precedence for common ISINs
            # We concat, then drop duplicates keeping the LAST occurrence.
            # So if we want DB to win, we put DB last.
            merged_df = pd.concat([csv_df, db_df])
            # If duplicates exist in ISIN, keep the one from DB (which is at the bottom)
            merged_df = merged_df.drop_duplicates(subset=["ISIN"], keep="last")

            # Backup CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = CSV_PATH.with_suffix(f".csv.backup.{timestamp}")
            shutil.copy(CSV_PATH, backup_path)
            print(f"[BACKUP] Backed up CSV to {backup_path}")

            # Save merged
            merged_df.to_csv(CSV_PATH, index=False)
            print(f"[OK] Merged: {len(merged_df)} total positions")

    # Backup DB
    backup_db = DB_PATH.with_suffix(".db.backup")
    shutil.copy(DB_PATH, backup_db)
    print(f"[BACKUP] Backed up DB to {backup_db}")
    print("\n[DONE] Migration complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate portfolio.db to CSV")
    parser.add_argument(
        "--mode",
        choices=["merge", "overwrite", "skip", "status"],
        default="status",
        help="Migration mode",
    )
    args = parser.parse_args()

    if args.mode == "status":
        check_status()
    else:
        migrate(mode=args.mode)
