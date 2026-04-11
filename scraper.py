import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import json
import os
import time

BASE_URL = "https://www.kernelcast.es"
SECCIONES = ["/noticias", "/blog"]
RSS_FILE = "feed.xml"
SEEN_FILE = "seen.json"

def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return []

def guardar_vistos(vistos):
    with open(SEEN_FILE, "w") as f:
        json.dump(vistos, f)

def obtener_articulos():
    articulos = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for seccion in SECCIONES:
        url = BASE_URL + seccion
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/noticias/" in href or "/blog/" in href:
                if href.startswith("/"):
                    href = BASE_URL + href
                titulo = a.get_text(strip=True)
                if titulo and len(titulo) > 20:
                    articulos.append({"url": href, "titulo": titulo})
    vistos_urls = {}
    unicos = []
    for art in articulos:
        if art["url"] not in vistos_urls:
            vistos_urls[art["url"]] = True
            unicos.append(art)
    return unicos

def obtener_detalle(url, headers):
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        imagen = None
        twitter_image = soup.find("meta", property="twitter:image")
        if twitter_image and twitter_image.get("content"):
            imagen = twitter_image["content"].replace("&amp;", "&")
        if not imagen:
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                imagen = og_image["content"].replace("&amp;", "&")
        if not imagen:
            meta_twitter = soup.find("meta", attrs={"name": "twitter:image"})
            if meta_twitter and meta_twitter.get("content"):
                imagen = meta_twitter["content"].replace("&amp;", "&")

        descripcion = None
        twitter_desc = soup.find("meta", property="twitter:description")
        if twitter_desc and twitter_desc.get("content"):
            descripcion = twitter_desc["content"]
        if not descripcion:
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                descripcion = og_desc["content"]
        if not descripcion:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                descripcion = meta_desc["content"]
        if not descripcion:
            for p in soup.find_all("p"):
                texto = p.get_text(strip=True)
                if len(texto) > 80:
                    descripcion = texto[:300]
                    break

        return imagen, descripcion
    except Exception as e:
        print(f"Error al obtener detalle de {url}: {e}")
        return None, None

def generar_rss(articulos):
    headers = {"User-Agent": "Mozilla/5.0"}
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:media", "http://search.yahoo.com/mrss/")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "KernelCast"
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "description").text = "Últimas noticias de KernelCast"
    ET.SubElement(channel, "language").text = "es"

    for art in articulos[:30]:
        imagen, descripcion = obtener_
