"""Post the next scheduled poster from queue.json to Instagram.

Runs daily from GitHub Actions. Uses only the Python standard library.

Needs two GitHub secrets:
  IG_USER_ID       - Instagram account ID (from the Meta developer app)
  IG_ACCESS_TOKEN  - Instagram long-lived access token

Each entry in queue.json looks like:
  {"date": "2026-10-14", "image": "posts/2026-10-14-teak-stain.jpg",
   "caption": "...", "status": "pending"}

Images must be JPEG, ideally 1080x1350 (portrait) or 1080x1080 (square).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com/v21.0"
QUEUE_FILE = "queue.json"
IST = timezone(timedelta(hours=5, minutes=30))


def call(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        sys.exit(f"Instagram API error on {path}: {err.code} {body}")


def image_url(path):
    repo = os.environ["GITHUB_REPOSITORY"]  # owner/name, set by GitHub Actions
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{urllib.parse.quote(path)}"


def main():
    user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    dry_run = os.environ.get("DRY_RUN") == "1"

    with open(QUEUE_FILE, encoding="utf-8") as f:
        queue = json.load(f)

    today = datetime.now(IST).date().isoformat()
    due = [p for p in queue if p.get("status") == "pending" and p["date"] <= today]
    if not due:
        print(f"Nothing due on {today}.")
        return

    post = sorted(due, key=lambda p: p["date"])[0]
    url = image_url(post["image"])
    print(f"Posting {post['image']} ({post['date']})\n  {url}")
    if dry_run:
        print("DRY_RUN=1, not posting.")
        return

    container = call("POST", f"{user_id}/media",
                     {"image_url": url, "caption": post["caption"], "access_token": token})
    creation_id = container["id"]

    # Wait until Instagram has processed the image.
    for _ in range(12):
        status = call("GET", creation_id, {"fields": "status_code", "access_token": token})
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            sys.exit(f"Instagram could not process the image: {status}")
        time.sleep(5)

    result = call("POST", f"{user_id}/media_publish",
                  {"creation_id": creation_id, "access_token": token})

    post["status"] = "posted"
    post["media_id"] = result.get("id")
    post["posted_at"] = datetime.now(IST).isoformat(timespec="minutes")
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Posted. Instagram media id {post['media_id']}")


if __name__ == "__main__":
    main()
