import json
import os
import requests

JSON_FILE = "facebook_posts.json"
OUTPUT_DIR = "images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.facebook.com/"
}

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for i, item in enumerate(data):
    url = item.get("image_url")
    post_id = item.get("post_id")
    page_id = item.get("page_id")
    if not url:
        continue

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        # Ensure it's actually an image
        content_type = r.headers.get("Content-Type", "")
        if not content_type.startswith("image"):
            print(f"Skipped (not image): {url}")
            continue

        # Get extension from Content-Type
        # ext = content_type.split("/")[-1]
        ext = '.jpeg'  # Default to jpeg if unsure
        filename = f"fb_{page_id}_{post_id}.{ext}"

        with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
            f.write(r.content)

        print(f"Downloaded: {filename}")

    except Exception as e:
        print(f"Failed: {e}")
