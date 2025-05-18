import requests
from bs4 import BeautifulSoup
import csv
from datetime import date
import time
import random

# Constants
base_url = "https://uae.microless.com"
category_path = "/cpus/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; rv:109.0) Gecko/20100101 Firefox/117.0"
]

def scrape_product_page(url):
    for attempt in range(3):
        is_retry = attempt > 0
        if is_retry:
            wait = random.uniform(2, 6) if attempt == 2 else 0
            print(f"🔁 Retry {attempt}/2 {'after waiting' if wait else 'immediate'}.")
            if wait:
                time.sleep(wait)

        headers = {
            "User-Agent": random.choice(USER_AGENTS) if is_retry else USER_AGENTS[0]
        }

        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.content, 'html.parser')

            stock_div = soup.find("div", class_="instock-lable")
            stock_status = stock_div.text.strip() if stock_div else "Unknown"

            qty_selector = soup.select_one("div.quantity-selector select[name='quantity']")
            if qty_selector:
                options = qty_selector.find_all("option")
                max_qty = options[-1].text.strip() if options else "Not listed"
            else:
                max_qty = "Not listed"

            if stock_status != "Unknown" or max_qty != "Not listed":
                return stock_status, max_qty

        except Exception as e:
            print(f"❌ Error scraping: {url} -> {e}")

    return "Unknown", "Not listed"

def scrape_category_page(url):
    res = requests.get(url, headers={"User-Agent": USER_AGENTS[0]})
    soup = BeautifulSoup(res.content, "html.parser")
    products = soup.find_all("div", class_="product product-carousel grid-list")
    return products

def scrape(export_dir):
    product_data = []
    page = 1

    while True:
        if page == 1:
            url = base_url + category_path
        else:
            url = f"{base_url}{category_path}l/?sort=popularity&page={page}"

        print(f"🔄 Scraping page {page}: {url}")
        products = scrape_category_page(url)

        if not products:
            print("✅ No more products found.")
            break

        for p in products:
            try:
                title_tag = p.select_one("div.product-title a")
                title = title_tag.text.strip()
                link = title_tag["href"].strip()
                full_url = link if link.startswith("http") else base_url + link

                price_tag = p.select_one("div.product-price .new-price .price-amount")
                price = price_tag.text.strip().replace(",", "") if price_tag else "0"
                price_val = float(price) if price.replace(".", "", 1).isdigit() else 0

                discount_tag = p.select_one("div.product-discount-badge")
                discount = discount_tag.text.strip() if discount_tag else ""

                stock_status = ""
                max_qty = ""

                if price_val > 1000:
                    print(f"🟡 Checking stock for: {title}")
                    stock_status, max_qty = scrape_product_page(full_url)

                product_data.append({
                    "Date": date.today().isoformat(),
                    "Product Name": title,
                    "Price (AED)": price,
                    "Discount": discount,
                    "Stock Status": stock_status,
                    "Available Qty": max_qty,
                    "Product URL": full_url
                })

                time.sleep(random.uniform(1.5, 3.5))

            except Exception as e:
                print(f"❌ Error extracting product: {e}")

        page += 1

    if product_data:
        export_dir.mkdir(exist_ok=True)
        filename = export_dir / f"microless_cpu_with_stock_{date.today().isoformat()}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=product_data[0].keys())
            writer.writeheader()
            writer.writerows(product_data)

        print(f"\n✅ Scraped {len(product_data)} CPU products. Saved to {filename}")
    else:
        print("⚠️ No products scraped.")
