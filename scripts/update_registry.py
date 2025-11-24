import json
import os
import pandas as pd
from pathlib import Path

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

REGISTRY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'adapter_registry.json'))

# Map CLI options to Adapter Keys (and keywords for validation)
PROVIDER_OPTIONS = {
    "1": {"key": "ishares", "label": "iShares", "keywords": ["ishares", "blackrock", "ishs"]},
    "2": {"key": "amundi", "label": "Amundi / Lyxor", "keywords": ["amundi", "lyxor", "lyx", "multi units"]},
    "3": {"key": "xtrackers", "label": "Xtrackers (DWS)", "keywords": ["xtrackers", "db x-trackers", "dws", "x(ie)"]},
    "4": {"key": "vaneck", "label": "VanEck", "keywords": ["vaneck"]},
    "5": {"key": "vanguard", "label": "Vanguard", "keywords": ["vanguard"]},
    "6": {"key": "invesco", "label": "Invesco", "keywords": ["invesco", "source"]},
    "7": {"key": "spdr", "label": "SPDR (State Street)", "keywords": ["spdr", "state street"]},
    "s": {"key": "skip", "label": "Skip (Not an ETF / Ignore)", "keywords": []}
}

def load_registry():
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_registry(registry):
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Updated registry saved to {REGISTRY_PATH}")

def validate_selection(choice_key, etf_name):
    """
    Checks if the selected provider is plausible based on the ETF name.
    Returns True if plausible or if user confirms the mismatch.
    """
    if choice_key == "skip":
        return True
        
    provider_info = next((p for k, p in PROVIDER_OPTIONS.items() if p["key"] == choice_key), None)
    if not provider_info:
        return True # Should not happen if logic is correct

    keywords = provider_info["keywords"]
    name_lower = etf_name.lower()
    
    match = any(k in name_lower for k in keywords)
    
    if match:
        return True
    else:
        print(f"\n⚠️  WARNING: You selected '{provider_info['label']}', but the name '{etf_name}' does not contain expected keywords {keywords}.")
        confirm = input("Are you sure this is correct? (y/n): ").strip().lower()
        return confirm == 'y'

def update_registry_interactive(trades_df):
    """
    Scans trades for new ISINs and prompts user to classify them.
    """
    registry = load_registry()
    
    if trades_df.empty:
        logger.info("No trades to scan.")
        return

    # Ensure columns exist
    if 'ISIN' not in trades_df.columns or 'NAME' not in trades_df.columns:
        logger.warning("Trades DataFrame missing ISIN or NAME columns. Skipping registry update.")
        return

    unique_assets = trades_df[['ISIN', 'NAME']].drop_duplicates()
    
    new_entries = False
    
    print("\n--- 🕵️  Registry Update Check ---")
    
    for _, row in unique_assets.iterrows():
        isin = row['ISIN']
        name = row['NAME']
        
        if isin not in registry:
            print(f"\n🆕  New Asset Detected:")
            print(f"    ISIN: {isin}")
            print(f"    Name: {name}")
            
            while True:
                print("\nSelect Provider Adapter:")
                for k, v in PROVIDER_OPTIONS.items():
                    print(f"  [{k}] {v['label']}")
                
                choice = input("Choice > ").strip().lower()
                
                if choice in PROVIDER_OPTIONS:
                    selected_key = PROVIDER_OPTIONS[choice]["key"]
                    
                    # Validation Step
                    if validate_selection(selected_key, name):
                        if selected_key != "skip":
                            registry[isin] = selected_key
                            new_entries = True
                            print(f"✅  Mapped {isin} -> {selected_key}")
                        else:
                            # Persist the skip choice to prevent repetitive prompting
                            registry[isin] = "ignore" 
                            new_entries = True
                            print(f"⏭️  Marked {isin} as 'ignore'. You won't be asked again.")
                        break
                else:
                    print("Invalid choice. Please try again.")

    if new_entries:
        save_registry(registry)
    else:
        print("\n✅  Registry is up to date.")

if __name__ == "__main__":
    # For testing, we try to load the parser output if it exists
    test_file = os.path.join(project_root, 'debug', 'parser_test', 'trades.csv')
    if os.path.exists(test_file):
        print(f"Loading test data from {test_file}")
        df = pd.read_csv(test_file)
        update_registry_interactive(df)
    else:
        print("No test trades.csv found. Run the parser first.")
