import streamlit as st
import pandas as pd
from pathlib import Path
import difflib
import datetime
import glob

# Setup
st.set_page_config(page_title="PC Market Tracker", layout="wide")
ARCHIVE_DIR = Path("data_archive")
files = sorted(ARCHIVE_DIR.glob("normalized_daily_*.csv"))

# Load all daily files
if not files:
    st.error("No normalized_daily_*.csv files found.")
    st.stop()

dfs = []
for f in files:
    try:
        df = pd.read_csv(f)
        df["date"] = pd.to_datetime(df.get("date", f.name.split("normalized_daily_")[-1].replace(".csv", "")))
        dfs.append(df)
    except Exception as e:
        st.warning(f"⚠️ Failed to load {f.name}: {e}")

# Combine
df = pd.concat(dfs, ignore_index=True)
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["base_price"] = pd.to_numeric(df["base_price"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Vendor/source cleanup
df["Source"] = df["source_file"].str.replace(".csv", "", regex=False)
df["VendorKey"] = df["Source"].str.extract(r"(^.*?)(_20\d{2}-\d{2}-\d{2})?$")[0]

# Category mapping
category_map = {
    "gccgamers_cases": "Case",
    "microless_cases": "Case",
    "gccgamers_gpu": "GPU",
    "microless_gpu": "GPU",
    "laifai_gpu": "GPU",
    "laifai_cpu": "CPU",
    "microless_cpu": "CPU",
    "microless_cpu_with_stock": "CPU",
    "dxbgamers_cpu": "CPU",
}
df["Category"] = df["VendorKey"].map(category_map).fillna("Other")

# Product links
df["Link"] = df["product_url"].apply(lambda x: f"[🔗 View]({x})" if pd.notna(x) else "")

# Rename
df.rename(columns={
    "product_name": "Product Name",
    "price": "Final Price (AED)",
    "base_price": "Base Price (AED)",
    "stock_status": "Stock Status"
}, inplace=True)

# Sidebar
st.sidebar.markdown("📅 **Latest data update:**")
st.sidebar.code(df['date'].max().date())
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Go to", [
    "Product Explorer", "HYTE Case Tracker", "Daily Insights", "Vendor Snapshot", "Promotions", "Profit Estimator"
])

# 1️⃣ Product Explorer
if page == "Product Explorer":
    st.title("📦 Product Explorer")
    category = st.selectbox("Select category", sorted(df["Category"].unique()))
    vendors = df["VendorKey"].dropna().unique().tolist()
    selected_vendors = st.multiselect("Vendors", vendors, default=vendors)
    date_range = st.date_input("Date range", [df["date"].min(), df["date"].max()])

    filtered = df[
        (df["Category"] == category) &
        (df["VendorKey"].isin(selected_vendors)) &
        (df["date"] >= pd.to_datetime(date_range[0])) &
        (df["date"] <= pd.to_datetime(date_range[1]))
    ]

    st.markdown(f"### Showing {len(filtered)} results in **{category}**")
    st.dataframe(filtered, use_container_width=True)

# 2️⃣ HYTE Case Tracker
elif page == "HYTE Case Tracker":
    st.title("🖥️ HYTE Case Price Tracker")
    
    # Filter to HYTE cases only
    hyte_df = df[(df["Category"] == "Case") & (df["Product Name"].str.contains("HYTE", case=False, na=False))]

    # Tag HYTE model
    def get_hyte_model(name):
        name = name.lower()
        if "y40" in name:
            return "Y40"
        elif "y70" in name:
            return "Y70"
        elif "y60" in name:
            return "Y60"
        elif "revolt" in name:
            return "Revolt"
        else:
            return "Other"

    hyte_df["HYTE Model"] = hyte_df["Product Name"].apply(get_hyte_model)

    # Sidebar filters
    vendors = sorted(hyte_df["VendorKey"].dropna().unique().tolist())
    models = sorted(hyte_df["HYTE Model"].dropna().unique().tolist())

    selected_vendors = st.multiselect("Select Vendors", vendors, default=vendors)
    selected_models = st.multiselect("Select HYTE Models", models, default=models)

    # Apply filters
    hyte_df_filtered = hyte_df[
        (hyte_df["VendorKey"].isin(selected_vendors)) &
        (hyte_df["HYTE Model"].isin(selected_models))
    ].sort_values(by=["date", "Final Price (AED)"], ascending=[False, True])

    st.dataframe(hyte_df_filtered, use_container_width=True)

    if not hyte_df_filtered.empty:
        st.markdown("### 📈 Average Price by Vendor")
        chart_data = hyte_df_filtered.groupby("Source")["Final Price (AED)"].mean().sort_values()
        st.bar_chart(chart_data)
    else:
        st.info("No HYTE cases found for selected filters.")

# 3️⃣ Daily Insights
elif page == "Daily Insights":
    st.title("🆕 Daily Market Insights")

    # Date range selection
    st.markdown("### 📅 Analysis Period")
    col1, col2 = st.columns(2)
    
    with col1:
        from_date = st.date_input("From Date", df["date"].min().date())
    with col2:
        to_date = st.date_input("To Date", df["date"].max().date())

    # Add category filter for out of stock analysis
    st.markdown("### 📭 Analysis Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        categories = sorted(df["Category"].unique())
        selected_categories = st.multiselect("Filter by categories", categories, default=categories, key="out_of_stock_categories")
    
    with col2:
        vendors = df["VendorKey"].dropna().unique().tolist()
        selected_vendors = st.multiselect("Filter by vendors", vendors, default=vendors, key="out_of_stock_vendors")

    # Filter data by date range
    df_from = df[df["date"] >= pd.to_datetime(from_date)]
    df_to = df[df["date"] <= pd.to_datetime(to_date)]
    df_range = df[(df["date"] >= pd.to_datetime(from_date)) & (df["date"] <= pd.to_datetime(to_date))]

    # Get earliest and latest data within the range for comparison
    df_start_period = df[df["date"] == df_range["date"].min()]
    df_end_period = df[df["date"] == df_range["date"].max()]

    new_products = df_end_period[~df_end_period["Product Name"].isin(df_start_period["Product Name"])]
    restocked = df_end_period[df_end_period["Stock Status"].str.lower() != "out of stock"]
    restocked = restocked[restocked["Product Name"].isin(df_start_period[df_start_period["Stock Status"].str.lower() == "out of stock"]["Product Name"])]

    delisted = df_start_period[~df_start_period["Product Name"].isin(df_end_period["Product Name"])]

    # Collect all products that went out of stock during the entire date range
    went_out_of_stock_list = []
    
    # Get all unique dates in the range, sorted
    dates_in_range = sorted(df_range["date"].unique())
    
    for i in range(1, len(dates_in_range)):
        current_date = dates_in_range[i]
        previous_date = dates_in_range[i-1]
        
        df_current = df[df["date"] == current_date]
        df_previous = df[df["date"] == previous_date]
        
        # Products that were available yesterday but out of stock today
        previously_available = df_previous[df_previous["Stock Status"].str.lower() != "out of stock"]
        now_unavailable = df_current[df_current["Stock Status"].str.lower() == "out of stock"]
        daily_out_of_stock = now_unavailable[now_unavailable["Product Name"].isin(previously_available["Product Name"])]
        
        # Add the date when it went out of stock
        if not daily_out_of_stock.empty:
            daily_out_of_stock = daily_out_of_stock.copy()
            daily_out_of_stock["Went Out of Stock Date"] = current_date
            went_out_of_stock_list.append(daily_out_of_stock)
    
    # Combine all out of stock events
    if went_out_of_stock_list:
        went_out_of_stock = pd.concat(went_out_of_stock_list, ignore_index=True)
        # Remove duplicates (same product might go out of stock multiple times)
        went_out_of_stock = went_out_of_stock.drop_duplicates(subset=["Product Name", "Source"], keep="first")
    else:
        went_out_of_stock = pd.DataFrame()
    
    # Apply category and vendor filters to out of stock products
    if not went_out_of_stock.empty:
        went_out_of_stock_filtered = went_out_of_stock[
            (went_out_of_stock["Category"].isin(selected_categories)) &
            (went_out_of_stock["VendorKey"].isin(selected_vendors))
        ]
    else:
        went_out_of_stock_filtered = pd.DataFrame()

    merged = pd.merge(
        df_end_period[["Product Name", "Final Price (AED)"]],
        df_start_period[["Product Name", "Final Price (AED)"]],
        on="Product Name", suffixes=("_end", "_start")
    )
    merged["change"] = merged["Final Price (AED)_end"] - merged["Final Price (AED)_start"]
    top_changes = merged.reindex(columns=["Product Name", "Final Price (AED)_start", "Final Price (AED)_end", "change"])
    top_changes = top_changes.sort_values("change", key=abs, ascending=False).head(3)

    st.subheader(f"🆕 Newly Added Products ({from_date} to {to_date})")
    st.dataframe(new_products)
    st.subheader(f"♻️ Restocked Products ({from_date} to {to_date})")
    st.dataframe(restocked)
    st.subheader(f"🗑️ Delisted Products ({from_date} to {to_date})")
    st.dataframe(delisted)
    st.subheader(f"📭 Went Out of Stock During Period ({len(went_out_of_stock_filtered)} filtered results)")
    if not went_out_of_stock_filtered.empty:
        # Reorder columns to show the out of stock date prominently
        display_columns = ["Went Out of Stock Date", "Product Name", "Final Price (AED)", "Category", "Source", "Stock Status"]
        available_columns = [col for col in display_columns if col in went_out_of_stock_filtered.columns]
        st.dataframe(went_out_of_stock_filtered[available_columns])
    else:
        st.info("No products went out of stock during the selected period.")
    
    # Show summary by category
    if not went_out_of_stock_filtered.empty:
        st.markdown("#### 📊 Out of Stock Summary by Category")
        category_summary = went_out_of_stock_filtered.groupby("Category").size().reset_index(name="Count")
        st.dataframe(category_summary)
    
    st.subheader(f"📉 Top 3 Price Changes ({from_date} to {to_date})")
    st.dataframe(top_changes)

# 4️⃣ Vendor Snapshot
elif page == "Vendor Snapshot":
    st.title("🏬 Vendor Performance Snapshot")
    snapshot = df.groupby("Source").agg({
        "Product Name": "count",
        "Final Price (AED)": ["mean", "std"],
        "Category": pd.Series.nunique
    })
    st.dataframe(snapshot)

# 5️⃣ Promotions
elif page == "Promotions":
    st.title("🎁 Vendor Promotions & Bundles")
    promo_df = df[df["Product Name"].str.contains("bundle|free|gift|combo", case=False, na=False)]
    st.dataframe(promo_df)

# 6️⃣ Profit Estimator
elif page == "Profit Estimator":
    st.title("💰 Profit Estimator")
    markup = st.slider("Estimated markup %", 10, 100, 35)
    df["Estimated Cost"] = df["Final Price (AED)"] * (1 - markup / 100)
    df["Estimated Profit"] = df["Final Price (AED)"] - df["Estimated Cost"]

    for cat in ["Case", "CPU", "GPU"]:
        st.subheader(f"📂 {cat}s")
        filtered = df[df["Category"] == cat]
        st.dataframe(filtered[["Product Name", "Final Price (AED)", "Estimated Cost", "Estimated Profit", "Source"]], use_container_width=True)