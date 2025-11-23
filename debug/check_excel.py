import pandas as pd
import os

file_path = "data/inputs/manual_holdings/FR0010361683.xlsx"

print(f"Checking file: {file_path}")

# 1. Check file size
try:
    size = os.path.getsize(file_path)
    print(f"File size: {size} bytes")
except Exception as e:
    print(f"Error getting size: {e}")

# 2. Peek at first bytes (Magic Numbers)
try:
    with open(file_path, "rb") as f:
        header = f.read(10)
        print(f"First 10 bytes: {header}")
except Exception as e:
    print(f"Error reading bytes: {e}")

# 3. Try reading with pandas (default)
print("\n--- Pandas Default Read ---")
try:
    df = pd.read_excel(file_path)
    print("Success!")
    print(df.head())
except Exception as e:
    print(f"Failed: {e}")

# 4. Try reading with 'openpyxl' explicitly
print("\n--- Pandas (engine='openpyxl') ---")
try:
    df = pd.read_excel(file_path, engine='openpyxl')
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

# 5. Try reading as HTML (sometimes they are fake xls)
print("\n--- Pandas (read_html) ---")
try:
    dfs = pd.read_html(file_path)
    print("Success! (It was HTML)")
    print(dfs[0].head())
except Exception as e:
    print(f"Failed: {e}")
