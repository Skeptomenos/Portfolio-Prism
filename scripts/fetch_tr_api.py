#!/usr/bin/env python3
"""
Fetch portfolio from Trade Republic via pytr API.

Usage:
    python scripts/fetch_tr_api.py              # Normal fetch
    python scripts/fetch_tr_api.py --reconfigure  # Update credentials in .env

First run: Prompts for phone number and PIN, saves to .env
Subsequent runs: Uses saved credentials, may need 4-digit code from TR app
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


def convert_and_save_holdings(raw_csv_path: Path) -> int:
    """
    Convert pytr format (semicolon) to pipeline format (comma).
    Extract only ISIN and quantity columns.

    Returns number of positions saved.
    """
    positions = []

    with open(raw_csv_path, "r") as f:
        lines = f.readlines()

    # Skip header, parse data
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # pytr format: name;isin;quantity;...
        parts = line.split(";")
        if len(parts) >= 3:
            isin = parts[1].strip()
            quantity = parts[2].strip()

            # Validate ISIN format
            if re.match(r"^[A-Z]{2}[A-Z0-9]{10}$", isin):
                positions.append((isin, quantity))

    if not positions:
        print("\n[ERROR] No valid positions found in pytr output")
        return 0

    # Write to calculated_holdings.csv
    with open(HOLDINGS_FILE, "w") as f:
        f.write("ISIN,Quantity\n")
        for isin, quantity in positions:
            f.write(f"{isin},{quantity}\n")

    return len(positions)


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
    count = convert_and_save_holdings(raw_csv)

    if count == 0:
        display_fallback_message("No positions parsed")
        sys.exit(1)

    # Calculate total value if available
    try:
        import pandas as pd

        raw_df = pd.read_csv(raw_csv, sep=";")
        if "netValue" in raw_df.columns:
            total_value = raw_df["netValue"].sum()
            print(f"\n[OK] Fetched {count} positions from Trade Republic")
            print(f"     Total value: EUR {total_value:,.2f}")
        else:
            print(f"\n[OK] Fetched {count} positions from Trade Republic")
    except Exception:
        print(f"\n[OK] Fetched {count} positions from Trade Republic")

    print(f"     Saved to: {HOLDINGS_FILE.relative_to(PROJECT_ROOT)}")

    # Cleanup temp file
    try:
        raw_csv.unlink()
    except Exception:
        pass


if __name__ == "__main__":
    main()
