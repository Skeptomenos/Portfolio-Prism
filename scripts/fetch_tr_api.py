#!/usr/bin/env python3
"""
Fetch portfolio from Trade Republic via pytr API.

Usage:
    python scripts/fetch_tr_api.py              # Normal fetch
    python scripts/fetch_tr_api.py --reconfigure  # Update credentials in .env

First run: Prompts for phone number and PIN, saves to .env
Subsequent runs: Uses saved credentials, may need 4-digit code from TR app

Output CSV format (calculated_holdings.csv):
    ISIN,Quantity,AvgCost,CurrentPrice,NetValue,TR_Name

    - ISIN: 12-character security identifier
    - Quantity: Number of shares/units held
    - AvgCost: Average purchase price from TR (for P/L calculation)
    - CurrentPrice: Derived from NetValue/Quantity (TR's real-time price)
    - NetValue: Current market value from TR (price * quantity)
    - TR_Name: Security name from Trade Republic (used as fallback if not in universe)

Note on data sources:
    - pytr v0.4.2 outputs: Name;ISIN;quantity;avgCost;netValue (5 columns)
    - pytr fetches real-time prices from TR's ticker API internally
    - We derive CurrentPrice = NetValue / Quantity
    - TR_Name is prefixed to avoid column collision with asset_universe.csv
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
HOLDINGS_FILE = PROJECT_ROOT / "data" / "working" / "calculated_holdings.csv"
BACKUP_DIR = PROJECT_ROOT / "data" / "working"
PYTR_COOKIES_DIR = Path.home() / ".pytr" / "cookies"
PYTR_CREDENTIALS_FILE = Path.home() / ".pytr" / "credentials"


def display_privacy_notice():
    """Show privacy notice before collecting credentials."""
    print()
    print("=" * 66)
    print("  TRADE REPUBLIC CREDENTIALS")
    print("=" * 66)
    print("  Your phone number and PIN will be stored in .env")
    print("  This file is LOCAL ONLY and listed in .gitignore")
    print("  Your credentials are NEVER uploaded or shared with anyone.")
    print("=" * 66)
    print()


def load_env_file() -> dict:
    """Load existing .env file into a dict."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip()
    return env_vars


def save_env_file(env_vars: dict):
    """Save env vars back to .env file, preserving comments."""
    lines = []
    existing_keys = set()

    # Read existing file to preserve comments and structure
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.split("=")[0].strip()
                    if key in env_vars:
                        lines.append(f"{key}={env_vars[key]}\n")
                        existing_keys.add(key)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)

    # Add any new keys that weren't in the file
    for key, value in env_vars.items():
        if key not in existing_keys:
            lines.append(f"{key}={value}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


from typing import Optional, Tuple


def load_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load TR_PHONE_NO and TR_PIN from .env."""
    env_vars = load_env_file()
    phone = env_vars.get("TR_PHONE_NO", "").strip()
    pin = env_vars.get("TR_PIN", "").strip()

    # Return None if empty
    phone = phone if phone else None
    pin = pin if pin else None

    return phone, pin


def prompt_and_save_credentials() -> Tuple[str, str]:
    """Prompt user for credentials and save to .env."""
    display_privacy_notice()

    phone = input(
        "Enter your Trade Republic phone number (e.g., +49123456789): "
    ).strip()
    pin = input("Enter your Trade Republic PIN (4 digits): ").strip()

    if not phone or not pin:
        print("\n[ERROR] Phone number and PIN are required.")
        sys.exit(1)

    # Validate format
    if not re.match(r"^\+\d{10,15}$", phone):
        print(f"\n[WARNING] Phone format may be incorrect: {phone}")
        print("          Expected format: +49123456789")

    if not re.match(r"^\d{4}$", pin):
        print(f"\n[WARNING] PIN should be 4 digits, got: {pin}")

    # Save to .env
    env_vars = load_env_file()
    env_vars["TR_PHONE_NO"] = phone
    env_vars["TR_PIN"] = pin
    save_env_file(env_vars)

    print(f"\n[OK] Credentials saved to {ENV_FILE}")
    return phone, pin


def setup_pytr_credentials(phone: str, pin: str):
    """Create pytr credentials file at ~/.pytr/credentials."""
    PYTR_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PYTR_CREDENTIALS_FILE, "w") as f:
        f.write(f"{phone}\n{pin}\n")


def backup_holdings():
    """Backup existing calculated_holdings.csv with timestamp if it exists.

    Creates: calculated_holdings.YYYY-MM-DD_HHMMSS.csv.bak
    """
    if not HOLDINGS_FILE.exists():
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_name = f"calculated_holdings.{timestamp}.csv.bak"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(HOLDINGS_FILE, backup_path)
    print(f"[OK] Backed up existing holdings to {backup_name}")
    return backup_path


def fetch_portfolio_via_pytr(phone: str, pin: str) -> Optional[Path]:
    """
    Fetch portfolio using pytr CLI.

    Returns path to raw CSV output, or None on failure.
    """
    # Ensure pytr credentials file exists
    setup_pytr_credentials(phone, pin)

    # Ensure cookies directory exists
    PYTR_COOKIES_DIR.mkdir(parents=True, exist_ok=True)

    # Create temp output file
    temp_output = PROJECT_ROOT / "data" / "working" / "temp" / "pytr_raw.csv"
    temp_output.parent.mkdir(parents=True, exist_ok=True)

    print("\n[...] Connecting to Trade Republic...")
    print("      You may be prompted for a 4-digit code from your TR app.\n")

    try:
        # Run pytr portfolio command
        result = subprocess.run(
            ["pytr", "portfolio", "--output", str(temp_output)],
            capture_output=False,  # Let user see prompts
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            return None

        if not temp_output.exists():
            print("\n[ERROR] pytr did not create output file")
            return None

        return temp_output

    except FileNotFoundError:
        print("\n[ERROR] pytr not found. Install it with: pip install pytr")
        return None
    except subprocess.TimeoutExpired:
        print("\n[ERROR] Timeout waiting for Trade Republic response")
        return None
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return None


def convert_and_save_holdings(raw_csv_path: Path) -> tuple[int, float, float]:
    """
    Convert pytr format (semicolon) to pipeline format (comma).
    Preserves all pytr fields including avgCost for P/L calculation.

    pytr CSV format (v0.4.2): Name;ISIN;quantity;avgCost;netValue (5 columns)
    Note: pytr calculates netValue = current_price * quantity internally.
          We derive current_price = netValue / quantity.

    Returns:
        tuple: (position_count, total_cost_basis, total_net_value)
    """
    positions = []
    total_cost_basis = 0.0
    total_net_value = 0.0

    with open(raw_csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Skip header, parse data
    # pytr format (v0.4.2): Name;ISIN;quantity;avgCost;netValue
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        parts = line.split(";")
        if len(parts) >= 5:
            # pytr v0.4.2 format: Name;ISIN;quantity;avgCost;netValue
            name = parts[0].strip()
            isin = parts[1].strip()
            quantity = parts[2].strip()
            avg_cost = parts[3].strip()
            net_value = parts[4].strip()

            # Derive current_price from netValue / quantity
            # This is the price pytr fetched from TR's real-time ticker
            current_price = ""
            try:
                qty = float(quantity.replace(",", ".")) if quantity else 0.0
                value = float(net_value.replace(",", ".")) if net_value else 0.0
                if qty > 0:
                    current_price = f"{value / qty:.4f}"
            except (ValueError, TypeError):
                pass

            # Validate ISIN format
            if re.match(r"^[A-Z]{2}[A-Z0-9]{10}$", isin):
                positions.append(
                    {
                        "isin": isin,
                        "quantity": quantity,
                        "avg_cost": avg_cost,
                        "current_price": current_price,
                        "net_value": net_value,
                        "name": name,
                    }
                )

                # Calculate totals for summary
                try:
                    qty = float(quantity.replace(",", ".")) if quantity else 0.0
                    cost = float(avg_cost.replace(",", ".")) if avg_cost else 0.0
                    value = float(net_value.replace(",", ".")) if net_value else 0.0
                    total_cost_basis += qty * cost
                    total_net_value += value
                except (ValueError, TypeError):
                    pass  # Skip invalid numbers for totals

        elif len(parts) >= 3:
            # Fallback: minimal format (backward compatibility with old pytr versions)
            name = parts[0].strip() if parts[0] else ""
            isin = parts[1].strip()
            quantity = parts[2].strip()

            if re.match(r"^[A-Z]{2}[A-Z0-9]{10}$", isin):
                positions.append(
                    {
                        "isin": isin,
                        "quantity": quantity,
                        "avg_cost": "",
                        "current_price": "",
                        "net_value": "",
                        "name": name,
                    }
                )

    if not positions:
        print("\n[ERROR] No valid positions found in pytr output")
        return 0, 0.0, 0.0

    # Write to calculated_holdings.csv with all fields
    # Format: ISIN,Quantity,AvgCost,CurrentPrice,NetValue,TR_Name
    # Note: TR_Name (not Name) to avoid column collision with asset_universe.csv
    with open(HOLDINGS_FILE, "w", encoding="utf-8") as f:
        f.write("ISIN,Quantity,AvgCost,CurrentPrice,NetValue,TR_Name\n")
        for pos in positions:
            # Escape commas in name field by quoting
            name = pos["name"].replace('"', '""')  # Escape quotes
            if "," in name or '"' in name:
                name = f'"{name}"'
            f.write(
                f"{pos['isin']},{pos['quantity']},{pos['avg_cost']},"
                f"{pos['current_price']},{pos['net_value']},{name}\n"
            )

    return len(positions), total_cost_basis, total_net_value


def display_fallback_message(error: str = ""):
    """Display helpful message when pytr fails."""
    print()
    print("=" * 50)
    print(f"  pytr failed{': ' + error if error else ''}")
    print("=" * 50)
    print()
    print("  Alternative: Use PDF export instead")
    print("  1. Download 'Kontoauszug' PDF from Trade Republic app")
    print("  2. Place in data/inputs/portfolio/")
    print("  3. Run: bash run.sh (select PDF option)")
    print()


def main():
    """Main entry point."""
    # Check for --reconfigure flag
    reconfigure = "--reconfigure" in sys.argv

    # Load or prompt credentials
    phone, pin = load_credentials()

    if reconfigure or not phone or not pin:
        if reconfigure:
            print("\n[INFO] Reconfiguring Trade Republic credentials...")
        phone, pin = prompt_and_save_credentials()

    print(f"\n[INFO] Using phone: {phone[:6]}{'*' * (len(phone) - 6)}")

    # Backup existing holdings
    backup_holdings()

    # Fetch portfolio via pytr
    raw_csv = fetch_portfolio_via_pytr(phone, pin)

    if not raw_csv:
        display_fallback_message()
        sys.exit(1)

    # Convert and save
    count, total_cost, total_value = convert_and_save_holdings(raw_csv)

    if count == 0:
        display_fallback_message("No positions parsed")
        sys.exit(1)

    # Display summary with P/L information
    print(f"\n[OK] Fetched {count} positions from Trade Republic")

    if total_value > 0:
        print(f"     Current Value:  EUR {total_value:>12,.2f}")

        if total_cost > 0:
            unrealized_pl = total_value - total_cost
            unrealized_pl_pct = ((total_value / total_cost) - 1) * 100

            print(f"     Cost Basis:     EUR {total_cost:>12,.2f}")
            pl_sign = "+" if unrealized_pl >= 0 else ""
            print(
                f"     Unrealized P/L: EUR {pl_sign}{unrealized_pl:>11,.2f} "
                f"({pl_sign}{unrealized_pl_pct:.2f}%)"
            )

    print(f"     Saved to: {HOLDINGS_FILE.relative_to(PROJECT_ROOT)}")

    # Cleanup temp file
    try:
        raw_csv.unlink()
    except Exception:
        pass


if __name__ == "__main__":
    main()
