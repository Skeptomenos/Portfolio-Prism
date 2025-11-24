# Phase 1.5: Data Migration Plan

## Current State Analysis

**SQLite Database:**
- Location: `data/working/database/portfolio.db` (564 KB)
- Last modified: Nov 24 19:43
- Contains: 21 positions

**Database Schema:**
```sql
CREATE TABLE positions (
  ISIN TEXT,
  name TEXT,
  total_quantity REAL,
  average_purchase_price REAL,
  asset_type TEXT
)
```

**CSV File:**
- Location: `data/true_data/portfolio_holdings.csv` (577 bytes)
- Last modified: Nov 24 19:59
- Contains: Already has data (schema: `ISIN,Quantity`)

**Status:** ⚠️ **CSV already exists** - Migration needs merge strategy, not simple copy

---

## Migration Strategy

### Decision Points

1. **CSV already exists** → Need merge/overwrite strategy
2. **DB has 21 positions** → Meaningful data to preserve
3. **CSV schema** → Simple (`ISIN,Quantity`) vs DB (`ISIN,name,total_quantity,average_purchase_price,asset_type`)

### Recommended Approach: **Smart Merge**

Compare DB positions vs CSV positions:
- If DB is newer → Update CSV with DB data
- If CSV is newer → Keep CSV, skip migration
- **Ask user** which is authoritative

---

## Migration Script Design

### [NEW] scripts/migrate_db_to_csv.py

```python
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
    
    print(f"CSV File: {'✓ Found' if csv_exists else '✗ Not found'}")
    if csv_exists:
        csv_stat = CSV_PATH.stat()
        print(f"  Size: {csv_stat.st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(csv_stat.st_mtime):%Y-%m-%d %H:%M}")
    
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
    db_df = load_db_positions()
    print(f"\n📊 Found {len(db_df)} positions in database")
    
    if not csv_exists:
        print("→ CSV doesn't exist, creating from DB...")
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        db_df.to_csv(CSV_PATH, index=False)
        print(f"✓ Created {CSV_PATH}")
    
    else:
        # CSV exists - merge strategy
        csv_df = pd.read_csv(CSV_PATH)
        print(f"📊 Found {len(csv_df)} positions in CSV")
        
        if mode == 'skip':
            print("→ Skipping migration (keeping CSV)")
            return
        
        elif mode == 'overwrite':
            # Backup CSV
            backup_path = CSV_PATH.with_suffix(f'.csv.backup.{datetime.now():%Y%m%d_%H%M%S}')
            shutil.copy(CSV_PATH, backup_path)
            print(f"📦 Backed up CSV to {backup_path}")
            
            # Overwrite
            db_df.to_csv(CSV_PATH, index=False)
            print(f"✓ Overwrote CSV with DB data")
        
        else:  # merge
            # Merge: DB takes precedence for common ISINs
            merged_df = pd.concat([csv_df, db_df]).drop_duplicates(subset=['ISIN'], keep='last')
            
            # Backup CSV
            backup_path = CSV_PATH.with_suffix(f'.csv.backup.{datetime.now():%Y%m%d_%H%M%S}')
            shutil.copy(CSV_PATH, backup_path)
            print(f"📦 Backed up CSV to {backup_path}")
            
            # Save merged
            merged_df.to_csv(CSV_PATH, index=False)
            print(f"✓ Merged: {len(merged_df)} total positions")
    
    # Backup DB
    backup_db = DB_PATH.with_suffix('.db.backup')
    shutil.copy(DB_PATH, backup_db)
    print(f"📦 Backed up DB to {backup_db}")
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Migrate portfolio.db to CSV')
    parser.add_argument('--mode', choices=['merge', 'overwrite', 'skip', 'status'],
                       default='status', help='Migration mode')
    args = parser.parse_args()
    
    if args.mode == 'status':
        check_status()
    else:
        migrate(mode=args.mode)
```

---

## Execution Plan

### Step 1: Check Status
```bash
python scripts/migrate_db_to_csv.py --mode status
```

**Expected Output:**
```
=== Migration Status ===
SQLite DB: ✓ Found
  Size: 564.0 KB
  Modified: 2025-11-24 19:43
CSV File: ✓ Found
  Size: 577 bytes
  Modified: 2025-11-24 19:59
```

### Step 2: Decide Mode

**Options:**
1. `--mode merge` (recommended) - Combine DB + CSV, DB wins on conflicts
2. `--mode overwrite` - Replace CSV entirely with DB
3. `--mode skip` - Keep CSV unchanged (if it's newer/correct)

### Step 3: Run Migration
```bash
python scripts/migrate_db_to_csv.py --mode merge
```

### Step 4: Verify
```bash
# Check CSV updated
wc -l data/true_data/portfolio_holdings.csv

# Check backups created
ls -lh data/working/database/*.backup*
ls -lh data/true_data/*.backup*
```

---

## Verification Checklist

- [ ] Migration script created
- [ ] Status check shows both files
- [ ] User decides merge mode
- [ ] Migration runs without errors
- [ ] CSV contains expected positions
- [ ] DB backed up to `.db.backup`
- [ ] Previous CSV backed up (if overwritten)
- [ ] Test pipeline with new CSV

---

## Rollback Plan

If migration fails or CSV is corrupted:

```bash
# Restore CSV from backup
cp data/true_data/portfolio_holdings.csv.backup.* data/true_data/portfolio_holdings.csv

# DB is still intact at data/working/database/portfolio.db
```

---

## Time Estimate

- Script creation: 15 min
- Testing: 10 min
- User decision: 5 min
- **Total: ~30 min**

---

## Risks & Mitigation

**Risk 1:** CSV gets corrupted
- **Mitigation:** Automatic backup before any writes

**Risk 2:** User doesn't know which is correct
- **Mitigation:** Show timestamps and record counts in status

**Risk 3:** Data loss
- **Mitigation:** DB backup created before any changes

---

## Next Steps After Migration

1. Update `run.sh` to NOT call `setup_db_legacy.py`
2. Test full pipeline with migrated CSV
3. Optionally delete `portfolio.db` after confirmation
