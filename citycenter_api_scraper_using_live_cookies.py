import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import date
from pathlib import Path

# Load cookies saved from the previous session
with open("citycenter_cookies.json", "r") as f:
    raw_cookies = json.load(f)

# Convert cookies to requests format
cookies = {cookie['name']: cookie['value'] for cookie in raw_cookies}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://citycenter.jo/computer-hardware/components-cpu-and-processor",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

url = "https://citycenter.jo/index.php?route=module/brainyfilter/ajaxfilter&count=1&price=1&path=18_64"

res = requests.get(url, headers=headers, cookies=cookies)

if res.status_code == 200:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(res.json().get("result", ""), "html.parser")
    cards = soup.select("div.caption")

    products = []
    for card in cards:
        a = card.select_one("h4 a")
        price_main = card.select_one("span.tb_integer")
        price_decimal = card.select_one("span.tb_decimal")

        name = a.text.strip() if a else "N/A"
        url = "https://citycenter.jo" + a['href'] if a else ""
        price = f"{price_main.text.strip()}.{price_decimal.text.strip()}" if price_main and price_decimal else "N/A"

        products.append({
            "Product Name": name,
            "Product URL": url,
            "Price (JOD)": price
        })

    EXPORT_DIR = Path("exports")
    EXPORT_DIR.mkdir(exist_ok=True)
    filename = EXPORT_DIR / f"citycenter_cpu_api_{date.today().isoformat()}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)

    print(f"✅ Saved {len(products)} products to {filename}")
else:
    print(f"❌ Still blocked — status code: {res.status_code}")
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(res.text)
