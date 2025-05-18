import pandas as pd
from pathlib import Path
from datetime import date

EXPORT_DIR = Path("exports")
ARCHIVE_DIR = Path("data_archive")
ARCHIVE_DIR.mkdir(exist_ok=True)

# Unified field names
COLUMN_MAP = {
    "Product Name": "product_name",
    "Final Price (AED)": "price",
    "Price (AED)": "price",
    "Base Price (AED)": "base_price",
    "Original Price (AED)": "base_price",
    "Discount": "discount",
    "Stock Status": "stock_status",
    "Available Qty": "available_qty",
    "Product URL": "product_url",
    "Date": "date"
}

def normalize_file(file_path: Path):
    try:
        df = pd.read_csv(file_path)
        df = df.rename(columns={col: COLUMN_MAP.get(col, col) for col in df.columns})

        for col in COLUMN_MAP.values():
            if col not in df.columns:
                df[col] = ""

        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["base_price"] = pd.to_numeric(df["base_price"], errors="coerce")

        df["base_price"] = df.apply(
            lambda row: row["price"] if pd.isna(row["base_price"]) or row["base_price"] < row["price"] else row["base_price"],
            axis=1
        )

        df["source_file"] = file_path.name
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["VendorKey"] = df["source_file"].str.replace(".csv", "", regex=False).str.extract(r"(^.*?)(_20\\d{2}-\\d{2}-\\d{2})?$")[0]

        return df

    except Exception as e:
        print(f"❌ Failed to normalize {file_path.name}: {e}")
        return pd.DataFrame()

def run_normalization():
    all_files = list(EXPORT_DIR.glob("*.csv"))
    all_data = []

    for file in all_files:
        df = normalize_file(file)
        if not df.empty:
            all_data.append(df)

            # Save each file to archive
            archive_path = ARCHIVE_DIR / f"normalized_daily_{date.today().isoformat()}.csv"
            df.to_csv(archive_path, index=False)

    if all_data:
        combined = pd.concat(all_data, ignore_index=True).drop_duplicates()
        OUTPUT_FILE = EXPORT_DIR / "normalized_combined.csv"
        combined.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Normalized and saved to {OUTPUT_FILE}")
    else:
        print("⚠️ No data to normalize.")

if __name__ == "__main__":
    run_normalization()
