import json
import os
import requests

# ---------------- CONFIG ----------------
JSONL_FILE = "facebook_posts.jsonl"   # ← JSONL file
BASE_DIR = "."                        # current page folder

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.facebook.com/"
}

TIMEOUT = 15
# ----------------------------------------

downloaded = 0
skipped = 0
failed = 0

with open(JSONL_FILE, "r", encoding="utf-8") as f:
    for line in f:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

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

            with open(output_path, "wb") as img:
                img.write(r.content)

            downloaded += 1
            print(f"✓ Downloaded: {output_path}")

        except Exception as e:
            failed += 1
            print(f"✗ Failed: {image_url} | {e}")

print("\n===== SUMMARY =====")
print(f"Downloaded: {downloaded}")
print(f"Skipped (already exists): {skipped}")
print(f"Failed: {failed}")
