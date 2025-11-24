#!/usr/bin/env python3
"""
One-time migration: portfolio.db → portfolio_holdings.csv

Safely merge SQLite positions into CSV format.
"""
import sqlite3
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
import argparse

DB_PATH = Path("data/working/database/portfolio.db")
CSV_PATH = Path("data/true_data/portfolio_holdings.csv")

def check_status():
    """Analyze current state."""
    db_exists = DB_PATH.exists()
    csv_exists = CSV_PATH.exists()
    
    print("=== Migration Status ===")
    print(f"SQLite DB: {'✓ Found' if db_exists else '✗ Not found'}")
    if db_exists:
        db_stat = DB_PATH.stat()
        print(f"  Size: {db_stat.st_size / 1024:.1f} KB")
        print(f"  Modified: {datetime.fromtimestamp(db_stat.st_mtime):%Y-%m-%d %H:%M}")
        
        # Count records
        try:
            conn = sqlite3.connect(DB_PATH)
            count = pd.read_sql_query("SELECT COUNT(*) as count FROM positions", conn).iloc[0]['count']
            conn.close()
            print(f"  Records: {count}")
        except Exception as e:
            print(f"  Records: Error - {e}")
    
    print(f"\nCSV File: {'✓ Found' if csv_exists else '✗ Not found'}")
    if csv_exists:
        csv_stat = CSV_PATH.stat()
        print(f"  Size: {csv_stat.st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(csv_stat.st_mtime):%Y-%m-%d %H:%M}")
        
        # Count records
        try:
            df = pd.read_csv(CSV_PATH)
            print(f"  Records: {len(df)}")
        except Exception as e:
            print(f"  Records: Error - {e}")
    
    return db_exists, csv_exists

def load_db_positions():
    """Load positions from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT ISIN, total_quantity FROM positions",
        conn
    )
    conn.close()
    
    # Rename to match CSV schema
    df.columns = ['ISIN', 'Quantity']
    return df

def migrate(mode='merge'):
    """
    Migrate DB to CSV.
    
    Args:
        mode: 'merge' (combine), 'overwrite' (replace CSV), or 'skip' (keep CSV)
    """
    db_exists, csv_exists = check_status()
    
    if not db_exists:
        print("\n✓ No database found - migration not needed")
        return
    
    # Load DB data
    print("\n📊 Loading database positions...")
    db_df = load_db_positions()
    print(f"   Found {len(db_df)} positions in database")
    
    if not csv_exists:
        print("\n→ CSV doesn't exist, creating from DB...")
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        db_df.to_csv(CSV_PATH, index=False)
        print(f"✓ Created {CSV_PATH}")
    
    else:
        # CSV exists - merge strategy
        csv_df = pd.read_csv(CSV_PATH)
        print(f"📊 Found {len(csv_df)} positions in CSV")
        
        if mode == 'skip':
            print("\n→ Skipping migration (keeping CSV)")
            return
        
        elif mode == 'overwrite':
            # Backup CSV
            backup_path = CSV_PATH.with_suffix(f'.csv.backup.{datetime.now():%Y%m%d_%H%M%S}')
            shutil.copy(CSV_PATH, backup_path)
            print(f"\n📦 Backed up CSV to {backup_path.name}")
            
            # Overwrite
            db_df.to_csv(CSV_PATH, index=False)
            print(f"✓ Overwrote CSV with DB data ({len(db_df)} positions)")
        
        else:  # merge
            # Merge: DB takes precedence for common ISINs
            merged_df = pd.concat([csv_df, db_df]).drop_duplicates(subset=['ISIN'], keep='last')
            
            # Backup CSV
            backup_path = CSV_PATH.with_suffix(f'.csv.backup.{datetime.now():%Y%m%d_%H%M%S}')
            shutil.copy(CSV_PATH, backup_path)
            print(f"\n📦 Backed up CSV to {backup_path.name}")
            
            # Save merged
            merged_df.to_csv(CSV_PATH, index=False)
            print(f"✓ Merged: {len(merged_df)} total positions")
            print(f"  (CSV had {len(csv_df)}, DB had {len(db_df)})")
    
    # Backup DB
    backup_db = DB_PATH.with_suffix('.db.backup')
    if not backup_db.exists():
        shutil.copy(DB_PATH, backup_db)
        print(f"📦 Backed up DB to {backup_db.name}")
    else:
        print(f"📦 DB backup already exists: {backup_db.name}")
    
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate portfolio.db to CSV')
    parser.add_argument('--mode', choices=['merge', 'overwrite', 'skip', 'status'],
                       default='status', help='Migration mode')
    args = parser.parse_args()
    
    if args.mode == 'status':
        check_status()
    else:
        migrate(mode=args.mode)
