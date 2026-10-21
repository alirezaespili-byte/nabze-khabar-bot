

import os
import json
import hashlib
from pathlib import Path
from html import escape

import feedparser
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "@NabzeKhabar1"
STATE = Path("seen.json")

FEEDS = [
    ("ایران", "https://www.mehrnews.com/rss"),
    ("ایران", "https://www.isna.ir/rss"),
    ("جهان", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("جهان", "https://feeds.bbci.co.uk/news/world/rss.xml"),
]

def main():
    seen = set(json.loads(STATE.read_text()) if STATE.exists() else [])
    first_run = not STATE.exists()
    news = []

    for category, url in FEEDS:
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:12]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if not title or not link:
                    continue

                key = hashlib.sha256(link.encode()).hexdigest()
                if key not in seen:
                    news.append((key, category, title, link, feed.feed.get("title", "")))
        except Exception as error:
            print("Feed error:", error)

    if not first_run:
        for key, category, title, link, source in news[:8]:
            message = (
                f"🔴 <b>{escape(title)}</b>\n\n"
                f"🌍 {escape(category)}\n"
                f"📰 منبع: {escape(source)}\n"
                f"🔗 {escape(link)}\n\n"
                "📡 نبض خبر"
            )
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )
            result.raise_for_status()
            seen.add(key)

    seen.update(item[0] for item in news)
    STATE.write_text(json.dumps(sorted(seen)))

if __name__ == "__main__":
    main()
