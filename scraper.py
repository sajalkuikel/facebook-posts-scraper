from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random
import json
import re
import os
from urllib.parse import urlparse


class FacebookScraper:
    def __init__(self, email, password, page_url):
        self.email = email
        self.password = password
        self.page_url = page_url
        self.driver = None

        # ---------- PAGE-BASED DIRECTORY SETUP ----------
        self.page_slug = self._extract_page_slug(page_url)
        self.base_dir = os.path.join("dataset", self.page_slug)
        self.image_dir = os.path.join(self.base_dir, "images")
        self.output_file = os.path.join(self.base_dir, "facebook_posts.json")

        os.makedirs(self.image_dir, exist_ok=True)

        self.scraped_urls = self._load_existing_urls()

    # --------------------------------------------------
    def _extract_page_slug(self, page_url):
        path = urlparse(page_url).path.strip("/")
        return path.split("/")[0]

    # --------------------------------------------------
    # RESUME SUPPORT (PER PAGE)
    # --------------------------------------------------
    def _load_existing_urls(self):
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            urls = {item["post_url"] for item in data}
            print(f"✓ Resuming {self.page_slug} with {len(urls)} posts")
            return urls
        return set()

    def _append_json(self, record):
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(record)

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------
    def human_type(self, element, text):
        for c in text:
            element.send_keys(c)
            time.sleep(random.uniform(0.15, 0.35))

    # --------------------------------------------------
    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        print("✓ Chrome driver initialized")

    # --------------------------------------------------
    def login(self):
        self.driver.get("https://www.facebook.com/login")
        time.sleep(4)

        email_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "pass")

        self.human_type(email_input, self.email)
        time.sleep(1)
        self.human_type(password_input, self.password)

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(20)

        print("✓ Logged in")

    # --------------------------------------------------
    def navigate_to_page(self):
        self.driver.get(self.page_url)
        time.sleep(5)
        print(f"✓ Page loaded: {self.page_slug}")

    # --------------------------------------------------
    def click_see_more(self):
        for btn in self.driver.find_elements(By.XPATH, "//div[text()='See more']"):
            try:
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(random.uniform(0.1, 0.25))
            except:
                pass

    # --------------------------------------------------
    def extract_posts(self):
        self.click_see_more()
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        posts_data = []

        posts = soup.find_all("div", {"class": "x1n2onr6 x1ja2u2z"})

        for post in posts:
            try:
                link = post.find("a", href=re.compile(r'/posts/'))
                if not link:
                    continue

                post_url = link.get("href").split("?")[0]
                if post_url.startswith("/"):
                    post_url = "https://www.facebook.com" + post_url

                if post_url in self.scraped_urls:
                    continue

                post_id_match = re.search(r'/posts/([^/?]+)', post_url)
                if not post_id_match:
                    continue
                post_id = post_id_match.group(1)

                if post.find("video"):
                    continue

                message_blocks = post.find_all("div", {"data-ad-preview": "message"})
                post_text = " ".join(m.get_text(strip=True) for m in message_blocks)
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

                self.scraped_urls.add(post_url)
                posts_data.append(record)

            except:
                continue

        return posts_data

    # --------------------------------------------------
    def scrape(self, max_posts=10):
        no_new_rounds = 0

        while len(self.scraped_urls) < max_posts:
            posts = self.extract_posts()

            if not posts:
                no_new_rounds += 1
            else:
                no_new_rounds = 0
                for post in posts:
                    self._append_json(post)
                    print(f"✓ [{self.page_slug}] Saved {len(self.scraped_urls)}")

            if no_new_rounds >= 1000:
                print("⚠ No new posts for a while. Stopping.")
                break

            self.driver.execute_script(
                f"window.scrollBy(0, {random.randint(900, 1400)});"
            )
            time.sleep(random.uniform(1.2, 2.2))

    # --------------------------------------------------
    def close(self):
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")


# --------------------------------------------------
if __name__ == "__main__":
    EMAIL = input("Enter your facebook email: ")
    PASSWORD = input("Enter your facebook password: ")
    PAGE_URL = input("Enter the facebook page URL: ")
    MAX_POSTS = 10

    scraper = FacebookScraper(EMAIL, PASSWORD, PAGE_URL)

    try:
        scraper.initialize_driver()
        scraper.login()
        scraper.navigate_to_page()
        scraper.scrape(MAX_POSTS)
        print("\n✓ Scraping complete")
    finally:
        scraper.close()
