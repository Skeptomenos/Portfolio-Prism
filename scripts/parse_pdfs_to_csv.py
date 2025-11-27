#!/usr/bin/env python3
"""
Parse Trade Republic PDFs and incrementally update portfolio_holdings.csv

This script:
1. Parses PDFs to extract trades
2. Calculates net positions
3. Merges with existing CSV (CSV takes precedence)
4. Backs up before changes

Usage:
    python scripts/parse_pdfs_to_csv.py --mode dry_run   # Preview changes
    python scripts/parse_pdfs_to_csv.py --mode add_new   # Add new positions only (default)
    python scripts/parse_pdfs_to_csv.py --mode merge     # Update quantities (use with caution)
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import argparse

from src.pdf_parser.parser import parse_pdfs_from_folder
from src.core.position_keeper import calculate_positions

PDF_INPUT_DIR = Path("data/inputs/portfolio")
CSV_PATH = Path("data/true_data/portfolio_holdings.csv")

def parse_pdfs_to_positions():
    """Parse PDFs and return positions DataFrame."""
    print("📄 Parsing PDFs from", PDF_INPUT_DIR)
    
    # Parse PDFs (returns trades DataFrame)
    trades_df = parse_pdfs_from_folder(PDF_INPUT_DIR)
    
    if trades_df.empty:
        print("⚠ No trades found in PDFs")
        return pd.DataFrame()
    
    print(f"   Found {len(trades_df)} trades")
    
    # Calculate positions
    positions_df = calculate_positions(trades_df)
    
    # Map to CSV schema (ISIN, Quantity)
    csv_df = positions_df[['ISIN', 'total_quantity']].copy()
    csv_df.columns = ['ISIN', 'Quantity']
    
    print(f"   Calculated {len(csv_df)} positions from trades")
    return csv_df

def update_csv(new_positions_df, mode='add_new'):
    """
    Update CSV with new positions.
    
    Args:
        new_positions_df: Positions from PDFs
        mode: 'add_new' (only add missing ISINs) or 'merge' (update quantities)
    """
    # Backup existing CSV
    if CSV_PATH.exists():
        backup = CSV_PATH.with_suffix(f'.csv.backup.{datetime.now():%Y%m%d_%H%M%S}')
        shutil.copy(CSV_PATH, backup)
        print(f"📦 Backed up CSV to {backup.name}")
        
        existing_df = pd.read_csv(CSV_PATH)
        print(f"📊 Existing CSV: {len(existing_df)} positions")
    else:
        existing_df = pd.DataFrame(columns=['ISIN', 'Quantity'])
        print("📊 No existing CSV, creating new")
    
    if mode == 'add_new':
        # Only add ISINs not in existing CSV
        new_isins = set(new_positions_df['ISIN']) - set(existing_df['ISIN'])
        to_add = new_positions_df[new_positions_df['ISIN'].isin(new_isins)]
        
        if len(to_add) > 0:
            updated_df = pd.concat([existing_df, to_add], ignore_index=True)
            print(f"✅ Added {len(to_add)} new positions:")
            print(to_add.to_string(index=False))
        else:
            updated_df = existing_df
            print("✅ No new positions to add (all ISINs already in CSV)")
    
    else:  # merge
        # Combine, existing CSV wins on conflicts
        combined = pd.concat([new_positions_df, existing_df])
        updated_df = combined.drop_duplicates(subset=['ISIN'], keep='last')
        print(f"✅ Merged: {len(updated_df)} total positions")
        print("⚠ Note: Existing CSV quantities preserved for common ISINs")
    
    # Save
    updated_df.to_csv(CSV_PATH, index=False)
    print(f"💾 Saved to {CSV_PATH}")

def main():
    parser = argparse.ArgumentParser(description='Parse PDFs and update CSV')
    parser.add_argument('--mode', choices=['add_new', 'merge', 'dry_run'],
                       default='add_new',
                       help='Update mode: add_new (default), merge, or dry_run')
    args = parser.parse_args()
    
    # Parse PDFs
    new_positions = parse_pdfs_to_positions()
    
    if new_positions.empty:
        print("\n❌ No positions to update")
        return
    
    if args.mode == 'dry_run':
        print("\n🔍 DRY RUN - Would process these positions:")
        print(new_positions.to_string(index=False))
        
        if CSV_PATH.exists():
            existing_df = pd.read_csv(CSV_PATH)
            new_isins = set(new_positions['ISIN']) - set(existing_df['ISIN'])
            if new_isins:
                print(f"\n📊 Would add {len(new_isins)} new ISINs:")
                print(new_positions[new_positions['ISIN'].isin(new_isins)].to_string(index=False))
            else:
                print("\n✅ All ISINs already exist in CSV")
    else:
        update_csv(new_positions, mode=args.mode)
        print("\n✅ CSV update complete!")

if __name__ == "__main__":
    main()
