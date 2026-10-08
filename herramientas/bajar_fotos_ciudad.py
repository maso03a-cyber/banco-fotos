"""Baja 4 fotos horizontales de cada ciudad de ciudades.txt que todavia no
tenga fotos en <Carpeta>/Destino.

Fuentes, en orden:
  1. Pexels, si hay PEXELS_API_KEY (sin atribucion obligatoria).
  2. Las fotos del articulo de la ciudad en Wikipedia (espanol e ingles),
     leidas de Wikimedia Commons: vistas y monumentos elegidos por la
     comunidad, buena resolucion. Licencias CC0, dominio
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
EVITAR = re.compile(r"map|mapa|plano|logo|escudo|coat|flag|bandera|seal|diagram|sign|interior|detail|detalle|retrato|portrait|\\bpres|governor|gobernador|airport|aeropuerto|stadium|estadio|hurric|hurac|satellite|sat[eé]lite_image|grabado|litograf|engraving|\\b1[5-8][0-9]{2}\\b", re.I)
LIC_OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?[0-9.]*)", re.I)


def limpio(t):
    return re.sub(r"<[^>]+>", "", t or "").strip()


def pexels(q, key):
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key, **UA},
                     params={"query": q, "orientation": "landscape", "size": "large", "per_page": 15}, timeout=30)
    r.raise_for_status()
    for p in r.json().get("photos", []):
        yield p["src"]["large2x"], f'{p["photographer"]} / Pexels'


def _articulo(wiki, q):
    r = requests.get(f"https://{wiki}.wikipedia.org/w/api.php", headers=UA, timeout=30, params={
        "action": "query", "format": "json", "list": "search", "srsearch": q, "srlimit": 1})
    r.raise_for_status()
    res = r.json().get("query", {}).get("search", [])
    return res[0]["title"] if res else None


def _imagenes(wiki, titulo):
    r = requests.get(f"https://{wiki}.wikipedia.org/w/api.php", headers=UA, timeout=30, params={
        "action": "parse", "format": "json", "page": titulo, "prop": "images", "redirects": 1})
    r.raise_for_status()
    return [f"File:{x}" for x in r.json().get("parse", {}).get("images", [])
            if x.lower().endswith((".jpg", ".jpeg"))]


def commons(q):
    """Fotos del articulo de la ciudad en Wikipedia (espanol e ingles): son
    las que la comunidad eligio para ilustrar la ciudad, asi que son vistas y
    monumentos, no insectos ni coches. Se leen de Commons con su licencia."""
    archivos = []
    for wiki in ("es", "en"):
        try:
            t = _articulo(wiki, q)
            if t:
                archivos += [a for a in _imagenes(wiki, t) if a not in archivos]
        except Exception as e:
            print(f"  {wiki}.wikipedia: {e}")
    for i in range(0, len(archivos), 40):
        lote = archivos[i:i + 40]
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=40, params={
            "action": "query", "format": "json", "titles": "|".join(lote),
            "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": ANCHO})
        r.raise_for_status()
        info = {p.get("title"): p for p in (r.json().get("query") or {}).get("pages", {}).values()}
        for t in lote:
            p = info.get(t.replace("_", " ")) or info.get(t)
            if not p or EVITAR.search(t):
                continue
            ii = (p.get("imageinfo") or [{}])[0]
            if ii.get("width", 0) < 1600 or ii.get("width", 0) < ii.get("height", 1) * 1.25:
                continue
            md = ii.get("extmetadata", {})
            lic = limpio(md.get("LicenseShortName", {}).get("value"))
            if not LIC_OK.match(lic):
                continue
            autor = limpio(md.get("Artist", {}).get("value")) or "autor desconocido"
            yield ii.get("thumburl") or ii["url"], f"{autor.splitlines()[0][:60]} / Wikimedia Commons, {lic}"


def guardar(url, ruta):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if im.width < 1200 or im.width < im.height * 1.2:
        return False
    # Fuera fotos en blanco y negro, sepia o grabados antiguos: saturacion baja.
    sat = im.convert("HSV").resize((64, 40)).getchannel("S")
    if sum(sat.getdata()) / (64 * 40 * 255) < 0.16:
        return False
    if im.width > ANCHO:
        im = im.resize((ANCHO, round(im.height * ANCHO / im.width)), Image.LANCZOS)
    im.save(ruta, "JPEG", quality=85, optimize=True)
    return True


def fotos_en(destino):
    return [f for f in os.listdir(destino) if f.lower().endswith((".jpg", ".jpeg", ".png"))] if os.path.isdir(destino) else []


def main():
    """Llena cada ciudad hasta 4 fotos. Si alguien borra una foto mala de una
    carpeta que lleno este bot, en la siguiente corrida se repone con otra
    (las que ya se usaron o se borraron no se vuelven a bajar)."""
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    for linea in open("ciudades.txt", encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#") or "|" not in linea:
            continue
        carpeta, q = [x.strip() for x in linea.split("|", 1)]
        destino = os.path.join(carpeta, "Destino")
        cred_path = os.path.join(destino, "CREDITOS.txt")
        hay = sorted(fotos_en(destino))
        if hay and not os.path.exists(cred_path):
            continue                      # carpeta subida a mano: no se toca
        if len(hay) >= 4:
            continue
        os.makedirs(destino, exist_ok=True)
        previos = {}
        usadas = set()
        if os.path.exists(cred_path):
            for l in open(cred_path, encoding="utf-8"):
                if ": " in l:
                    f, resto = l.rstrip("\n").split(": ", 1)
                    previos[f] = resto
                    usadas.add(resto.split(" | ")[-1])
        # renumerar las que quedan: 1.jpg, 2.jpg...
        creditos = []
        for n_, f in enumerate(hay, 1):
            nuevo = f"{n_}.jpg"
            if f != nuevo:
                os.rename(os.path.join(destino, f), os.path.join(destino, nuevo))
            creditos.append(f"{nuevo}: {previos.get(f, 'sin dato')}")
        n = len(hay)
        fuentes = ([pexels(q, key)] if key else []) + [commons(q)]
        for fuente in fuentes:
            try:
                for url, credito in fuente:
                    if n == 4:
                        break
                    if url in usadas:
                        continue
                    usadas.add(url)
                    try:
                        if guardar(url, os.path.join(destino, f"{n + 1}.jpg")):
                            n += 1
                            creditos.append(f"{n}.jpg: {credito} | {url}")
                    except Exception as e:
                        print(f"  saltada: {e}")
            except Exception as e:
                print(f"ERROR en {carpeta}: {e}")
            if n == 4:
                break
        if creditos:
            open(cred_path, "w", encoding="utf-8").write("\n".join(creditos) + "\n")
        print(f"{carpeta}: {n} fotos", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
