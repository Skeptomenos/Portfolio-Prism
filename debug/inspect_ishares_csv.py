import requests
import pandas as pd
from io import StringIO

url = "https://www.ishares.com/de/privatanleger/de/produkte/251903/fund/1478358465952.ajax?fileType=csv&fileName=IE00B53SZB19_holdings&dataType=fund"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Fetching {url}...")
response = requests.get(url, headers=headers)
response.raise_for_status()

print("Parsing CSV...")
csv_data = StringIO(response.text)
df = pd.read_csv(csv_data, skiprows=2)

print("\nColumns found:")
print(df.columns.tolist())

print("\nFirst 5 rows (Ticker, Name, Weight):")
print(df[["Emittententicker", "Name", "Gewichtung (%)"]].head())
