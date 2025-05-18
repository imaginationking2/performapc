import requests
from bs4 import BeautifulSoup
import csv
import random
from datetime import date

base_url = "https://gccgamers.com"
category_path = "/computer-parts-compnents/graphic-cards.html"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64)",
]

def scrape_category_page(url):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.find_all("div", class_="product-item-info")

def scrape(export_dir):
    product_data = []
    page = 1

    while True:
        page_url = category_path if page == 1 else f"{category_path}?p={page}"
        full_url = f"{base_url}{'/' if not page_url.startswith('/') else ''}{page_url}"
        print(f"🔄 Scraping page {page}: {full_url}")
        products = scrape_category_page(full_url)
        if not products:
            print("✅ No more products found.")
            break

        for p in products:
            try:
                title_tag = p.select_one("h2.product.name.product-name a")
                if not title_tag:
                    continue
                title = title_tag.text.strip()
                link = title_tag["href"].strip()

                price_tag = p.select_one("span.price-wrapper span.price")
                price_text = price_tag.text.strip().replace("AED", "").replace(",", "").strip() if price_tag else ""
                price = float(price_text) if price_text.replace(".", "", 1).isdigit() else ""

                old_price_tag = p.select_one("span.old-price span.price")
                old_price = old_price_tag.text.strip().replace("AED", "").strip() if old_price_tag else ""

                discount_tag = p.select_one("span.labelsale")
                discount = discount_tag.text.strip() if discount_tag else ""

                stock_tag = p.select_one("div.stock.unavailable span")
                stock_status = "Out of Stock" if stock_tag else "In Stock"

                product_data.append({
                    "Date": date.today().isoformat(),
                    "Product Name": title,
                    "Model": "",
                    "Price (AED)": price,
                    "Original Price (AED)": old_price,
                    "Discount": discount,
                    "Stock Status": stock_status,
                    "Product URL": link
                })

            except Exception as e:
                print(f"❌ Product parse error: {e}")

        page += 1

    if product_data:
        export_dir.mkdir(exist_ok=True)
        filename = export_dir / f"gccgamers_gpu_{date.today().isoformat()}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=product_data[0].keys())
            writer.writeheader()
            writer.writerows(product_data)

        print(f"\n✅ Scraped {len(product_data)} GPU products. Saved to {filename}")
    else:
        print("⚠️ No GPU products scraped.")
