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

        # Imagen de cabecera
        imagen = None
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            imagen = og_image["content"]

        # Descripción / resumen
        descripcion = None
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            descripcion = og_desc["content"]
        if not descripcion:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                descripcion = meta_desc["content"]

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
        imagen, descripcion = obtener_detalle(art["url"], headers)
        time.sleep(1)

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = art["titulo"]
        ET.SubElement(item, "link").text = art["url"]
        ET.SubElement(item, "guid").text = art["url"]
        ET.SubElement(item, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        if descripcion:
            ET.SubElement(item, "description").text = descripcion

        if imagen:
            media = ET.SubElement(item, "media:content")
            media.set("url", imagen)
            media.set("medium", "image")

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(RSS_FILE, encoding="unicode", xml_declaration=True)
    print(f"RSS generado con {len(articulos[:30])} artículos.")

if __name__ == "__main__":
    articulos = obtener_articulos()
    generar_rss(articulos)
    print("Hecho.")
