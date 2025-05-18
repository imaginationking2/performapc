import requests
from bs4 import BeautifulSoup
import csv
from datetime import date
import time
import random
from pathlib import Path

BASE_URL = "https://uae.microless.com"
CATEGORY_URL = f"{BASE_URL}/computer_cases/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def scrape_product_page(url):
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.content, 'html.parser')

        stock_block = soup.select_one("div.product-price + div.bottom div.free-shipping, div.product-price + div.bottom div.instock-lable")
        out_of_stock = soup.select_one(".product-price + .bottom .out-of-stock")

        stock_status = "Out of stock" if out_of_stock else "In stock"

        qty_selector = soup.select_one("div.quantity-selector select[name='quantity']")
        if qty_selector:
            options = qty_selector.find_all("option")
            max_qty = options[-1].text.strip() if options else "Not listed"
        else:
            max_qty = "Not listed"

        return stock_status, max_qty

    except Exception as e:
        print(f"❌ Error scraping stock info for: {url} — {e}")
        return "Unknown", "Not listed"

def get_product_data(product):
    try:
        name_tag = product.select_one(".product-title a")
        name = name_tag.text.strip()
        href = name_tag["href"]
        url = href if href.startswith("http") else BASE_URL + href

        price_block = product.select_one("div.new-price span.price-amount")
        base_price_block = product.select_one("div.old-price")

        final_price = price_block.text.replace("AED", "").replace(",", "").strip() if price_block else "0"
        base_price = base_price_block.text.replace("AED", "").replace(",", "").strip() if base_price_block else final_price

        price_val = float(final_price) if final_price.replace(".", "", 1).isdigit() else 0

        discount_block = product.select_one("div.product-discount-badge")
        discount = discount_block.text.replace("% OFF", "").strip() if discount_block else ""

        stock_status = ""
        max_qty = ""

        if price_val > 1000:
            print(f"🟡 Checking stock for: {name}")
            stock_status, max_qty = scrape_product_page(url)

        return {
            "Date": date.today().isoformat(),
            "Product Name": name,
            "Base Price (AED)": base_price,
            "Final Price (AED)": final_price,
            "Discount": discount,
            "Stock Status": stock_status,
            "Available Qty": max_qty,
            "Product URL": url
        }

    except Exception as e:
        print(f"❌ Error parsing product: {e}")
        return None

def scrape_page(page_num):
    page_url = CATEGORY_URL if page_num == 1 else f"{CATEGORY_URL}l/?sort=popularity&page={page_num}"
    print(f"🔄 Scraping page {page_num}: {page_url}")
    try:
        res = requests.get(page_url, headers=HEADERS)
        soup = BeautifulSoup(res.content, "html.parser")
        return soup.select("div.product.product-carousel.grid-list")
    except Exception as e:
        print(f"❌ Failed to load page {page_num}: {e}")
        return []

def scrape(export_dir: Path):
    all_products = []
    page = 1

    while True:
        products = scrape_page(page)
        if not products:
            print("✅ No more products found.")
            break

        for product in products:
            item = get_product_data(product)
            if item:
                all_products.append(item)

            time.sleep(random.uniform(1.2, 2.5))

        page += 1

    if all_products:
        export_dir.mkdir(exist_ok=True)
        filename = export_dir / f"microless_cases_{date.today().isoformat()}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_products[0].keys())
            writer.writeheader()
            writer.writerows(all_products)

        print(f"\n✅ Saved {len(all_products)} case products to {filename}")
    else:
        print("⚠️ No case products scraped.")
