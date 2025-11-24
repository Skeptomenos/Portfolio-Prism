import pandas as pd
from python_calamine import CalamineWorkbook
from python_calamine.pandas import pandas_monkeypatch

# Activate calamine engine
pandas_monkeypatch()

file_path = "data/inputs/manual_holdings/FR0010361683.xlsx"

print(f"--- Inspecting {file_path} ---")

try:
    df = pd.read_excel(file_path, engine="calamine")
    print("Columns:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head().to_string())
    
    # Look for AstraZeneca
    astra = df[df.astype(str).apply(lambda x: x.str.contains('ASTRA', case=False, na=False)).any(axis=1)]
    print("\n--- AstraZeneca Entry ---")
    print(astra.to_string())
except Exception as e:
    print(f"Failed: {e}")

