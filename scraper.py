import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import re
import os
import time

BASE_URL = "https://www.kernelcast.es"
SECCIONES = ["/noticias", "/blog"]
RSS_FILE = "feed.xml"

def obtener_articulos():
    articulos = []
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    vistos_urls = {}

    for seccion in SECCIONES:
        url = BASE_URL + seccion
        print(f"Scrapeando: {url}")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"Error al acceder a {url}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar todos los enlaces que coincidan con el patrón de artículo:
        # /noticias/NUMEROID_slug o /blog/NUMEROID_slug
        patron = re.compile(r"/(noticias|blog)/\d+_[^\"'\s]+")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Normalizar URL
            if href.startswith("/"):
                href = BASE_URL + href
            elif not href.startswith("http"):
                continue

            # Verificar que la ruta coincide con el patrón de artículo
            ruta = href.replace(BASE_URL, "")
            if not patron.match(ruta):
                continue

            # Obtener título: probar el propio <a>, luego elementos hijos
            titulo = ""
            for selector in [
                lambda el: el.get_text(strip=True),
                lambda el: el.find(["h1", "h2", "h3", "h4", "span", "p"]) and el.find(["h1", "h2", "h3", "h4", "span", "p"]).get_text(strip=True),
            ]:
                try:
                    t = selector(a)
                    if t and len(t) > 15:
                        titulo = t
                        break
                except Exception:
                    continue

            # Si no hay título en el enlace, derivarlo del slug de la URL
            if not titulo or len(titulo) < 10:
                slug = ruta.split("_", 1)[-1] if "_" in ruta else ruta.split("/")[-1]
                titulo = slug.replace("-", " ").replace("_", " ").capitalize()

            if href not in vistos_urls:
                vistos_urls[href] = True
                articulos.append({"url": href, "titulo": titulo})
                print(f"  Encontrado: {titulo[:60]}...")

    print(f"Total artículos únicos encontrados: {len(articulos)}")
    return articulos


def obtener_detalle(url, headers):
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        imagen = None
        for prop in ["twitter:image", "og:image"]:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                imagen = tag["content"].replace("&amp;", "&")
                break

        descripcion = None
        for prop in ["og:description", "twitter:description", "description"]:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                descripcion = tag["content"]
                break

        if not descripcion:
            for p in soup.find_all("p"):
                texto = p.get_text(strip=True)
                if len(texto) > 80:
                    descripcion = texto[:300]
                    break

        # Intentar obtener título real desde og:title o twitter:title
        titulo_real = None
        for prop in ["og:title", "twitter:title"]:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                titulo_real = tag["content"]
                break
        if not titulo_real:
            title_tag = soup.find("title")
            if title_tag:
                titulo_real = title_tag.get_text(strip=True).split("|")[0].strip()

        return imagen, descripcion, titulo_real

    except Exception as e:
        print(f"Error al obtener detalle de {url}: {e}")
        return None, None, None


def generar_rss(articulos):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:media", "http://search.yahoo.com/mrss/")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "KernelCast"
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "description").text = "Últimas noticias de KernelCast"
    ET.SubElement(channel, "language").text = "es"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    procesados = 0
    for art in articulos[:30]:
        imagen, descripcion, titulo_real = obtener_detalle(art["url"], headers)
        time.sleep(0.5)

        titulo_final = titulo_real if titulo_real and len(titulo_real) > 5 else art["titulo"]

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = titulo_final
        ET.SubElement(item, "link").text = art["url"]
        ET.SubElement(item, "guid").text = art["url"]
        ET.SubElement(item, "pubDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        if descripcion:
            ET.SubElement(item, "description").text = descripcion

        if imagen:
            media = ET.SubElement(item, "media:content")
            media.set("url", imagen)
            media.set("medium", "image")

        procesados += 1

    print(f"Artículos incluidos en el feed: {procesados}")

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(RSS_FILE, encoding="unicode", xml_declaration=True)
    print(f"Feed guardado en {RSS_FILE}")


if __name__ == "__main__":
    print(f"Iniciando scraper - {datetime.now()}")
    articulos = obtener_articulos()
    if articulos:
        generar_rss(articulos)
    else:
        print("No se encontraron artículos. Revisa la estructura HTML de la web.")
