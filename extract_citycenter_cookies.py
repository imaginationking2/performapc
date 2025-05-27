from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# Launch Chrome in visible mode (not headless)
options = Options()
options.add_experimental_option("detach", True)  # keeps browser open
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open the target page for you to solve CAPTCHA manually
url = "https://citycenter.jo/computer-hardware/components-cpu-and-processor"
print(f"🔓 Open the browser window and pass CAPTCHA manually: {url}")
driver.get(url)

# Give you time to manually solve CAPTCHA
input("✅ Press ENTER after CAPTCHA is solved and page loads completely...")

# Extract cookies from your real session
cookies = driver.get_cookies()
with open("citycenter_cookies.json", "w") as f:
    json.dump(cookies, f, indent=2)

print("✅ Cookies saved to citycenter_cookies.json")
driver.quit()
