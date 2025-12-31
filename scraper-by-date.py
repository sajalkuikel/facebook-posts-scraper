import time
import random
import json
import os
import re
from urllib.parse import urlparse
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


class FacebookMonthlyScraper:
    def __init__(self, email, password, page_url):
        self.email = email
        self.password = password
        self.page_url = page_url

        self.page_slug = self._extract_page_slug(page_url)
        self.base_dir = os.path.join("dataset", self.page_slug)
        os.makedirs(self.base_dir, exist_ok=True)

        self.driver = None

    # --------------------------------------------------
    def _extract_page_slug(self, page_url):
        return urlparse(page_url).path.strip("/").split("/")[0]

    # --------------------------------------------------
    def _setup_month_dirs(self, year, month):
        month_key = f"{year}-{MONTHS.index(month)+1:02d}"
        month_dir = os.path.join(self.base_dir, month_key)
        image_dir = os.path.join(month_dir, "images")
        os.makedirs(image_dir, exist_ok=True)

        jsonl_path = os.path.join(month_dir, "facebook_posts.jsonl")
        return month_dir, image_dir, jsonl_path

    # --------------------------------------------------
    def _load_existing_urls(self, jsonl_path):
        urls = set()
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        urls.add(json.loads(line)["post_url"])
                    except:
                        continue
            print(f"✓ Resuming {len(urls)} posts")
        return urls

    # --------------------------------------------------
    def _append_jsonl(self, jsonl_path, record):
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # --------------------------------------------------
    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    # --------------------------------------------------
    def login(self):
        self.driver.get("https://www.facebook.com/login")
        time.sleep(4)

        email = self.driver.find_element(By.NAME, "email")
        password = self.driver.find_element(By.NAME, "pass")

        for c in self.email:
            email.send_keys(c)
            time.sleep(0.1)
        for c in self.password:
            password.send_keys(c)
            time.sleep(0.1)

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(20)

    # --------------------------------------------------
    def apply_date_filter(self, year, month=None, day=None, timeout=20):
        """
        Apply Facebook feed filter using Year -> Month -> Day (optional)

        Args:
            year (int or str): e.g. 2025
            month (str): e.g. "December" (optional)
            day (int or str): e.g. 15 (optional)
            timeout (int): wait timeout
        """

        wait = WebDriverWait(self.driver, timeout)

        # --------------------------------------------------
        # 1️⃣ Open Filters modal
        # --------------------------------------------------
        filters_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[.//span[text()='Filters'] and @role='button']"
            ))
        )
        self.driver.execute_script("arguments[0].click();", filters_btn)
        time.sleep(1)

        # --------------------------------------------------
        # 2️⃣ YEAR dropdown (role=combobox)
        # --------------------------------------------------
        year_box = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@role='combobox' and .//span[text()='Year']]"
            ))
        )
        self.driver.execute_script("arguments[0].click();", year_box)

        year_option = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                f"//div[@role='option' and .//span[text()='{year}']]"
            ))
        )
        self.driver.execute_script("arguments[0].click();", year_option)
        time.sleep(1)

        # --------------------------------------------------
        # 3️⃣ MONTH dropdown (optional)
        # --------------------------------------------------
        if month:
            month_box = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[@role='combobox' and .//span[text()='Month']]"
                ))
            )
            self.driver.execute_script("arguments[0].click();", month_box)

            month_option = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f"//div[@role='option' and .//span[text()='{month}']]"
                ))
            )
            self.driver.execute_script("arguments[0].click();", month_option)
            time.sleep(1)

        # --------------------------------------------------
        # 4️⃣ DAY dropdown (optional)
        # --------------------------------------------------
        if day:
            day_box = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[@role='combobox' and .//span[text()='Day']]"
                ))
            )
            self.driver.execute_script("arguments[0].click();", day_box)

            day_option = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f"//div[@role='option' and .//span[text()='{day}']]"
                ))
            )
            self.driver.execute_script("arguments[0].click();", day_option)
            time.sleep(1)

        # --------------------------------------------------
        # 5️⃣ Click Done
        # --------------------------------------------------
        done_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@role='button' and .//span[text()='Done']]"
            ))
        )
        self.driver.execute_script("arguments[0].click();", done_btn)

        # Allow feed to reload
        time.sleep(4)

        print(
            f"✓ Date filter applied → "
            f"Year={year}, Month={month or 'ALL'}, Day={day or 'ALL'}"
        )
    # --------------------------------------------------
    def extract_posts(self, scraped_urls):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        posts = soup.find_all("div", {"class": "x1n2onr6 x1ja2u2z"})
        results = []

        for post in posts:
            try:
                link = post.find("a", href=re.compile(r"/posts/"))
                if not link:
                    continue

                post_url = link.get("href").split("?")[0]
                if post_url.startswith("/"):
                    post_url = "https://www.facebook.com" + post_url

                if post_url in scraped_urls:
                    continue

                post_id = post_url.split("/")[-1]

                if post.find("video"):
                    continue

                text_blocks = post.find_all("div", {"data-ad-preview": "message"})
                post_text = " ".join(t.get_text(strip=True) for t in text_blocks)
                if len(post_text) < 5:
                    continue

                image_url = None
                for img in post.find_all("img"):
                    src = img.get("src", "")
                    if "scontent" in src and "emoji" not in src.lower():
                        image_url = src
                        break

                if not image_url:
                    continue

                record = {
                    "post_id": post_id,
                    "page_id": self.page_slug,
                    "post_url": post_url,
                    "post_text": post_text,
                    "image_url": image_url,
                    "image_file": f"images/fb_{post_id}.jpeg"
                }

                scraped_urls.add(post_url)
                results.append(record)

            except:
                continue

        return results

    # --------------------------------------------------
    def scrape_month(self, year, month, limit=200):
        month_dir, image_dir, jsonl_path = self._setup_month_dirs(year, month)
        scraped_urls = self._load_existing_urls(jsonl_path)

        self.initialize_driver()
        self.login()
        self.driver.get(self.page_url)
        time.sleep(5)

        self.apply_date_filter(year, month)

        no_new = 0

        while len(scraped_urls) < limit:
            posts = self.extract_posts(scraped_urls)

            if not posts:
                no_new += 1
            else:
                no_new = 0
                for p in posts:
                    self._append_jsonl(jsonl_path, p)
                    print(f"✓ [{year} {month}] {len(scraped_urls)}")

            if no_new >= 6 :
                print("⚠ No new posts, stopping month")
                break

            self.driver.execute_script(
                f"window.scrollBy(0, {random.randint(900, 1400)});"
            )
            time.sleep(random.uniform(1.2, 2.2))

        self.driver.quit()
        print(f"✓ Finished {year} {month}")

    # --------------------------------------------------
    def run(self, start_year=2025, start_month="December"):
        start_idx = MONTHS.index(start_month)

        for year in range(start_year, 2015, -1):
            for m in reversed(MONTHS[:start_idx + 1]):
                self.scrape_month(year, m)
            start_idx = 11


# --------------------------------------------------
if __name__ == "__main__":
    EMAIL = input("Facebook email: ")
    PASSWORD = input("Facebook password: ")
    PAGE_URL = input("Facebook page URL: ")
       
    scraper = FacebookMonthlyScraper(EMAIL, PASSWORD, PAGE_URL)
    scraper.run(start_year=2025, start_month="December")
