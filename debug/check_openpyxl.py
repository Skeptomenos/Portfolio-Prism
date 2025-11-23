import openpyxl
import pandas as pd

file_path = "data/inputs/manual_holdings/FR0010361683.xlsx"

print("--- Trying openpyxl directly ---")
try:
    # Try data_only=True to skip formulas/styles which might be broken
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    print("Workbook loaded successfully!")
    
    ws = wb.active
    data = ws.values
    cols = next(data)
    print(f"Columns: {cols}")
    
    # Convert to DF
    df = pd.DataFrame(data, columns=cols)
    print(df.head())
    
except Exception as e:
    print(f"Failed: {e}")
