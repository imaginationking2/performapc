from playwright.sync_api import sync_playwright
import json

def scrape_tiktok_mobile(hashtag="gaminguae", max_scrolls=5):
    results = []
    url = f"https://www.tiktok.com/tag/{hashtag}"

    with sync_playwright() as p:
        iphone = p.devices['iPhone 13 Pro']
        browser = p.webkit.launch(headless=False)
        context = browser.new_context(**iphone)
        page = context.new_page()

        print(f"🌐 Visiting: {url}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(6000)

        for _ in range(max_scrolls):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)

        # Grab all visible text blocks (more robust than fixed divs)
        all_blocks = page.query_selector_all("div, span, strong")

        for block in all_blocks:
            try:
                text = block.inner_text().strip()
                if (
                    len(text) > 20 and             # meaningful content
                    any(word in text.lower() for word in ["#", "setup", "gaming", "uae", "valorant", "pc", "build"])
                ):
                    results.append({"caption": text})
            except Exception:
                continue

        browser.close()

    return results

if __name__ == "__main__":
    hashtag = "gaminguae"
    posts = scrape_tiktok_mobile(hashtag)

    with open(f"tiktok_{hashtag}_mobile_filtered.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"✅ Scraped and filtered {len(posts)} posts from #{hashtag}")
