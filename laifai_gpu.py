import requests
from bs4 import BeautifulSoup
from datetime import date
import csv
import time
import random
from pathlib import Path

BASE_URL = "https://laifai.ae"
CATEGORY_URL = f"{BASE_URL}/product-category/vga-card/"

HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/121.0",
    ]),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

def get_soup(url, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, "html.parser")
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:
                wait = random.uniform(5, 10)
                print(f"🔄 Rate limited. Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
        except requests.RequestException as e:
            print(f"⚠️ Connection error: {e}. Retrying...")
            time.sleep(2)
    return None

def parse_product(product):
    try:
        title_tag = product.select_one("h2.woocommerce-loop-product__title")
        title = title_tag.text.strip() if title_tag else "Unknown"

        product_link_tag = product.select_one("a.woocommerce-LoopProduct-link")
        url = product_link_tag["href"].strip() if product_link_tag else ""

        price_tag = product.select_one("span.price bdi")
        final_price = price_tag.text.replace("AED", "").replace(",", "").strip() if price_tag else "0"

        return {
            "Date": date.today().isoformat(),
            "Product Name": title,
            "Base Price (AED)": final_price,
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
        url = CATEGORY_URL if page == 1 else f"{CATEGORY_URL}page/{page}/"
        print(f"🔄 Scraping page {page}: {url}")
        soup = get_soup(url)

        if soup is None:
            print("✅ Reached non-existent page or blocked. Ending scrape.")
            break

        products = soup.find_all("div", class_="product-outer")
        if not products:
            print("✅ No products found. Ending scrape.")
            break

        for product in products:
            item = parse_product(product)
            if item:
                product_data.append(item)

        page += 1
        delay = random.uniform(1.5, 3.5)
        print(f"⏳ Waiting {delay:.2f}s before next page...")
        time.sleep(delay)

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
