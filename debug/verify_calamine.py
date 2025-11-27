import pandas as pd
from python_calamine.pandas import pandas_monkeypatch

# Activate calamine engine for pandas
pandas_monkeypatch()

file_path = "data/inputs/manual_holdings/FR0010361683.xlsx"

print(f"--- Testing Calamine on: {file_path} ---")

try:
    # Use 'calamine' engine which we just patched in
    df = pd.read_excel(file_path, engine="calamine")
    print("✅ Success! Calamine read the file.")
    print(f"Shape: {df.shape}")
    print("First 5 rows:")
    print(df.head())
except Exception as e:
    print(f"❌ Failed: {e}")
