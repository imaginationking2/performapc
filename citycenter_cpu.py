import requests
from bs4 import BeautifulSoup
import csv
from datetime import date
from pathlib import Path

# ✅ Your CityCenter API URL
url = "https://citycenter.jo/index.php?route=module/brainyfilter/ajaxfilter&count=1&price=1&path=18_64"

# ✅ Headers to simulate a browser
headers = {
    "Host": "citycenter.jo",
    "Connection": "keep-alive",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Referer": "https://citycenter.jo/computer-hardware/components-cpu-and-processor",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9"
}

# ✅ Paste your manually copied cookies here
cookies = {
    "language": "en",
    "currency": "JOD",
    "PHPSESSID": "d9de8f2405edae511d32d5b153bc7f41",         # <<== Paste here
    "cf_clearance": "BWjnyL_Ay4Lmm2KDKVF8JjPqna8.Ug7cdZnaFslI8cE-1748181602-1.2.1.1-M5TaHbDoWVgP.atZOR74Yp.f_ngAMzkG6YGoTUySyehpmmk7lFyGfZfafa6qQeure77_fuIX0_BfiTWI1tHFwpGitu5QhfjHPN.JfIMv_hr77S24oSTplHBOZv.DzFEOPLabvY0YecwmoLJuXi_fxL7CDjP0XGoLE4PIOHkESkZaLJBetFAtWgxokQP3qrHnazNI5LX92eJXYZZR0xfYsCG9xtLEtB1BFpWrjbZkyKQE5QSgtgUrOZ8lGsPHn6z37yj7Ag3avjfz2NvtMUHmuheavOHqwzy.o0V_2JFB8w2ucYXhLTpVEPXxx5r646a4Z35ynXlJ8OabxRTuTht_81iRReYvuT6j.R3P6Pk0b064GY6BR7DXwRttO01yTj.o"  # <<== Paste here
}

# 🔄 Make the request
res = requests.get(url, headers=headers, cookies=cookies)

if res.status_code == 200:
    data = res.json()
    html = data.get("result", "")

    if not html:
        print("⚠️ No product HTML found in API response.")
    else:
        soup = BeautifulSoup(html, "html.parser")
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

        if products:
            EXPORT_DIR = Path("exports")
            EXPORT_DIR.mkdir(exist_ok=True)
            filename = EXPORT_DIR / f"citycenter_cpu_api_{date.today().isoformat()}.csv"

            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)

            print(f"✅ Scraped and saved {len(products)} products to {filename}")
        else:
            print("⚠️ HTML parsed but no products found.")
else:
    print(f"❌ Request failed with status code: {res.status_code}")
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("🧪 Saved response to debug_page.html for inspection.")
