import os
from datetime import date
from pathlib import Path
import importlib

# Directory where CSV files will be saved
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

# List of vendor modules to run
vendor_modules = [
    "microless_cpu_with_stock",
    "gccgamers_cases",
    "laifai_cpu",
    "gccgamers_coolers",
    "gccgamers_gpu",
    "microless_gpu",
    "microless_Cases",
    "laifai_gpu",
    "dxbgamers_cpu",
]

def run_all_scrapers():
    print(f"📦 Starting vendor scraping: {date.today().isoformat()}")
    for module_name in vendor_modules:
        try:
            print(f"\n▶ Running {module_name}.scrape()")
            scraper = importlib.import_module(module_name)

            if not hasattr(scraper, "scrape"):
                raise AttributeError("Module has no 'scrape' function")

            scraper.scrape(EXPORT_DIR)

        except Exception as e:
            print(f"❌ Failed to run {module_name}: {e}")

    print(f"\n✅ Done. All outputs saved to: {EXPORT_DIR.resolve()}")

if __name__ == "__main__":
    run_all_scrapers()
