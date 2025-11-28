import pandas as pd

try:
    df = pd.read_csv("outputs/true_exposure_report.csv")
    total = df["total_exposure"].sum()
    print(f"Total Portfolio Value: {total}")

    astra = df[df["name"].str.contains("ASTRA", case=False, na=False)]
    if not astra.empty:
        print("\nAstraZeneca Holdings:")
        print(astra.to_string())
    else:
        print("\nNo AstraZeneca found.")

except Exception as e:
    print(f"Error: {e}")
