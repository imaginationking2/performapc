import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import date

base_url = "https://laifai.ae"
category_path = "/product-category/cpu/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

USER_DELAY = 1.5  # seconds


def get_soup(url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return BeautifulSoup(response.content, "html.parser")


def scrape(export_dir):
    data = []
    page = 1

    while True:
        if page == 1:
            url = base_url + category_path
        else:
            url = base_url + category_path + f"page/{page}/"

        print(f"🔄 Scraping page {page}: {url}")
        soup = get_soup(url)

        if soup is None:
            print("✅ Reached non-existent page (404). Scraping completed.")
            break

        products = soup.find_all("div", class_="product-outer")
        if not products:
            print("✅ No products found. Ending scrape.")
            break

        for p in products:
            try:
                title_tag = p.select_one("h2.woocommerce-loop-product__title")
                title = title_tag.text.strip() if title_tag else "Not found"

                product_link_tag = p.select_one("a.woocommerce-LoopProduct-link")
                product_url = product_link_tag["href"].strip() if product_link_tag else ""

                price_tag = p.select_one("span.price bdi")
                price = price_tag.text.strip().replace("AED", "").strip() if price_tag else "Not found"

                sku_tag = p.select_one("div.product-sku")
                sku = sku_tag.text.replace("SKU:", "").strip() if sku_tag else ""

                data.append({
                    "Product Name": title,
                    "Price (AED)": price,
                    "SKU": sku,
                    "Product URL": product_url
                })

            except Exception as e:
                print(f"❌ Error extracting product: {e}")

        page += 1
        time.sleep(USER_DELAY)

    if data:
        export_dir.mkdir(exist_ok=True)
        filename = export_dir / f"laifai_cpu_{date.today().isoformat()}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print(f"\n📦 Scraped {len(data)} CPU products across {page - 1} pages. Saved to {filename}")
    else:
        print("⚠️ No products were scraped.")
