import requests
from bs4 import BeautifulSoup
from datetime import date
import csv
import time
from pathlib import Path

BASE_URL = "https://laifai.ae"
CATEGORY_URL = f"{BASE_URL}/product-category/vga-card/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def scrape_page(url):
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.content, "html.parser")
        return soup.find_all("div", class_="product-outer")
    except Exception as e:
        print(f"❌ Error fetching {url} — {e}")
        return []

def parse_product(product):
    try:
        name_tag = product.select_one("h2.woocommerce-loop-product__title a")
        if not name_tag:
            return None
        name = name_tag.text.strip()
        url = name_tag["href"]

        price_box = product.select_one("span.price")
        if not price_box:
            return None

        final_price_tag = price_box.select_one("ins span.woocommerce-Price-amount")
        base_price_tag = price_box.select_one("del span.woocommerce-Price-amount")
        single_price_tag = price_box.select_one("span.woocommerce-Price-amount")

        if final_price_tag:
            final_price = final_price_tag.text.replace("AED", "").replace(",", "").strip()
        elif single_price_tag:
            final_price = single_price_tag.text.replace("AED", "").replace(",", "").strip()
        else:
            final_price = "0"

        if base_price_tag:
            base_price = base_price_tag.text.replace("AED", "").replace(",", "").strip()
        else:
            base_price = final_price

        return {
            "Date": date.today().isoformat(),
            "Product Name": name,
            "Base Price (AED)": base_price,
            "Final Price (AED)": final_price,
            "Discount": "",
            "Stock Status": "In stock",
            "Available Qty": "",
            "Product URL": url
        }

    except Exception as e:
        print(f"❌ Error parsing product — {e}")
        return None

def scrape(export_dir: Path):
    product_data = []
    page = 1

    while True:
        url = f"{CATEGORY_URL}" if page == 1 else f"{CATEGORY_URL}page/{page}/"
        print(f"🔄 Scraping page {page}: {url}")
        products = scrape_page(url)
        if not products:
            print("✅ No more products found.")
            break

        for product in products:
            item = parse_product(product)
            if item:
                product_data.append(item)

        page += 1
        time.sleep(1.5)

    if product_data:
        export_dir.mkdir(exist_ok=True)
        filename = export_dir / f"laifai_gpu_{date.today().isoformat()}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=product_data[0].keys())
            writer.writeheader()
            writer.writerows(product_data)

        print(f"\n✅ Saved {len(product_data)} GPU products to {filename}")
    else:
        print("⚠️ No GPU products scraped.")
