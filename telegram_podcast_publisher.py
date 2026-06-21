import os
import json
import re
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
PODCAST_RSS_URL = "https://anchor.fm/s/f9df9bd0/podcast/rss"
STATE_FILE = "telegram_podcast_published.json"


def load_last_published():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_published_link")
    return None


def save_last_published(link):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_published_link": link}, f, indent=2)


def send_to_telegram(title, link, description):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = f"<b>🎙️ Nuevo episodio: {title}</b>\n\n{description}\n\n🎧 <a href='{link}'>Escúchalo aquí</a>"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    response = requests.post(url, json=payload)
    print(f"  Status: {response.status_code}")
    print(f"  Respuesta: {response.text}")
    return response.ok


def main():
    feed = feedparser.parse(PODCAST_RSS_URL)
    if not feed.entries:
        print("Feed vacío o no disponible.")
        return

    latest = feed.entries[0]
    link = latest.get("link", "")
    last_published = load_last_published()

    if not link or link == last_published:
        print("No hay episodios de podcast nuevos para publicar.")
        return

    title = latest.get("title", "Sin título")
    description = latest.get("summary", "")
    description = re.sub(r"<[^>]+>", "", description)
    if len(description) > 300:
        description = description[:300].rsplit(" ", 1)[0] + "…"

    print(f"Publicando episodio: {title}")
    ok = send_to_telegram(title, link, description)
    if ok:
        save_last_published(link)
        print("  ✓ Publicado correctamente")
    else:
        print("  ✗ Error al publicar")


if __name__ == "__main__":
    main()
