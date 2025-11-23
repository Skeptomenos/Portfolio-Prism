import pandas as pd
import os

# Use the long filename
file_path = "data/inputs/manual_holdings/Fondszusammensetzung_Amundi MSCI India Swap UCITS ETF EUR Acc_FR0010361683_18_11_2025.xlsx"

print(f"Checking file: {file_path}")

try:
    # Try default read
    df = pd.read_excel(file_path)
    print("Success! (Default)")
    print(df.head())
except Exception as e:
    print(f"Default Failed: {e}")
    
try:
    # Try openpyxl
    df = pd.read_excel(file_path, engine='openpyxl')
    print("Success! (openpyxl)")
except Exception as e:
    print(f"openpyxl Failed: {e}")
