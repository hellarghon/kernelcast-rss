import os
import json
import re
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
PODCAST_RSS_URL = "https://anchor.fm/s/f9df9bd0/podcast/rss"
STATE_FILE = "telegram_podcast_published.json"


def load_published():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return []


def save_published(published):
    with open(STATE_FILE, "w") as f:
        json.dump(published, f, indent=2)


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
    published = load_published()
    published_set = set(published)
    new_published = list(published)

    entries_to_send = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link or link in published_set:
            continue
        entries_to_send.append(entry)

    entries_to_send = entries_to_send[:1]

    if not entries_to_send:
        print("No hay episodios de podcast nuevos para publicar.")

    for entry in entries_to_send:
        title = entry.get("title", "Sin título")
        link = entry.get("link", "")
        description = entry.get("summary", "")
        description = re.sub(r"<[^>]+>", "", description)
        if len(description) > 300:
            description = description[:300].rsplit(" ", 1)[0] + "…"

        print(f"Publicando episodio: {title}")
        ok = send_to_telegram(title, link, description)
        if ok:
            new_published.append(link)
            print(f"  ✓ Publicado correctamente")
        else:
            print(f"  ✗ Error al publicar")

    save_published(new_published)


if __name__ == "__main__":
    main()
