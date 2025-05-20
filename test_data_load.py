# test_data_load.py
import pandas as pd
import glob

files = glob.glob("data_archive/normalized_daily_*.csv")
print("Files found:", files)

dfs = [pd.read_csv(f) for f in files]
df = pd.concat(dfs, ignore_index=True)

print("Rows loaded:", len(df))
print(df.head())
