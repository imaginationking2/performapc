import streamlit as st
import pandas as pd
from pathlib import Path
import difflib
import datetime

# Setup
st.set_page_config(page_title="PC Market Tracker", layout="wide")
DATA_PATH = Path("exports/normalized_combined.csv")

# Load data
if not DATA_PATH.exists():
    st.error("Missing file: `exports/normalized_combined.csv`")
    st.stop()

df = pd.read_csv(DATA_PATH)
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["base_price"] = pd.to_numeric(df["base_price"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Source and VendorKey cleanup
df["Source"] = df["source_file"].str.replace(".csv", "", regex=False)
df["VendorKey"] = df["Source"].str.extract(r"(^.*?)(_20\d{2}-\d{2}-\d{2})?$")[0]

# Category mapping by VendorKey
category_map = {
    "gccgamers_cases": "Case",
    "microless_cases": "Case",
    "gccgamers_gpu": "GPU",
    "microless_gpu": "GPU",
    "laifai_gpu": "GPU",
    "laifai_cpu": "CPU",
    "microless_cpu": "CPU",
    "dxbgamers_cpu": "CPU",
}
df["Category"] = df["VendorKey"].map(category_map).fillna("Other")

# Product links
df["Link"] = df["product_url"].apply(lambda x: f"[🔗 View]({x})" if pd.notna(x) else "")

# Rename for display
df.rename(columns={
    "product_name": "Product Name",
    "price": "Final Price (AED)",
    "base_price": "Base Price (AED)",
}, inplace=True)

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Go to", [
    "Product Explorer", "HYTE Case Tracker", "Daily Insights", "Vendor Snapshot", "Promotions", "Profit Estimator"
])

# -------------------------
# 📦 Product Explorer Page
# -------------------------
if page == "Product Explorer":
    st.title("📦 Product Explorer")

    category = st.selectbox("Select category", sorted(df["Category"].unique()))
    vendors = df["Source"].unique().tolist()
    selected_vendors = st.multiselect("Vendors", vendors, default=vendors)
    date_range = st.date_input("Date range", [df["date"].min(), df["date"].max()])

    filtered = df[
        (df["Category"] == category) &
        (df["Source"].isin(selected_vendors)) &
        (df["date"] >= pd.to_datetime(date_range[0])) &
        (df["date"] <= pd.to_datetime(date_range[1]))
    ]

    st.markdown(f"### Showing {len(filtered)} results in **{category}**")
    st.dataframe(filtered, use_container_width=True)

# --------------------------
# 🖥️ HYTE Case Tracker Page
# --------------------------
elif page == "HYTE Case Tracker":
    st.title("🖥️ HYTE Case Price Tracker")

    hyte_df = df[(df["Category"] == "Case") & (df["Product Name"].str.contains("HYTE", case=False, na=False))]
    st.dataframe(hyte_df, use_container_width=True)

    if not hyte_df.empty:
        st.markdown("### 📈 Average Price by Vendor")
        chart_data = hyte_df.groupby("Source")["Final Price (AED)"].mean().sort_values()
        st.bar_chart(chart_data)
    else:
        st.info("No HYTE cases found.")

# --------------------------
# 🆕 Daily Insights Page
# --------------------------
elif page == "Daily Insights":
    st.title("🆕 Daily Market Insights")

    dates = sorted(df["date"].dropna().unique())
    today = st.selectbox("Select date to analyze", reversed(dates))
    past = st.selectbox("Compare against date", reversed(dates))

    df_today = df[df["date"] == pd.to_datetime(today)]
    df_past = df[df["date"] == pd.to_datetime(past)]

    new_products = df_today[~df_today["Product Name"].isin(df_past["Product Name"])]
    restocked = df_today[df_today["stock_status"].str.lower() != "out of stock"]
    restocked = restocked[restocked["Product Name"].isin(df_past[df_past["stock_status"].str.lower() == "out of stock"]["Product Name"])]

    delisted = df_past[~df_past["Product Name"].isin(df_today["Product Name"])]

    previously_available = df_past[df_past["stock_status"].str.lower() != "out of stock"]
    now_unavailable = df_today[df_today["stock_status"].str.lower() == "out of stock"]
    went_out_of_stock = now_unavailable[now_unavailable["Product Name"].isin(previously_available["Product Name"])]

    merged = pd.merge(df_today[["Product Name", "Final Price (AED)"]], df_past[["Product Name", "Final Price (AED)"]], on="Product Name", suffixes=_("today", "past"))
    merged["change"] = merged["Final Price (AED)_today"] - merged["Final Price (AED)_past"]
    top_changes = merged.reindex(columns=["Product Name", "Final Price (AED)_past", "Final Price (AED)_today", "change"])
    top_changes = top_changes.sort_values("change", key=abs, ascending=False).head(3)

    st.subheader("🆕 Newly Added Products")
    st.dataframe(new_products)
    st.subheader("♻️ Restocked Products")
    st.dataframe(restocked)
    st.subheader("🗑️ Delisted Products")
    st.dataframe(delisted)
    st.subheader("📭 Went Out of Stock Today")
    st.dataframe(went_out_of_stock)
    st.subheader("📉 Top 3 Price Changes Today")
    st.dataframe(top_changes)

# --------------------------
# 🏬 Vendor Snapshot
# --------------------------
elif page == "Vendor Snapshot":
    st.title("🏬 Vendor Performance Snapshot")
    snapshot = df.groupby("Source").agg({
        "Product Name": "count",
        "Final Price (AED)": ["mean", "std"],
        "Category": pd.Series.nunique
    })
    st.dataframe(snapshot)

# --------------------------
# 🎁 Promotions
# --------------------------
elif page == "Promotions":
    st.title("🎁 Vendor Promotions & Bundles")
    promo_df = df[df["Product Name"].str.contains("bundle|free|gift|combo", case=False, na=False)]
    st.dataframe(promo_df)

# --------------------------
# 💰 Profit Estimator (Internal)
# --------------------------
elif page == "Profit Estimator":
    st.title("💰 Profit Estimator")
    markup = st.slider("Estimated markup %", 10, 100, 35)
    df["Estimated Cost"] = df["Final Price (AED)"] * (1 - markup / 100)
    df["Estimated Profit"] = df["Final Price (AED)"] - df["Estimated Cost"]

    for cat in ["Case", "CPU", "GPU"]:
        st.subheader(f"📂 {cat}s")
        filtered = df[df["Category"] == cat]
        st.dataframe(filtered[["Product Name", "Final Price (AED)", "Estimated Cost", "Estimated Profit", "Source"]], use_container_width=True)