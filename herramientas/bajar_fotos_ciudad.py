"""Baja 4 fotos horizontales de cada ciudad de ciudades.txt que todavia no
tenga fotos en <Carpeta>/Destino.

Fuentes, en orden:
  1. Pexels, si hay PEXELS_API_KEY (sin atribucion obligatoria).
  2. Wikimedia Commons, solo fotos marcadas como "Quality images" (revisadas
     por la comunidad): fotos reales, buena resolucion. Licencias CC0, dominio
     publico, CC BY o CC BY-SA. Las CC BY piden credito: va en CREDITOS.txt y
     la skill lo imprime en la presentacion.
Guarda 1.jpg..4.jpg de 1600 px de ancho y CREDITOS.txt (una linea por foto).
Si una carpeta la lleno este bot (tiene CREDITOS.txt) y quedo con menos de 3
fotos, la vuelve a llenar."""
import io
import os
import re
import sys

import requests
from PIL import Image

UA = {"User-Agent": "banco-fotos-college-traveler/1.0 (contacto@collegetraveler.com)"}
ANCHO = 1600
EVITAR = re.compile(r"map|mapa|plano|logo|escudo|coat|flag|bandera|seal|diagram|sign|interior of|detail|detalle", re.I)
LIC_OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?[0-9.]*)", re.I)


def limpio(t):
    return re.sub(r"<[^>]+>", "", t or "").strip()


def pexels(q, key):
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key, **UA},
                     params={"query": q, "orientation": "landscape", "size": "large", "per_page": 15}, timeout=30)
    r.raise_for_status()
    for p in r.json().get("photos", []):
        yield p["src"]["large2x"], f'{p["photographer"]} / Pexels'


def commons(q):
    for extra in ('incategory:"Quality_images"', ""):
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=40, params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 40,
            "gsrsearch": f'{q} filetype:bitmap {extra}'.strip(),
            "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": ANCHO})
        r.raise_for_status()
        pages = sorted((r.json().get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]
            if EVITAR.search(p.get("title", "")):
                continue
            if ii.get("width", 0) < 1600 or ii.get("width", 0) < ii.get("height", 1) * 1.25:
                continue
            md = ii.get("extmetadata", {})
            lic = limpio(md.get("LicenseShortName", {}).get("value"))
            if not LIC_OK.match(lic):
                continue
            autor = limpio(md.get("Artist", {}).get("value")) or "autor desconocido"
            autor = autor.split("\n")[0][:60]
            yield ii.get("thumburl") or ii["url"], f"{autor} / Wikimedia Commons, {lic}"


def guardar(url, ruta):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if im.width < 1200 or im.width < im.height * 1.2:
        return False
    if im.width > ANCHO:
        im = im.resize((ANCHO, round(im.height * ANCHO / im.width)), Image.LANCZOS)
    im.save(ruta, "JPEG", quality=85, optimize=True)
    return True


def fotos_en(destino):
    return [f for f in os.listdir(destino) if f.lower().endswith((".jpg", ".jpeg", ".png"))] if os.path.isdir(destino) else []


def main():
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    errores = 0
    for linea in open("ciudades.txt", encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#") or "|" not in linea:
            continue
        carpeta, q = [x.strip() for x in linea.split("|", 1)]
        destino = os.path.join(carpeta, "Destino")
        hay = fotos_en(destino)
        del_bot = os.path.exists(os.path.join(destino, "CREDITOS.txt"))
        if hay and not (del_bot and len(hay) < 3):
            continue
        if del_bot:
            for f in hay + ["CREDITOS.txt"]:
                os.remove(os.path.join(destino, f))
        os.makedirs(destino, exist_ok=True)
        fuentes = ([pexels(q, key)] if key else []) + [commons(q)]
        creditos, n = [], 0
        for fuente in fuentes:
            try:
                for url, credito in fuente:
                    if n == 4:
                        break
                    try:
                        if guardar(url, os.path.join(destino, f"{n + 1}.jpg")):
                            n += 1
                            creditos.append(f"{n}.jpg: {credito}")
                    except Exception as e:
                        print(f"  saltada: {e}")
            except Exception as e:
                print(f"ERROR en {carpeta}: {e}")
                errores += 1
            if n == 4:
                break
        if creditos:
            open(os.path.join(destino, "CREDITOS.txt"), "w", encoding="utf-8").write("\n".join(creditos) + "\n")
        print(f"{carpeta}: {n} fotos", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
