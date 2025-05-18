import requests
from bs4 import BeautifulSoup
from datetime import date
import csv
import time
from pathlib import Path

BASE_URL = "https://dxbgamers.com"
CATEGORY_PATH = "/product-category/hardware-components/processors/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def scrape_page(url):
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.content, "html.parser")
        return soup.find_all("div", class_="product-wrapper")
    except Exception as e:
        print(f"❌ Error fetching page: {url} — {e}")
        return []

def parse_product(prod):
    try:
        title_tag = prod.select_one("h3.wd-entities-title a")
        name = title_tag.text.strip()
        url = title_tag["href"]

        new_price_tag = prod.select_one("ins .woocommerce-Price-amount")
        old_price_tag = prod.select_one("del .woocommerce-Price-amount")
        single_price_tag = prod.select_one("span.price > span.woocommerce-Price-amount")

        if new_price_tag:
            final_price = new_price_tag.text.replace("AED", "").strip().replace(",", "")
        elif single_price_tag:
            final_price = single_price_tag.text.replace("AED", "").strip().replace(",", "")
        else:
            final_price = "0"

        if old_price_tag:
            base_price = old_price_tag.text.replace("AED", "").strip().replace(",", "")
        else:
            base_price = final_price

        discount_tag = prod.select_one("span.onsale.product-label")
        discount = discount_tag.text.strip() if discount_tag else ""

        stock_tag = prod.select_one("p.wd-product-stock")
        stock_status = stock_tag.text.strip() if stock_tag else "Unknown"

        return {
            "Date": date.today().isoformat(),
            "Product Name": name,
            "Base Price (AED)": base_price,
            "Final Price (AED)": final_price,
            "Discount": discount,
            "Stock Status": stock_status,
            "Available Qty": "",
            "Product URL": url
        }

    except Exception as e:
        print(f"❌ Error parsing product: {e}")
        return None

def scrape(export_dir: Path):
    product_data = []
    page = 1

    while True:
        page_url = CATEGORY_PATH if page == 1 else f"{CATEGORY_PATH}page/{page}/"
        full_url = BASE_URL + page_url
        print(f"🔄 Scraping page {page}: {full_url}")
        products = scrape_page(full_url)
        if not products:
            print("✅ No more products found.")
            break

        for prod in products:
            data = parse_product(prod)
            if data:
                product_data.append(data)
            time.sleep(0.8)

        page += 1

    if product_data:
        export_dir.mkdir(exist_ok=True)
        filename = export_dir / f"dxbgamers_cpu_{date.today().isoformat()}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=product_data[0].keys())
            writer.writeheader()
            writer.writerows(product_data)

        print(f"\n✅ Saved {len(product_data)} CPUs to {filename}")
    else:
        print("⚠️ No CPU products scraped.")
