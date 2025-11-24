# Implementation Plan: Technical Debt Resolution (Updated)

## Goal
Eliminate all 4 known technical debt items to achieve a fully modernized, maintainable codebase.

---

## Phase 1: Delete Legacy Modules & Database Code

### Priority: High (Blocker)
**Time:** 30 minutes

### Issue Analysis
- `src/data/manager.py` loads positions from SQLite DB (deprecated)
- `src/data/database.py` provides DB utilities (also deprecated)
- Both are imported but **unused** in current CSV workflow

**Current Imports of manager.py:**
- `src/core/reporting.py` (line 8) - unused
- `src/core/aggregation.py` (line 10) - unused
- `debug/generate_inputs.py` (line 8) - unused

### Proposed Changes

#### [MODIFY] [aggregation.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/core/aggregation.py)
```python
# REMOVE (Line 10)
from src.data.manager import load_positions_from_db
```

#### [MODIFY] [reporting.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/core/reporting.py)
```python
# REMOVE (Line 8)
from src.data.manager import load_positions_from_db
```

#### [MODIFY] [generate_inputs.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/debug/generate_inputs.py)
```python
# REMOVE (Line 8)
from src.data.manager import load_positions_from_db
```

#### [DELETE] src/data/manager.py
#### [DELETE] src/data/database.py

#### [RENAME] scripts/setup_db.py → scripts/setup_db_legacy.py
Add deprecation warning at top of file.

---

## Phase 1.5: Data Migration (One-Time)

### Priority: High (Data Preservation)
**Time:** 30 minutes

### Purpose
Preserve existing user data in `portfolio.db` before removing SQLite workflow.

### Proposed Changes

#### [NEW] [scripts/migrate_db_to_csv.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/scripts/migrate_db_to_csv.py)

```python
#!/usr/bin/env python3
"""
One-time migration: portfolio.db → portfolio_holdings.csv
Run this before deleting manager.py if you have existing DB data.
"""
import sqlite3
import pandas as pd
from pathlib import Path
import shutil

DB_PATH = Path("data/working/database/portfolio.db")
CSV_PATH = Path("data/true_data/portfolio_holdings.csv")

def migrate():
    if not DB_PATH.exists():
        print("✓ No portfolio.db found - no migration needed")
        return
        
    if CSV_PATH.exists():
        print("⚠ portfolio_holdings.csv already exists")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            return
    
    print("Migrating positions from SQLite to CSV...")
    
    # Load from DB
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT ISIN, total_quantity FROM positions", conn)
    conn.close()
    
    # Rename columns to match CSV schema
    df.columns = ['ISIN', 'Quantity']
    
    # Save to CSV
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    
    # Backup DB
    backup_path = DB_PATH.with_suffix('.db.backup')
    shutil.copy(DB_PATH, backup_path)
    
    print(f"✓ Migrated {len(df)} positions to {CSV_PATH}")
    print(f"✓ Backed up DB to {backup_path}")

if __name__ == "__main__":
    migrate()
```

**Usage:**
```bash
python scripts/migrate_db_to_csv.py
```

---

## Phase 2: Reconnect PDF Parser to CSV Workflow

### Priority: High
**Time:** 90 minutes

### Current vs Target Architecture

**Current (Broken):**
```
PDFs → [setup_db.py] → SQLite DB → [DEAD END]
```

**Target:**
```
PDFs → [parse_pdfs_to_csv.py] → portfolio_holdings.csv → [state_manager] → Pipeline
```

### Proposed Changes

#### [NEW] [scripts/parse_pdfs_to_csv.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/scripts/parse_pdfs_to_csv.py)

```python
#!/usr/bin/env python3
"""
Parse Trade Republic PDFs and update portfolio_holdings.csv
"""
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

from src.pdf_parser.parser import main as run_pdf_parser
from src.core.position_keeper import calculate_positions
from src.pdf_parser.utils import parse_description

PDF_INPUT_DIR = "data/inputs/portfolio"
CSV_PATH = Path("data/true_data/portfolio_holdings.csv")

def parse_pdfs_to_csv():
    """Parse PDFs and update CSV with positions."""
    
    # Backup existing CSV
    if CSV_PATH.exists():
        backup = CSV_PATH.with_suffix(f'.csv.backup.{datetime.now():%Y%m%d_%H%M%S}')
        shutil.copy(CSV_PATH, backup)
        print(f"✓ Backed up CSV to {backup}")
    
    # Parse PDFs (uses existing parser)
    sys.argv = ["parser.py", "--input_folder", PDF_INPUT_DIR]
    trades_df = run_pdf_parser()  # Returns trades DataFrame
    
    if trades_df.empty:
        print("No trades found in PDFs")
        return
    
    # Calculate positions
    positions_df = calculate_positions(trades_df)
    
    # Map to CSV schema (ISIN, Quantity)
    csv_df = positions_df[['ISIN', 'total_quantity']].copy()
    csv_df.columns = ['ISIN', 'Quantity']
    
    # Save
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    csv_df.to_csv(CSV_PATH, index=False)
    
    print(f"✓ Saved {len(csv_df)} positions to {CSV_PATH}")

if __name__ == "__main__":
    parse_pdfs_to_csv()
```

#### [MODIFY] [run.sh](file:///Users/davidhelmus/Repos/portfolio-master/POC/run.sh)

```bash
# OLD
python scripts/setup_db.py

# NEW
python scripts/parse_pdfs_to_csv.py
```

---

## Phase 3: Automate Ticker Management

### Priority: Medium
**Time:** 30 minutes

### Current Status
`scripts/sync_ticker_map.py` **already exists** and uses correct path (`config/asset_universe.csv`).

### Enhancement: Add CLI Flags

#### [MODIFY] [scripts/sync_ticker_map.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/scripts/sync_ticker_map.py)

Add argument parsing:

```python
import argparse

def validate_map():
    """Check for duplicates and missing tickers."""
    with open(TICKER_MAP_PATH, 'r') as f:
        ticker_map = json.load(f)
    
    # Check for duplicate ISINs
    duplicates = [k for k, v in ticker_map.items() if list(ticker_map.values()).count(v) > 1]
    if duplicates:
        print(f"⚠ Duplicates found: {duplicates}")
    else:
        print("✓ No duplicates")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild', action='store_true', help='Rebuild from asset_universe.csv')
    parser.add_argument('--validate', action='store_true', help='Validate existing map')
    args = parser.parse_args()
    
    if args.validate:
        validate_map()
    else:
        sync_map()

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Rebuild from asset_universe.csv
python scripts/sync_ticker_map.py --rebuild

# Validate
python scripts/sync_ticker_map.py --validate
```

---

## Phase 4: Asset Management CLI

### Priority: Medium
**Time:** 100 minutes

### Proposed Changes

#### [NEW] [scripts/manage_assets.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/scripts/manage_assets.py)

```python
#!/usr/bin/env python3
"""Asset Universe Management CLI"""
import argparse
import pandas as pd
from pathlib import Path
import subprocess

UNIVERSE_PATH = Path("config/asset_universe.csv")

def add_asset(isin, ticker, name, provider):
    """Add new asset to universe."""
    df = pd.read_csv(UNIVERSE_PATH)
    
    # Validate
    if isin in df['ISIN'].values:
        print(f"⚠ Asset {isin} already exists")
        return
    
    # Append
    new_row = pd.DataFrame([{
        'ISIN': isin,
        'Name': name,
        'Yahoo_Ticker': ticker,
        'Provider': provider
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Save
    df.to_csv(UNIVERSE_PATH, index=False)
    print(f"✓ Added {name} ({isin})")
    
    # Auto-sync ticker map
    subprocess.run(['python', 'scripts/sync_ticker_map.py'])

def list_assets():
    """Display all assets."""
    df = pd.read_csv(UNIVERSE_PATH)
    print(df.to_string())

def search_assets(query):
    """Search by ISIN or ticker."""
    df = pd.read_csv(UNIVERSE_PATH)
    mask = df['ISIN'].str.contains(query, case=False) | df['Yahoo_Ticker'].str.contains(query, case=False)
    print(df[mask].to_string())

def validate_universe():
    """Check for duplicates and issues."""
    df = pd.read_csv(UNIVERSE_PATH)
    
    # Duplicate ISINs
    dups = df[df.duplicated('ISIN', keep=False)]
    if not dups.empty:
        print(f"⚠ Duplicate ISINs:\n{dups}")
    
    # Missing tickers
    missing = df[df['Yahoo_Ticker'].isna() | (df['Yahoo_Ticker'] == '-')]
    if not missing.empty:
        print(f"⚠ Missing tickers:\n{missing[['ISIN', 'Name']]}")
    
    if dups.empty and missing.empty:
        print("✓ Universe is valid")

def main():
    parser = argparse.ArgumentParser(description='Manage Asset Universe')
    subparsers = parser.add_subparsers(dest='command')
    
    # Add command
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--isin', required=True)
    add_parser.add_argument('--ticker', required=True)
    add_parser.add_argument('--name', required=True)
    add_parser.add_argument('--provider', default='Stock')
    
    # List command
    subparsers.add_parser('list')
    
    # Search command
    search_parser = subparsers.add_parser('search')
    search_parser.add_argument('query')
    
    # Validate command
    subparsers.add_parser('validate')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_asset(args.isin, args.ticker, args.name, args.provider)
    elif args.command == 'list':
        list_assets()
    elif args.command == 'search':
        search_assets(args.query)
    elif args.command == 'validate':
        validate_universe()

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Add asset
python scripts/manage_assets.py add --isin US0378331005 --ticker AAPL --name "Apple Inc."

# List all
python scripts/manage_assets.py list

# Search
python scripts/manage_assets.py search AAPL

# Validate
python scripts/manage_assets.py validate
```

---

## Verification Plan

### Phase 1: Legacy Cleanup
```bash
# Remove imports, delete files
pytest tests/ -v
python scripts/run_pipeline.py
```
**Expected:** No errors, pipeline uses CSV workflow.

### Phase 1.5: Migration
```bash
python scripts/migrate_db_to_csv.py
cat data/true_data/portfolio_holdings.csv
```
**Expected:** Existing data preserved in CSV.

### Phase 2: PDF Parser
```bash
python scripts/parse_pdfs_to_csv.py
python scripts/run_pipeline.py
```
**Expected:** CSV updated, pipeline runs successfully.

### Phase 3: Ticker Sync
```bash
python scripts/sync_ticker_map.py --validate
```
**Expected:** No duplicates, map synced.

### Phase 4: Asset CLI
```bash
python scripts/manage_assets.py validate
python scripts/manage_assets.py add --isin TEST123 --ticker TST --name "Test"
```
**Expected:** Asset added, ticker_map auto-synced.

---

## Time Estimates

| Phase | Tasks | Time |
|-------|-------|------|
| 1 | Remove imports, delete files, rename setup_db | 30 min |
| 1.5 | Create & run migration script | 30 min |
| 2 | Create parse_pdfs_to_csv.py, update run.sh, test | 90 min |
| 3 | Add flags to sync_ticker_map.py | 30 min |
| 4 | Create manage_assets.py with all commands | 100 min |
| **Total** | | **~4.5 hours** |

---

## Rollback Strategy

### If Phase 2 Fails
1. Restore CSV from backup (`*.backup.*`)
2. Revert `run.sh` to use `setup_db_legacy.py`
3. Keep using CSV workflow until parser fixed

### If Data Lost
1. Use migration backup: `portfolio.db.backup`
2. Re-run migration script

---

## Success Criteria

- ✅ `src/data/manager.py` and `database.py` deleted
- ✅ Existing data migrated from SQLite to CSV
- ✅ PDFs parse directly to `portfolio_holdings.csv`
- ✅ `ticker_map.json` can be validated & rebuilt
- ✅ Assets managed via CLI (no manual CSV editing)
- ✅ All tests passing
- ✅ Backups created before destructive operations

---

## Post-Implementation

1. Update `CHANGELOG.md`: Document all 4 resolutions
2. Update `DECISION_LOG.md`: CSV-first architecture decision
3. Update `README.md`: New workflows and CLI usage
4. Commit: "Resolve technical debt: PDF parser, legacy cleanup, ticker automation, asset CLI"
