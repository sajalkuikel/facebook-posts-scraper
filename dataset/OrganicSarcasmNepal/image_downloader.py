import json
import os
import requests
from urllib.parse import urlparse

# ---------------- CONFIG ----------------
JSON_FILE = "facebook_posts.json"   # per-page JSON
BASE_DIR = "."                      # current page folder
IMAGE_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.facebook.com/"
}

TIMEOUT = 15
# ----------------------------------------


with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

downloaded = 0
skipped = 0

for item in data:
    image_url = item.get("image_url")
    image_file = item.get("image_file")  # already relative path

    if not image_url or not image_file:
        continue

    output_path = os.path.join(BASE_DIR, image_file)

    # ✅ RESUME CHECK
    if os.path.exists(output_path):
        skipped += 1
        continue

    try:
        r = requests.get(image_url, headers=HEADERS, timeout=TIMEOUT)
        content_type = r.headers.get("Content-Type", "")

        if not content_type.startswith("image"):
            print(f"⚠ Skipped (not image): {image_url}")
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(r.content)

        downloaded += 1
        print(f"✓ Downloaded: {output_path}")

    except Exception as e:
        print(f"✗ Failed: {image_url} | {e}")

print("\n===== SUMMARY =====")
print(f"Downloaded: {downloaded}")
print(f"Skipped (already exists): {skipped}")
