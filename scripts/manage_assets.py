#!/usr/bin/env python3
"""
Asset Universe Management CLI

Manage config/asset_universe.csv without manual CSV editing.
Provides commands to add, list, search, validate, and remove assets.
"""
import argparse
import pandas as pd
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

UNIVERSE_PATH = Path("config/asset_universe.csv")

def load_universe() -> pd.DataFrame:
    """Load asset universe from CSV"""
    if not UNIVERSE_PATH.exists():
        print(f"❌ Universe file not found: {UNIVERSE_PATH}")
        return pd.DataFrame()
    return pd.read_csv(UNIVERSE_PATH)

def save_universe(df: pd.DataFrame, backup=True):
    """Save universe with optional backup"""
    if backup and UNIVERSE_PATH.exists():
        backup_path = str(UNIVERSE_PATH) + f".backup.{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copy(UNIVERSE_PATH, backup_path)
        print(f"📦 Backed up to {Path(backup_path).name}")
    
    df.to_csv(UNIVERSE_PATH, index=False)

def validate_isin(isin: str) -> bool:
    """Validate ISIN format (2 letters + 10 alphanumeric)"""
    return bool(re.match(r'^[A-Z]{2}[A-Z0-9]{10}$', isin.upper()))

def add_asset(isin, ticker, name, provider='N/A', asset_class='Stock', tr_ticker=None):
    """Add new asset to universe"""
    
    # Normalize ISIN
    isin = isin.upper()
    
    # Validate ISIN
    if not validate_isin(isin):
        print(f"❌ Invalid ISIN format: {isin}")
        print("   Expected: 2 letters + 10 alphanumeric (e.g., US0378331005)")
        return False
    
    # Load universe
    df = load_universe()
    if df.empty:
        return False
    
    # Check duplicates
    if isin in df['ISIN'].values:
        existing = df[df['ISIN'] == isin].iloc[0]
        print(f"❌ Asset already exists: {existing['Name']} ({isin})")
        return False
    
    # Create new row
    new_row = {
        'ISIN': isin,
        'TR_Ticker': tr_ticker or ticker,
        'Yahoo_Ticker': ticker,
        'Name': name,
        'Provider': provider,
        'Asset_Class': asset_class
    }
    
    # Append and sort
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = df.sort_values('ISIN').reset_index(drop=True)
    
    # Save
    save_universe(df, backup=True)
    
    print(f"✅ Added: {name} ({isin})")
    print(f"   Ticker: {ticker}")
    print(f"   Class: {asset_class}")
    
    # Auto-sync ticker map
    print("\n🔄 Auto-syncing ticker map...")
    try:
        import sys
        result = subprocess.run(
            [sys.executable, 'scripts/sync_ticker_map.py', '--mode', 'sync'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Ticker map synced")
        else:
            print("⚠️  Ticker map sync failed (run manually)")
    except Exception as e:
        print(f"⚠️  Could not auto-sync ticker map: {e}")
    
    return True

def list_assets(format='table', filter_class=None):
    """List all assets"""
    
    df = load_universe()
    if df.empty:
        return
    
    if filter_class:
        df = df[df['Asset_Class'] == filter_class]
    
    if format == 'table':
        print(df.to_string(index=False))
    elif format == 'csv':
        print(df.to_csv(index=False))
    elif format == 'json':
        print(df.to_json(orient='records', indent=2))
    
    print(f"\n📊 Total: {len(df)} asset(s)")
    if filter_class:
        print(f"   Filter: {filter_class}")

def search_assets(query, field=None):
    """Search assets by query"""
    
    df = load_universe()
    if df.empty:
        return
    
    # Convert wildcards to regex
    pattern = query.replace('*', '.*')
    
    try:
        if field:
            # Search specific field
            if field not in df.columns:
                print(f"❌ Invalid field: {field}")
                print(f"   Available: {', '.join(df.columns)}")
                return
            mask = df[field].astype(str).str.contains(pattern, case=False, na=False, regex=True)
        else:
            # Search across all columns
            mask = df.apply(
                lambda row: row.astype(str).str.contains(pattern, case=False, regex=True).any(),
                axis=1
            )
        
        results = df[mask]
        
        if results.empty:
            print(f"❌ No results for: {query}")
        else:
            print(results.to_string(index=False))
            print(f"\n📊 Found: {len(results)} asset(s)")
    
    except re.error as e:
        print(f"❌ Invalid search pattern: {e}")

def validate_universe():
    """Comprehensive validation of asset universe"""
    
    print("🔍 Validating asset universe...")
    
    df = load_universe()
    if df.empty:
        return False
    
    issues = []
    warnings = []
    
    # Check 1: Duplicate ISINs
    dups = df[df.duplicated('ISIN', keep=False)]
    if not dups.empty:
        issues.append(f"❌ {len(dups)} duplicate ISINs:")
        for isin in dups['ISIN'].unique():
            issues.append(f"     {isin}")
    
    # Check 2: Invalid ISIN format
    invalid_isins = df[~df['ISIN'].astype(str).str.match(r'^[A-Z]{2}[A-Z0-9]{10}$')]
    if not invalid_isins.empty:
        issues.append(f"❌ {len(invalid_isins)} invalid ISIN formats:")
        for _, row in invalid_isins.head(5).iterrows():
            issues.append(f"     {row['ISIN']} ({row['Name']})")
    
    # Check 3: Missing required fields
    for col in ['ISIN', 'Yahoo_Ticker', 'Name']:
        missing = df[df[col].isna() | (df[col].astype(str).str.strip() == '')]
        if not missing.empty:
            issues.append(f"❌ {len(missing)} rows missing {col}")
    
    # Check 4: Invalid asset class
    valid_classes = {'Stock', 'ETF'}
    invalid = df[~df['Asset_Class'].isin(valid_classes)]
    if not invalid.empty:
        issues.append(f"❌ {len(invalid)} invalid Asset_Class values:")
        for val in invalid['Asset_Class'].unique():
            issues.append(f"     '{val}' (should be 'Stock' or 'ETF')")
    
    # Check 5: Missing tickers (warning only)
    missing_tickers = df[df['Yahoo_Ticker'].isna() | (df['Yahoo_Ticker'] == '-')]
    if not missing_tickers.empty:
        warnings.append(f"⚠️  {len(missing_tickers)} assets without Yahoo ticker")
    
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
        print("✅ Universe is valid!")
        return True
    elif not issues:
        print("\n✅ No critical issues (warnings can be ignored)")
        return True
    else:
        print(f"\n❌ Found {len(issues)} critical issue(s)")
        return False

def remove_asset(isin):
    """Remove asset from universe"""
    
    isin = isin.upper()
    
    df = load_universe()
    if df.empty:
        return False
    
    if isin not in df['ISIN'].values:
        print(f"❌ Asset not found: {isin}")
        return False
    
    # Show what will be removed
    asset = df[df['ISIN'] == isin].iloc[0]
    print(f"⚠️  Removing: {asset['Name']} ({isin})")
    print(f"   Ticker: {asset['Yahoo_Ticker']}")
    print(f"   Class: {asset['Asset_Class']}")
    
    # Confirm
    response = input("\nAre you sure? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return False
    
    # Remove
    df = df[df['ISIN'] != isin]
    save_universe(df, backup=True)
    
    print(f"✅ Removed {isin}")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Manage asset universe',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add asset
  python scripts/manage_assets.py add --isin US0378331005 --ticker AAPL --name "Apple Inc."
  
  # List all assets
  python scripts/manage_assets.py list
  
  # List only ETFs
  python scripts/manage_assets.py list --filter ETF
  
  # Search for iShares funds
  python scripts/manage_assets.py search iShares
  
  # Search by specific field
  python scripts/manage_assets.py search --field Provider iShares
  
  # Validate universe
  python scripts/manage_assets.py validate
  
  # Remove asset
  python scripts/manage_assets.py remove --isin US0378331005
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add new asset')
    add_parser.add_argument('--isin', required=True, help='ISIN code (e.g., US0378331005)')
    add_parser.add_argument('--ticker', required=True, help='Yahoo Finance ticker')
    add_parser.add_argument('--name', required=True, help='Asset name')
    add_parser.add_argument('--provider', default='N/A', help='Provider (default: N/A)')
    add_parser.add_argument('--asset-class', choices=['Stock', 'ETF'], default='Stock', 
                           help='Asset class (default: Stock)')
    add_parser.add_argument('--tr-ticker', help='Trade Republic ticker (defaults to Yahoo ticker)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all assets')
    list_parser.add_argument('--format', choices=['table', 'csv', 'json'], default='table',
                            help='Output format (default: table)')
    list_parser.add_argument('--filter', choices=['Stock', 'ETF'], dest='filter_class',
                            help='Filter by asset class')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search assets')
    search_parser.add_argument('query', help='Search query (supports * wildcard)')
    search_parser.add_argument('--field', choices=['ISIN', 'Name', 'Provider', 'Yahoo_Ticker', 'Asset_Class'],
                               help='Search in specific field only')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate universe')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove asset')
    remove_parser.add_argument('--isin', required=True, help='ISIN of asset to remove')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to functions
    if args.command == 'add':
        add_asset(
            isin=args.isin,
            ticker=args.ticker,
            name=args.name,
            provider=args.provider,
            asset_class=args.asset_class,
            tr_ticker=args.tr_ticker
        )
    elif args.command == 'list':
        list_assets(format=args.format, filter_class=args.filter_class)
    elif args.command == 'search':
        search_assets(query=args.query, field=args.field)
    elif args.command == 'validate':
        validate_universe()
    elif args.command == 'remove':
        remove_asset(isin=args.isin)

if __name__ == "__main__":
    main()
