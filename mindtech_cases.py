import requests
from bs4 import BeautifulSoup
import csv
from datetime import date
import os

BASE_URL = "https://uae.microless.com"
CATEGORY_PATH = "/computer_cases/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

product_data = []

def scrape_listing_page(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.find_all("div", class_="product product-carousel grid-list")

def extract_product_info(product):
    try:
        # Title & URL
        title_tag = product.select_one("div.product-title a")
        title = title_tag.text.strip()
        relative_url = title_tag["href"]
        full_url = relative_url if relative_url.startswith("http") else BASE_URL + relative_url

        # Final price
        price_tag = product.select_one("div.product-price .new-price .price-amount")
        price = price_tag.text.strip().replace(",", "") if price_tag else "0"

        # Base price
        old_price_tag = product.select_one("div.product-price .old-price")
        base_price = old_price_tag.text.replace("AED", "").strip().replace(",", "") if old_price_tag else price

        # Discount
        discount_tag = product.select_one("div.product-discount-badge")
        discount = discount_tag.text.strip() if discount_tag else ""

        return {
            "Date": date.today().isoformat(),
            "Product Name": title,
            "Base Price (AED)": base_price,
            "Final Price (AED)": price,
            "Discount": discount,
            "Stock Status": "",  # Not collected from this page
            "Available Qty": "",  # Not collected from this page
            "Product URL": full_url
        }

    except Exception as e:
        print(f"❌ Error parsing product: {e}")
        return None

# Main scrape loop
page = 1
while True:
    if page == 1:
        url = BASE_URL + CATEGORY_PATH
    else:
        url = f"{BASE_URL}{CATEGORY_PATH}l/?sort=popularity&page={page}"

    print(f"🔄 Scraping page {page}: {url}")
    products = scrape_listing_page(url)
    if not products:
        print("✅ No more products found.")
        break

    for product in products:
        data = extract_product_info(product)
        if data:
            product_data.append(data)

    page += 1

# Save to CSV
os.makedirs("outputs", exist_ok=True)
filename = f"outputs/microless_cases_{date.today().isoformat()}.csv"

with open(filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=product_data[0].keys())
    writer.writeheader()
    writer.writerows(product_data)

print(f"\n✅ Scraped {len(product_data)} PC cases. Saved to {filename}")
